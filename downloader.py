import yt_dlp
import os
import re

_FFMPEG_PATH = "ffmpeg"

try:
    import imageio_ffmpeg
    _FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    for candidate in ["/system/bin/ffmpeg", "/data/data/org.baixador/files/ffmpeg"]:
        if os.path.exists(candidate):
            _FFMPEG_PATH = candidate
            break

def sanitize_filename(title):
    return re.sub(r'[<>:"/\\|?*]', '_', title)

AUDIO_QUALITY_MAP = {
    "320kbps": "320",
    "192kbps": "192",
    "128kbps": "128",
}

def get_format_option(format_choice):
    formats = {
        "Melhor Vídeo (MP4)": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "Melhor Áudio (MP3)": "bestaudio/best",
        "Vídeo 1080p (MP4)": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]",
        "Vídeo 720p (MP4)": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]",
        "Vídeo 480p (MP4)": "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]",
    }
    return formats.get(format_choice, "best")

class Downloader:
    def __init__(self, progress_callback=None, status_callback=None):
        self.progress_callback = progress_callback
        self.status_callback = status_callback

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            if self.progress_callback:
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded = d.get('downloaded_bytes', 0)
                if total > 0:
                    pct = (downloaded / total) * 100
                    self.progress_callback(pct)
                speed = d.get('speed', 0)
                if speed:
                    speed_mb = speed / 1024 / 1024
                    if self.status_callback:
                        self.status_callback(f"Baixando... {speed_mb:.1f} MB/s")
        elif d['status'] == 'finished':
            if self.status_callback:
                self.status_callback("Processando...")

    def download(self, url, output_path, format_choice="Melhor Vídeo (MP4)", audio_quality="192kbps"):
        fmt = get_format_option(format_choice)
        is_audio = "áudio" in format_choice.lower() or "mp3" in format_choice.lower()
        aq = AUDIO_QUALITY_MAP.get(audio_quality, "192")

        ydl_opts = {
            'format': fmt,
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'progress_hooks': [self.progress_hook],
            'quiet': True,
            'no_warnings': True,
            'ffmpeg_location': _FFMPEG_PATH,
        }

        if is_audio:
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': aq,
            }]

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'desconhecido')
                ext = 'mp3' if is_audio else 'mp4'
                filename = f"{sanitize_filename(title)}.{ext}"
                filepath = os.path.join(output_path, filename)
                return True, filepath, title
        except Exception as e:
            return False, str(e), None
