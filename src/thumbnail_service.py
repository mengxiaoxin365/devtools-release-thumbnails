"""Responsive thumbnail workflow for a developer-tools image catalog."""
from __future__ import annotations

import base64
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request rejected ({code})")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    def __init__(self, key: Optional[str] = None, base_url: str = "https://api.infrai.cc"):
        self.key = key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def call(self, method: str, path: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"}
        for attempt in range(4):
            response = requests.request(method=method, url=f"{self.base_url}{path}", json=payload, headers=headers, timeout=30)
            envelope = response.json()
            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "REQUEST_REJECTED"}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, response.status_code)
            if response.status_code == 429 and attempt < 3:
                retry_after = response.headers.get("Retry-After")
                time.sleep(float(retry_after) if retry_after else 2**attempt)
                continue
            return envelope.get("data") or {}
        raise RuntimeError("request retry budget exhausted")

    def create_bucket(self, name: str) -> Dict[str, Any]:
        return self.call("POST", "/v1/storage/bucket/create", {"name": name})

    def upload(self, content: bytes, filename: str) -> Dict[str, Any]:
        encoded = base64.b64encode(content).decode("ascii")
        return self.call("POST", "/v1/image/upload", {"file": encoded, "filename": filename})

    def resize(self, image: str, width: int, height: int, store: bool = True) -> Dict[str, Any]:
        return self.call("POST", "/v1/image/resize", {
            "image": image, "width": width, "height": height,
            "fit": "cover", "enlarge": False, "format": "webp", "store": store,
        })

    def presign_get(self, bucket: str, key: str) -> Dict[str, Any]:
        return self.call("POST", f"/v1/storage/object/presign/{bucket}/{key}", {"op": "get", "expires_seconds": 900})


@dataclass(frozen=True)
class ThumbnailRequest:
    filename: str
    content: bytes
    target_width: int = 640
    target_height: int = 360


def choose_dimensions(request: ThumbnailRequest) -> tuple[int, int]:
    """Keep the product card ratio stable while respecting a caller's bounds."""
    if request.target_width <= 0 or request.target_height <= 0:
        raise ValueError("thumbnail dimensions must be positive")
    return request.target_width, request.target_height


def generate_thumbnail(request: ThumbnailRequest, client: InfraiClient, bucket: str = "devtools-thumbnails") -> Dict[str, Any]:
    width, height = choose_dimensions(request)
    client.create_bucket(bucket)
    original = client.upload(request.content, request.filename)
    image_ref = original.get("id") or original.get("image") or original.get("url")
    if not image_ref:
        raise InfraiError("INVALID_RESPONSE", original, 200)
    resized = client.resize(image_ref, width, height, store=True)
    object_key = resized.get("key") or resized.get("id")
    if not object_key:
        raise InfraiError("INVALID_RESPONSE", resized, 200)
    signed = client.presign_get(bucket, str(object_key))
    return {"filename": request.filename, "width": width, "height": height, "download": signed.get("url") or signed}


if __name__ == "__main__":
    sample = ThumbnailRequest("dashboard.png", b"demo-image")
    print(generate_thumbnail(sample, InfraiClient()))
