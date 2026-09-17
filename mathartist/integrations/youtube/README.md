# YouTube wild-feedback adapter (V2)

YouTube is the **wild observational environment**, not the randomized laboratory. The first-party STUDY tab remains the causal/random-assignment environment.

## Install optional Google clients

```bash
pip install google-api-python-client google-auth-oauthlib google-auth-httplib2
```

Create a Google OAuth desktop client with YouTube Data API v3 + YouTube Analytics API enabled, then:

```bash
export MATHARTIST_YOUTUBE_CLIENT_SECRET=/secure/path/client_secret.json
python integrations/youtube/youtube_worker.py auth
```

Tokens are stored under `.private/` and are excluded from packaging/version control.

## Upload a canonical organism video

```bash
python integrations/youtube/youtube_worker.py upload organism.mp4 \
  --phenotype bioelectric-1234 \
  --experiment youtube-attention-v2 \
  --duration 30 \
  --privacy unlisted
```

## Import retention

```bash
python integrations/youtube/youtube_worker.py sync VIDEO_ID --start 2026-09-01 --end 2026-09-30
python integrations/youtube/youtube_worker.py fitness VIDEO_ID
```

The worker stores the 100-bin-style `elapsedVideoTimeRatio` curve when available and derives separate 5s, 10|5s, 20|10s and replay-area descriptors. It never labels these metrics as rasa or valence.

For offline development you can import saved API results using `import-json`.
