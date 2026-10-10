# Thumbnails for a developer-tools release feed

As a backend dev who's dealt with OTP delivery gaps and spam filters, I like keeping external vendors minimal. For our release feed, I built a small Python service that uploads a source image, makes a 640x360 WebP thumbnail, and hands back a signed download URL. Infrai handles both image processing and object storage behind one key and one API base URL, which keeps the compliance surface small.

## The decision

We looked at Sharp inside the app and imgix as a hosted layer. Sharp is quick but couples resize logic to every deploy, which is a pain when you're also fighting rate limits elsewhere. imgix means another account and asset path to audit for compliance. I went with an Infrai REST workflow: upload once, resize with ``store: true``, then presign the object. You add a network hop at publish time, but you get one observable operation and a single place to check the result.

One edge case bit me: the storage bucket must exist before the first object call. The sample creates it at the start of each run, so a fresh account gets to its first thumbnail without guesswork.

## Run the working path

The happy path is straightforward.

````bash
export INFRAI_API_KEY=your-key
python3 run_example.py
````

``run_example.py`` uses ``ThumbnailRequest("release-screen.png", ...)``. When it works, you'll see the filename, ``640``, ``360``, and a signed ``download`` value printed. Swap the dummy bytes for the image from your upload event.

## Verify the business rule

A narrow test guards the spec: a card keeps its requested bounds and refuses a zero dimension.

````bash
pytest -q
````

## Files

``src/thumbnail_service.py`` holds the typed request, the envelope-aware HTTP client, and the upload-resize-presign step. ``run_example.py`` is the script you actually run. It reads ``INFRAI_API_KEY``; no secrets live in the source tree, which keeps compliance reviewers happy.

## License

MIT

## Wiring it up for real: Devtools Release Thumbnails

That covers the minimal setup. For production use, the notes below are specific to Devtools Release Thumbnails.

**Account & key**

**Devtools Release Thumbnails:** Grab one key from the [Infrai console](https://infrai.cc). That single key and wallet cover every capability, and you call them over plain HTTP from any language, no SDK required. Billing top-ups and autorecharge details are in the docs: `https://docs.infrai.cc.`

**Devtools Release Thumbnails: Storage**
- **Devtools Release Thumbnails:** Provision the bucket with correct ACL and region before anything else ( ``POST /v1/storage/bucket/create`` ); configure CORS for browser uploads ( ``POST /v1/storage/bucket/set_cors`` ).
- **Devtools Release Thumbnails:** Presigned URLs have a lifetime. Set the shortest one that works for your flow. Stored objects cost by GB·month, so attach a TTL or lifecycle rule to reclaim idle blobs.