# YouTube Downloader API

A production-grade REST API for downloading public YouTube content, built with FastAPI and yt-dlp.

> **Legal notice:** This tool is intended for downloading publicly available content only. Do not use it to bypass DRM, access paid/private content, or violate any terms of service.

## Project Structure

```
ytdownloader/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, lifespan, middleware
│   ├── config.py             # Settings via pydantic-settings + .env
│   ├── models.py             # Pydantic v2 request/response schemas
│   ├── routes/
│   │   ├── health.py         # GET  /api/v1/health
│   │   ├── info.py           # POST /api/v1/info, POST /api/v1/formats
│   │   └── download.py       # POST /api/v1/download/audio, /download/video
│   ├── services/
│   │   └── ytdlp.py          # yt-dlp wrapper (extract, download)
│   └── utils/
│       ├── validators.py     # URL validation, filename sanitization
│       └── cleanup.py        # Temp file cleanup (scheduled + deferred)
├── .env.example
├── .gitignore
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Requirements

- Python 3.11+
- FFmpeg (optional, required for MP3 conversion and video muxing)

## Quick Start

```bash
# 1. Clone and enter the project
cd ytdownloader

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy and edit environment config
cp .env.example .env

# 5. Run the server
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

## API Endpoints

### Health Check

```bash
curl http://localhost:8000/api/v1/health
```

### Get Video Info

```bash
curl -X POST http://localhost:8000/api/v1/info \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

### List Available Formats

```bash
curl -X POST http://localhost:8000/api/v1/formats \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

### Download Audio

```bash
# Default (best audio, convert to MP3 if FFmpeg is available)
curl -X POST http://localhost:8000/api/v1/download/audio \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}' \
  -o audio.mp3

# Specific format, no conversion
curl -X POST http://localhost:8000/api/v1/download/audio \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "format_id": "251", "convert_mp3": false}' \
  -o audio.webm
```

### Download Video

```bash
# Best quality
curl -X POST http://localhost:8000/api/v1/download/video \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}' \
  -o video.mp4

# 720p
curl -X POST http://localhost:8000/api/v1/download/video \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "resolution": "720p"}' \
  -o video_720p.mp4

# Specific format ID
curl -X POST http://localhost:8000/api/v1/download/video \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "format_id": "137+140"}' \
  -o video.mp4
```

## Configuration

All settings are configured via environment variables or `.env` file:

| Variable | Default | Description |
|---|---|---|
| `APP_NAME` | YouTube Downloader API | Application name |
| `APP_VERSION` | 1.0.0 | Shown in health check and docs |
| `DEBUG` | false | Enable debug mode |
| `HOST` | 0.0.0.0 | Bind host |
| `PORT` | 8000 | Bind port |
| `WORKERS` | 1 | Uvicorn worker count |
| `DOWNLOAD_DIR` | ~/ytdownloader_tmp | Temporary download directory |
| `MAX_FILE_AGE_SECONDS` | 600 | Max age before cleanup (seconds) |
| `CLEANUP_INTERVAL_SECONDS` | 120 | Periodic cleanup interval |
| `CORS_ORIGINS` | * | Comma-separated allowed origins |
| `LOG_LEVEL` | INFO | Logging level |

## Docker Deployment

```bash
# Build and run
docker compose up -d

# Or manually
docker build -t ytdownloader .
docker run -d -p 8000:8000 --name ytdownloader ytdownloader
```

## Linux VPS Deployment

```bash
# Install system dependencies
sudo apt update && sudo apt install -y python3.11 python3.11-venv ffmpeg

# Setup application
cd /opt
git clone <your-repo> ytdownloader && cd ytdownloader
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env as needed

# Run with multiple workers behind a reverse proxy
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Systemd Service (optional)

Create `/etc/systemd/system/ytdownloader.service`:

```ini
[Unit]
Description=YouTube Downloader API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/ytdownloader
Environment=PATH=/opt/ytdownloader/.venv/bin
ExecStart=/opt/ytdownloader/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now ytdownloader
```

### Nginx Reverse Proxy (optional)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        client_max_body_size 0;
    }
}
```

## Notes

- **FFmpeg** is required for MP3 conversion and merging separate video+audio streams into MP4. Without it, you get the native format from YouTube.
- Downloaded files are automatically deleted after being served (60s for audio, 120s for video) and a periodic cleanup removes any files older than `MAX_FILE_AGE_SECONDS`.
- The API validates that URLs match known YouTube URL patterns before processing.
