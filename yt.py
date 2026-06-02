import os
import sys
import yt_dlp

# Force stdout/stderr to use UTF-8 encoding to prevent UnicodeEncodeError on Windows terminals
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

def download_youtube(video_url, save_path=".", download_type="video"):
    """
    Downloads a YouTube video or audio using yt-dlp.
    
    :param video_url: The full URL of the YouTube video or playlist.
    :param save_path: The directory where the file should be saved.
    :param download_type: 'video' for MP4 (best quality) or 'audio' for MP3.
    """
    # Normalize paths and check/create the save directory
    save_path = os.path.abspath(save_path)
    if not os.path.exists(save_path):
        try:
            os.makedirs(save_path)
            print(f"📁 Created directory: {save_path}")
        except Exception as e:
            print(f"❌ Failed to create directory '{save_path}': {e}")
            return False

    # Define base options
    ydl_opts = {
        'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
        'noplaylist': True,  # Prevent downloading entire playlist if URL contains playlist parameters
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
        print(f"\n🎵 Initializing audio download (MP3 format)...")
    else:
        ydl_opts.update({
            # Merges video and audio streams for high-def formats (e.g. 1080p, 4K)
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
        })
        print(f"\n🎬 Initializing video download (MP4 format - Best Quality)...")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        print("\n✅ Download and processing completed successfully!")
        return True
    except KeyboardInterrupt:
        print("\n🛑 Download cancelled by user.")
        return False
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        return False

def main():
    print("=" * 60)
    print("      🎥 PREMIUM YOUTUBE DOWNLOADER (Powered by yt-dlp)      ")
    print("=" * 60)
    
    try:
        url = input("🔗 Enter YouTube URL (press Enter for default): ").strip()
        if not url:
            url = "https://www.youtube.com/watch?v=e0e3x9dd6FM"
            print(f"👉 Using default URL: {url}")

        print("\nSelect Download Type:")
        print("1. 🎬 Video (Best Quality MP4)")
        print("2. 🎵 Audio Only (MP3)")
        choice = input("Enter your choice (1 or 2, default: 1): ").strip()
        
        download_type = "audio" if choice == "2" else "video"

        # Display and confirm directory
        default_path = os.getcwd()
        print(f"\n📁 Default save directory: {default_path}")
        custom_path = input("Enter save path (press Enter to use default): ").strip()
        save_path = custom_path if custom_path else default_path

        print("\n" + "-" * 50)
        download_youtube(url, save_path, download_type)
        print("-" * 50)
        
    except KeyboardInterrupt:
        print("\n\n👋 Exiting... Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()