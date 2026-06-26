# YouTube Downloader API — Documentation

Base URL: `http://{host}:{port}/api/v1`

---

## 1. Health Check

```
GET /api/v1/health
```

Returns API status, version, and FFmpeg availability.

**Response** `200 OK`

```json
{
  "status": "ok",
  "version": "1.0.0",
  "ffmpeg_available": true
}
```

| Field | Type | Description |
|---|---|---|
| `status` | string | Always `"ok"` when healthy |
| `version` | string | API version from config |
| `ffmpeg_available` | bool | Whether FFmpeg is detected on the server |

**Example**
```bash
curl http://localhost:8000/api/v1/health
```

---

## 2. Get Video Info

```
POST /api/v1/info
```

Extracts metadata for a public YouTube video.

**Request Body** `application/json`

```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `url` | string (URL) | Yes | Full YouTube video URL |

**Response** `200 OK`

```json
{
  "id": "dQw4w9WgXcQ",
  "title": "Rick Astley - Never Gonna Give You Up",
  "duration": 212,
  "duration_string": "3:32",
  "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
  "channel": "Rick Astley",
  "uploader": "Rick Astley",
  "view_count": 1560000000,
  "like_count": 17000000,
  "upload_date": "20091025",
  "description": "The official video for Never Gonna Give You Up...",
  "webpage_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
}
```

| Field | Type | Description |
|---|---|---|
| `id` | string | YouTube video ID |
| `title` | string | Video title |
| `duration` | int\|null | Duration in seconds |
| `duration_string` | string\|null | Human-readable duration |
| `thumbnail` | string\|null | Thumbnail URL |
| `channel` | string\|null | Channel name |
| `uploader` | string\|null | Uploader name |
| `view_count` | int\|null | Total view count |
| `like_count` | int\|null | Total like count |
| `upload_date` | string\|null | Upload date (YYYYMMDD) |
| `description` | string\|null | First 500 characters |
| `webpage_url` | string\|null | Canonical URL |

**Error Responses**

| Status | Body | Cause |
|---|---|---|
| `400` | `{"detail": "Invalid or unsupported YouTube URL"}` | URL did not match YouTube pattern |
| `502` | `{"detail": "Extraction failed: ..."}` | yt-dlp could not extract info |

**Example**
```bash
curl -X POST http://localhost:8000/api/v1/info \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

---

## 3. List Formats

```
POST /api/v1/formats
```

Lists all downloadable formats for a public YouTube video.

**Request Body** — same as `POST /info`

```json
{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
```

**Response** `200 OK`

```json
{
  "id": "dQw4w9WgXcQ",
  "title": "Rick Astley - Never Gonna Give You Up",
  "formats": [
    {
      "format_id": "137",
      "ext": "mp4",
      "resolution": "1920x1080",
      "fps": 30.0,
      "vcodec": "avc1.640028",
      "acodec": "none",
      "filesize": null,
      "filesize_approx": 78456789,
      "tbr": 2896.0,
      "note": "1080p"
    }
  ]
}
```

**FormatInfo Fields**

| Field | Type | Description |
|---|---|---|
| `format_id` | string | Unique format identifier (used in download requests) |
| `ext` | string | File extension (`mp4`, `webm`, `m4a`, `opus`, ...) |
| `resolution` | string\|null | E.g. `"1920x1080"` or `"audio only"` |
| `fps` | float\|null | Frames per second |
| `vcodec` | string\|null | Video codec, `"none"` for audio-only |
| `acodec` | string\|null | Audio codec, `"none"` for video-only |
| `filesize` | int\|null | Exact file size in bytes (rare) |
| `filesize_approx` | int\|null | Approximate file size in bytes |
| `tbr` | float\|null | Total bitrate in kbps |
| `note` | string\|null | Quality label shown to users |

**Example**
```bash
curl -X POST http://localhost:8000/api/v1/formats \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

---

## 4. Download Audio

```
POST /api/v1/download/audio
```

Downloads the audio track. Returns the audio file directly.

**Request Body** `application/json`

```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "format_id": "251",
  "convert_mp3": true
}
```

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `url` | string (URL) | Yes | — | YouTube video URL |
| `format_id` | string\|null | No | `null` | Specific audio format ID from `/formats`. If omitted, picks best available audio. |
| `convert_mp3` | bool | No | `true` | Convert to MP3 via FFmpeg (ignored if FFmpeg unavailable) |

**Response** `200 OK`

| Content-Type | Description |
|---|---|
| `audio/mpeg` | MP3 file (when `convert_mp3=true` and FFmpeg available) |
| `audio/mp4` | M4A file |
| `audio/opus` | Opus file |
| `audio/ogg` | Ogg file |

The file is streamed with a `Content-Disposition` header containing the filename. Temporary files are auto-deleted **60 seconds** after the response.

**Error Responses**

| Status | Body | Cause |
|---|---|---|
| `400` | `{"detail": "Invalid or unsupported YouTube URL"}` | Invalid URL |
| `502` | `{"detail": "Download failed: ..."}` | yt-dlp download error |

**Examples**
```bash
# Best quality, convert to MP3
curl -X POST http://localhost:8000/api/v1/download/audio \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}' \
  -o song.mp3

# Specific format, no MP3 conversion
curl -X POST http://localhost:8000/api/v1/download/audio \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ","format_id":"251","convert_mp3":false}' \
  -o song.webm
