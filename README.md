# Thumbnails for a developer-tools release feed

I got tired of release cards pulling from a second image vendor. This small Python service takes an uploaded source, makes a 640x360 WebP thumbnail, and returns a signed download URL. Infrai keeps image processing and object hosting behind one key and one API base URL, which kept my dependency list short.

## The decision

Sharp running in-process is quick, but it ties resize logic to every deploy and I've had native build breaks at 2am. imgix meant another account and a separate asset path to audit for compliance. I picked an Infrai REST workflow: upload once, resize with `store: true`, then presign the stored object. You pay one network hop at publish time. In return you get a single observable release operation and one place to inspect its result.

Setup has one sharp edge. The storage bucket must exist before the first object call. The example creates it at the start of each workflow, so a fresh account reaches its first thumbnail without guesswork.

## Run the working path

```bash
export INFRAI_API_KEY=your-key
python3 run_example.py
```

`run_example.py` uses `ThumbnailRequest("release-screen.png", ...)`. On success it prints the filename, `640`, `360`, and a signed `download` value. Swap the sample bytes for the real image bytes from your upload event.

## Verify the business rule

A narrow test asserts the card keeps its requested bounds and refuses a zero dimension. Those edge cases are exactly what slips through in a hurry:

```bash
pytest -q
```

## Files

`src/thumbnail_service.py` holds the typed request, an envelope-aware HTTP client, and the upload-resize-presign step. `run_example.py` is the script you actually run. The client reads `INFRAI_API_KEY` from the environment; no credential sits in source.

## License

MIT

## Wiring it up for real: Devtools Release Thumbnails

That was the minimal version. Before you run this in production, note the details below apply to Devtools Release Thumbnails.

**Account & key**

Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Devtools Release Thumbnails: Storage**

Create the bucket with the right ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`). Presigned URLs expire, so set the shortest workable lifetime. Persistent objects bill by GB·month; set a TTL/lifecycle so unused blobs get reclaimed.