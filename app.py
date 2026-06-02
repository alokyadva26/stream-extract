import os
import asyncio
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import yt_dlp
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi.background import BackgroundTasks
import time

# Dictionary to hold progress information
download_progress = {}

app = FastAPI(title="Web-Based YouTube Downloader")

# Setup CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure downloads directory exists
# On serverless environments like Vercel, the root filesystem is read-only, so we use /tmp
if os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV"):
    DOWNLOADS_DIR = "/tmp"
else:
    DOWNLOADS_DIR = os.path.abspath("downloads")
    os.makedirs(DOWNLOADS_DIR, exist_ok=True)

class DownloadRequest(BaseModel):
    url: str
    format: Optional[str] = "video"  # "video" or "audio"
    task_id: Optional[str] = None

def delete_file(file_path: str):
    """Background task to delete file after sending it."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted temporary file: {file_path}")
    except Exception as e:
        print(f"Error deleting file {file_path}: {e}")

def run_yt_dlp(url: str, download_type: str, task_id: str = None) -> str:
    """Synchronous function to run yt-dlp. Runs in a separate thread."""
    import uuid
    # Use a unique identifier to prevent concurrent downloads from overwriting each other
    unique_id = str(uuid.uuid4())[:8]

    def progress_hook(d):
        if not task_id:
            return
        if d['status'] == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            if total > 0:
                percent = (downloaded / total) * 100
                download_progress[task_id] = {
                    'status': 'downloading',
                    'percent': percent,
                    'downloaded': downloaded,
                    'total': total
                }
        elif d['status'] == 'finished':
            download_progress[task_id] = {
                'status': 'processing',
                'percent': 100
            }
    
    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOADS_DIR, f'%(title)s_{unique_id}.%(ext)s'),
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'restrictfilenames': True,  # Prevent unicode issues in filenames
        'concurrent_fragment_downloads': 10,  # Massively speed up dash/hls fragmented downloads
        'progress_hooks': [progress_hook],
    }

    if download_type == "audio":
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    else:
        ydl_opts.update({
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
        })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info and download
            info = ydl.extract_info(url, download=True)
            
            # Identify the final filename. 
            # If postprocessing happened (like to mp3), the extension might have changed.
            if 'requested_downloads' in info and len(info['requested_downloads']) > 0:
                final_file = info['requested_downloads'][0].get('filepath')
            else:
                # Fallback to prepare_filename
                final_file = ydl.prepare_filename(info)
                
                # Manual extension fix for mp3 if needed
                if download_type == "audio" and not final_file.endswith(".mp3"):
                    final_file = os.path.splitext(final_file)[0] + ".mp3"
                elif download_type == "video" and not final_file.endswith(".mp4"):
                    final_file = os.path.splitext(final_file)[0] + ".mp4"
            
            if not os.path.exists(final_file):
                raise Exception(f"Downloaded file not found at {final_file}")
                
            return final_file
    except Exception as e:
        raise Exception(str(e))

@app.post("/api/download")
async def download_video(req: DownloadRequest, background_tasks: BackgroundTasks):
    if req.task_id:
        download_progress[req.task_id] = {'status': 'starting', 'percent': 0}
    try:
        # Run yt-dlp in a thread so it doesn't block the FastAPI event loop
        file_path = await asyncio.to_thread(run_yt_dlp, req.url, req.format, req.task_id)
        
        # Determine filename for download
        filename = os.path.basename(file_path)
        
        # Delete file after serving using a background task
        background_tasks.add_task(delete_file, file_path)
        
        return FileResponse(
            path=file_path, 
            filename=filename,
            media_type='application/octet-stream'
        )
    except Exception as e:
        if req.task_id:
            download_progress[req.task_id] = {'status': 'error', 'percent': 0, 'error': str(e)}
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/progress/{task_id}")
async def get_progress(task_id: str):
    return download_progress.get(task_id, {'status': 'unknown', 'percent': 0})

# Mount static files (frontend)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def get_index():
    with open(os.path.join("static", "index.html"), "r", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
