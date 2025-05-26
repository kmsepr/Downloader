import os
import subprocess
from flask import Flask, request, redirect, url_for, send_file, render_template_string

# Constants
COOKIES_PATH = "/mnt/data/cookies.txt"
VIDEO_PATH = "/mnt/data/lecture_360p.mp4"
AUDIO_PATH = "/mnt/data/lecture.mp3"

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

{% if downloaded %}
    <p><b>Download ready:</b></p>
    <ul>
        <li><a href="{{ url_for('download_video') }}">Download 360p Video (MP4)</a></li>
        <li><a href="{{ url_for('download_audio') }}">Download Audio (MP3)</a></li>
    </ul>
{% endif %}
"""

# Download + convert function
def download_and_convert(video_url):
    try:
        # Download 360p video
        subprocess.run([
            "yt-dlp",
            "--cookies", COOKIES_PATH,
            "-f", "best[height<=360][ext=mp4]",
            "-o", VIDEO_PATH,
            video_url
        ], check=True)

        # Extract MP3
        subprocess.run([
            "ffmpeg",
            "-i", VIDEO_PATH,
            "-vn",
            "-acodec", "libmp3lame",
            AUDIO_PATH
        ], check=True)

        return True
    except subprocess.CalledProcessError as e:
        print("Download failed:", e)
        return False

# Web routes
@app.route("/", methods=["GET", "POST"])
def index():
    downloaded = False
    if request.method == "POST":
        video_url = request.form.get("video_url")
        if video_url:
            downloaded = download_and_convert(video_url)
    return render_template_string(HTML, downloaded=downloaded)

@app.route("/download/video")
def download_video():
    return send_file(VIDEO_PATH, as_attachment=True)

@app.route("/download/audio")
def download_audio():
    return send_file(AUDIO_PATH, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
