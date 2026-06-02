# Premium YouTube Downloader 🎥

A powerful, high-quality YouTube Downloader command-line tool built using Python and the robust `yt-dlp` library.

## Features

- 🎬 **Video Downloads**: Download YouTube videos in their best available quality (including 1080p, 2K, 4K, and 8K if available) in a clean MP4 format.
- 🎵 **Audio Extraction**: Extract high-quality audio (192kbps MP3) directly from videos.
- 📁 **Custom Output Directory**: Easily choose where to save the files; creates the directory automatically if it doesn't exist.
- 🛑 **Playlist Safety**: Avoids accidentally downloading a whole playlist when a URL contains playlist parameters.
- 🛠 **FFmpeg Powered**: Smooth merging of high-definition video and audio streams.

## Prerequisites

1. **Python**: Ensure you have Python 3 installed.
2. **FFmpeg**: Required for high-quality video merging and audio conversion.
   * *Windows*: Can be installed via `winget install Gyan.FFmpeg` or downloaded from gyan.dev.
   * *Mac*: `brew install ffmpeg`
   * *Linux*: `sudo apt install ffmpeg`

## Installation

Install the required Python dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Simply run the script in your terminal:

```bash
python yt.py
```

Then follow the prompts to:
1. Enter the YouTube URL.
2. Select whether to download **Video** (MP4) or **Audio** (MP3).
3. Specify the directory to save the file (or press Enter to use the current directory).
