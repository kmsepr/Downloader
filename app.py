import os
import subprocess
import datetime
import requests
from flask import Flask, request, redirect, url_for, send_file, render_template_string

# Constants
COOKIES_PATH = "/mnt/data/xylem_cookies.txt"
DOWNLOAD_DIR = "/mnt/data"

# PenPencil API base
PENPENCIL_API = "https://api.penpencil.co/v1/videos/video-url-details"
VIDEO_URL_BASE = "https://d1d34p8vz63oiq.cloudfront.net/0fd876f5-47db-4c13-aa88-81d51a66597b/master.mpd"

# Flask app
app = Flask(__name__)

# HTML Template
HTML = """
<h1>PenPencil Downloader</h1>
<form method="post">
    <label>Enter PenPencil childId:</label><br>
    <input type="text" name="child_id" size="60" required>
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

def fetch_signed_mpd(child_id):
    """Fetch the signed DASH .mpd URL from PenPencil API."""
    params = {
        "type": "RECORDED",
        "videoContainerType": "DASH",
        "reqType": "query",
        "childId": child_id,
        "parentId": "64d35df09bafa30018e3f598",
        "videoUrl": VIDEO_URL_BASE,
        "secondaryParentId": "64d3802cd6ec8e00180120fb",
        "clientVersion": "201"
    }
    r = requests.get(PENPENCIL_API, params=params)
    return r.json().get("data", {}).get("url")

def download_and_convert(dash_url, child_id):
    """Download video + extract MP3 using yt-dlp and ffmpeg."""
    try:
        # Title fallback to childId and date
        date_str = datetime.datetime.now().strftime("%Y%m%d")
        title = f"penpencil_{date_str}_{child_id}"

        video_path = os.path.join(DOWNLOAD_DIR, f"{title}_360p.mp4")
        audio_path = os.path.join(DOWNLOAD_DIR, f"{title}.mp3")

        # Download best video <= 360p
        subprocess.run([
            "yt-dlp",
            "-f", "best[height<=360][ext=mp4]",
            "-o", video_path,
            dash_url
        ], check=True)

        # Extract MP3 using ffmpeg
        subprocess.run([
            "ffmpeg",
            "-i", video_path,
            "-vn",
            "-acodec", "libmp3lame",
            audio_path
        ], check=True)

        return title, os.path.basename(video_path), os.path.basename(audio_path)

    except subprocess.CalledProcessError as e:
        print("Download failed:", e)
        return None, None, None

@app.route("/", methods=["GET", "POST"])
def index():
    title = video_filename = audio_filename = None
    if request.method == "POST":
        child_id = request.form.get("child_id")
        if child_id:
            signed_url = fetch_signed_mpd(child_id)
            if signed_url:
                title, video_filename, audio_filename = download_and_convert(signed_url, child_id)
    return render_template_string(HTML, title=title, video_filename=video_filename, audio_filename=audio_filename)

@app.route("/download/video/<filename>")
def download_video(filename):
    return send_file(os.path.join(DOWNLOAD_DIR, filename), as_attachment=True)

@app.route("/download/audio/<filename>")
def download_audio(filename):
    return send_file(os.path.join(DOWNLOAD_DIR, filename), as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