```

---

## 5. Download Video

```
POST /api/v1/download/video
```

Downloads a video. Supports quality selection by format ID or resolution.

**Request Body** `application/json`

```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "format_id": "137+140",
  "resolution": "1080p"
}
```

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `url` | string (URL) | Yes | — | YouTube video URL |
| `format_id` | string\|null | No | `null` | Format ID from `/formats`. Use `"137+140"` to combine video+audio. If omitted, best quality is used. |
| `resolution` | string\|null | No | `null` | Human-readable resolution (`2160p`, `1440p`, `1080p`, `720p`, `480p`, `360p`). Ignored if `format_id` is set. |

> **Note:** `format_id` takes precedence over `resolution`. If neither is provided, the best available quality is selected.

**Response** `200 OK`

| Content-Type | Description |
|---|---|
| `video/mp4` | MP4 file (with FFmpeg) |
| `video/webm` | WebM file |
| `video/x-matroska` | MKV file |

The file is streamed with a `Content-Disposition` header. Temporary files are auto-deleted **120 seconds** after the response.

**Error Responses**

| Status | Body | Cause |
|---|---|---|
| `400` | `{"detail": "Invalid or unsupported YouTube URL"}` | Invalid URL |
| `502` | `{"detail": "Download failed: ..."}` | yt-dlp download error |
| `502` | `{"detail": "The requested format is not available for this video"}` | Format ID not found |
| `502` | `{"detail": "This video is unavailable or private"}` | Private/missing video |
| `502` | `{"detail": "Download failed (empty file). Try a different quality."}` | HLS stream failure |

**Examples**
```bash
# Best quality (video + audio merged)
curl -X POST http://localhost:8000/api/v1/download/video \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}' \
  -o video.mp4

# 720p
curl -X POST http://localhost:8000/api/v1/download/video \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ","resolution":"720p"}' \
  -o video_720p.mp4

# Specific format combination
curl -X POST http://localhost:8000/api/v1/download/video \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ","format_id":"137+140"}' \
  -o video_1080p.mp4
```

---

## Error Reference

| Status | Meaning |
|---|---|
| `200` | Success — file returned or JSON payload |
| `400` | Invalid request (bad URL, missing field) |
| `500` | Unhandled internal server error |
| `502` | Bad gateway — yt-dlp operation failed (bad URL, network issue, YouTube error) |

All error responses follow the same shape:

```json
{"detail": "Human-readable error message"}
```

### Common 502 error messages

| Detail | Cause |
|---|---|
| `Invalid or unsupported YouTube URL` | URL pattern mismatch |
| `This video is unavailable or private` | Video is private, age-restricted, or taken down |
| `This video requires authentication...` | Login required (not supported — ethical restriction) |
| `The requested format is not available...` | Format ID does not exist for this video |
| `Download failed (empty file)...` | HLS stream failed — try a different quality or retry |
| `Download failed: ...` | Generic yt-dlp error |

---

## Resolution Reference

When using the `resolution` parameter on `POST /api/v1/download/video`:

| Resolution | yt-dlp format selector |
|---|---|
| `2160p` | Best video ≤ 2160p + best audio |
| `1440p` | Best video ≤ 1440p + best audio |
| `1080p` | Best video ≤ 1080p + best audio |
| `720p` | Best video ≤ 720p + best audio |
| `480p` | Best video ≤ 480p + best audio |
| `360p` | Best video ≤ 360p + best audio |

> With FFmpeg available, video and audio streams are merged into a single MP4. Without FFmpeg, progressive formats (pre-merged) are preferred but are limited to 720p.

---

## OpenAPI / Swagger

Interactive docs are available at:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **OpenAPI JSON:** `http://localhost:8000/openapi.json`

---

## Configuration

All settings via environment variables or `.env`. See `.env.example`.

| Variable | Default | Description |
|---|---|---|
| `HOST` | `0.0.0.0` | Bind address |
| `PORT` | `8000` | Bind port |
| `DOWNLOAD_DIR` | `~/ytdownloader_tmp` | Temporary download storage |
| `MAX_FILE_AGE_SECONDS` | `600` | Age after which files are cleaned up |
| `CLEANUP_INTERVAL_SECONDS` | `120` | Periodic sweep interval |
| `CORS_ORIGINS` | `*` | Comma-separated allowed origins |
| `LOG_LEVEL` | `INFO` | Python logging level |

---

## Client Integration Pattern

Typical download flow for a client app:

```
1. POST /api/v1/info          → get title, thumbnail, duration
2. POST /api/v1/formats       → get list of quality options
3. POST /api/v1/download/video → stream the file
                 (or)
   POST /api/v1/download/audio → stream the file
```

### Python example
```python
import requests

BASE = "http://localhost:8000/api/v1"

# Get video info
r = requests.post(f"{BASE}/info", json={"url": "https://youtu.be/..."})
info = r.json()
print(info["title"])

# Download video
r = requests.post(f"{BASE}/download/video",
    json={"url": "https://youtu.be/...", "resolution": "720p"},
    stream=True)
with open(f"{info['title']}.mp4", "wb") as f:
    for chunk in r.iter_content(chunk_size=8192):
        f.write(chunk)
```

### JavaScript example
```javascript
const BASE = "http://localhost:8000/api/v1";

// Get info
const info = await fetch(`${BASE}/info`, {
  method: "POST",
  headers: {"Content-Type": "application/json"},
  body: JSON.stringify({url: "https://youtu.be/..."}),
}).then(r => r.json());

// Download video (Node.js)
const axios = require("axios");
const fs = require("fs");
const { data: stream } = await axios.post(`${BASE}/download/video`,
  {url: "https://youtu.be/...", resolution: "720p"},
  {responseType: "stream"}
);
stream.pipe(fs.createWriteStream("video.mp4"));
```
