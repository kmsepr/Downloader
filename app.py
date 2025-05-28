import os
import subprocess
from flask import Flask, request, redirect, url_for, send_file, render_template_string

# Constants
COOKIES_PATH = "/mnt/data/xylem_cookies.txt"
DOWNLOAD_DIR = "/mnt/data"

# Flask app
app = Flask(__name__)

# HTML Template
HTML = """
<h1>Downloader</h1>
<form method="post">
    <label>Enter Video URL:</label><br>
    <input type="text" name="video_url" size="80" required>
    <button type="submit">Download</button>
</form>

{% if title %}
    <p><b>Download ready:</b> {{ title }}</p>
    <ul>
        <li><a href="{{ url_for('download_video', filename=video_filename) }}">Download 360p Video (MP4)</a></li>
        <li><a href="{{ url_for('download_audio', filename=audio_filename) }}">Download Audio (MP3)</a></li>
    </ul>
{% endif %}
"""

def download_and_convert(video_url):
    try:
        print("[INFO] Getting video title...")
        title = subprocess.check_output([
            "yt-dlp",
            "--cookies", COOKIES_PATH,
            "--get-title",
            video_url
        ]).decode().strip()

        print("[INFO] Title:", title)

        safe_title = "".join(c for c in title if c.isalnum() or c in " _-").rstrip()
        video_path = os.path.join(DOWNLOAD_DIR, f"{safe_title}_360p.mp4")
        audio_path = os.path.join(DOWNLOAD_DIR, f"{safe_title}.mp3")

        print("[INFO] Downloading 360p video...")
        subprocess.run([
            "yt-dlp",
            "--cookies", COOKIES_PATH,
            "-f", "best[height<=360][ext=mp4]",
            "-o", video_path,
            video_url
        ], check=True)
        print("[INFO] Video downloaded to:", video_path)

        print("[INFO] Extracting audio (MP3)...")
        subprocess.run([
            "yt-dlp",
            "--cookies", COOKIES_PATH,
            "--extract-audio",
            "--audio-format", "mp3",
            "-o", audio_path,
            video_url
        ], check=True)
        print("[INFO] Audio saved to:", audio_path)

        return title, os.path.basename(video_path), os.path.basename(audio_path)
    except subprocess.CalledProcessError as e:
        print("[ERROR] Download or conversion failed:", e)
        return None, None, None

@app.route("/", methods=["GET", "POST"])
def index():
    title = video_filename = audio_filename = None
    if request.method == "POST":
        video_url = request.form.get("video_url")
        if video_url:
            title, video_filename, audio_filename = download_and_convert(video_url)
    return render_template_string(HTML, title=title, video_filename=video_filename, audio_filename=audio_filename)

@app.route("/download/video/<filename>")
def download_video(filename):
    return send_file(os.path.join(DOWNLOAD_DIR, filename), as_attachment=True)

@app.route("/download/audio/<filename>")
def download_audio(filename):
    return send_file(os.path.join(DOWNLOAD_DIR, filename), as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)