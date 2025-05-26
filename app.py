import os
import subprocess
from flask import Flask, request, send_file, render_template_string

# Constants
COOKIES_PATH = "/mnt/data/cookies.txt"
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
{% elif error %}
    <p style="color:red;"><b>Error:</b> {{ error }}</p>
{% endif %}
"""

# Download + convert function
def download_and_convert(video_url):
    try:
        # Get video title
        title = subprocess.check_output([
            "yt-dlp",
            "--cookies", COOKIES_PATH,
            "--get-title",
            video_url
        ]).decode().strip()

        # Sanitize filename
        safe_title = "".join(c for c in title if c.isalnum() or c in " _-").rstrip()
        video_path = os.path.join(DOWNLOAD_DIR, f"{safe_title}_360p.mp4")
        audio_path = os.path.join(DOWNLOAD_DIR, f"{safe_title}.mp3")

        # Check if cached
        if os.path.exists(video_path) and os.path.exists(audio_path):
            return title, os.path.basename(video_path), os.path.basename(audio_path), None

        # Download 360p video
        subprocess.run([
            "yt-dlp",
            "--cookies", COOKIES_PATH,
            "-f", "best[height<=360][ext=mp4]",
            "-o", video_path,
            video_url
        ], check=True)

        # Extract MP3
        subprocess.run([
            "ffmpeg",
            "-i", video_path,
            "-vn",
            "-acodec", "libmp3lame",
            audio_path
        ], check=True)

        return title, os.path.basename(video_path), os.path.basename(audio_path), None
    except subprocess.CalledProcessError as e:
        return None, None, None, f"Download or conversion failed: {e}"
    except Exception as e:
        return None, None, None, str(e)

# Web routes
@app.route("/", methods=["GET", "POST"])
def index():
    title = video_filename = audio_filename = error = None
    if request.method == "POST":
        video_url = request.form.get("video_url")
        if video_url:
            title, video_filename, audio_filename, error = download_and_convert(video_url)
    return render_template_string(HTML, title=title, video_filename=video_filename, audio_filename=audio_filename, error=error)

@app.route("/download/video/<filename>")
def download_video(filename):
    return send_file(os.path.join(DOWNLOAD_DIR, filename), as_attachment=True)

@app.route("/download/audio/<filename>")
def download_audio(filename):
    return send_file(os.path.join(DOWNLOAD_DIR, filename), as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)