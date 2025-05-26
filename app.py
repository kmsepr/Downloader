import os
import subprocess
import unicodedata
import re
from flask import Flask, request, send_file, render_template_string, redirect, url_for

# Config
COOKIES_PATH = "/mnt/data/cookies.txt"
DOWNLOAD_DIR = "/mnt/data"

app = Flask(__name__)

HTML = """
<h1>Lecture Downloader</h1>

<form method="post">
    <label>Enter Video URL:</label><br>
    <input type="text" name="video_url" size="80" required>
    <button type="submit">Download</button>
</form>

{% if error %}
    <p style="color:red;"><b>Error:</b> {{ error }}</p>
{% endif %}

{% if title %}
    <p><b>Downloaded:</b> {{ title }}</p>
{% endif %}

<hr>
<h2>Cached Files</h2>
{% if files %}
    <table border="1" cellpadding="5" cellspacing="0">
        <tr><th>Title</th><th>Video (MP4)</th><th>Audio (MP3)</th><th>Actions</th></tr>
        {% for base in files %}
        <tr>
            <td>{{ base }}</td>
            <td><a href="{{ url_for('download_video', filename=base + '_360p.mp4') }}">MP4</a></td>
            <td><a href="{{ url_for('download_audio', filename=base + '.mp3') }}">MP3</a></td>
            <td><a href="{{ url_for('remove_file', base=base) }}">Remove</a></td>
        </tr>
        {% endfor %}
    </table>
{% else %}
    <p>No cached files found.</p>
{% endif %}
"""

# Utility: get cached base names (title without extension)
def get_cached_titles():
    files = os.listdir(DOWNLOAD_DIR)
    bases = set()
    for f in files:
        if f.endswith("_360p.mp4"):
            base = f[:-10]  # remove _360p.mp4
            if os.path.exists(os.path.join(DOWNLOAD_DIR, f"{base}.mp3")):
                bases.add(base)
    return sorted(bases)

# Utility: sanitize title to ASCII-safe filename
def sanitize(title):
    title = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode('ascii')
    title = re.sub(r'[^a-zA-Z0-9 _-]', '_', title)
    return title.strip()

# Downloader function
def download_and_convert(video_url):
    try:
        # Get title
        title = subprocess.check_output([
            "yt-dlp", "--cookies", COOKIES_PATH, "--get-title", video_url
        ]).decode().strip()

        safe_title = sanitize(title) or "video"

        video_path = os.path.join(DOWNLOAD_DIR, f"{safe_title}_360p.mp4")
        audio_path = os.path.join(DOWNLOAD_DIR, f"{safe_title}.mp3")

        # If both already exist, skip
        if os.path.exists(video_path) and os.path.exists(audio_path):
            return safe_title, None

        # Download video
        subprocess.run([
            "yt-dlp", "--cookies", COOKIES_PATH,
            "-f", "best[height<=360][ext=mp4]",
            "-o", video_path,
            video_url
        ], check=True)

        # Convert to MP3
        subprocess.run([
            "ffmpeg", "-i", video_path, "-vn", "-acodec", "libmp3lame", audio_path
        ], check=True)

        return safe_title, None

    except subprocess.CalledProcessError as e:
        return None, f"Download or conversion failed: {e}"
    except Exception as e:
        return None, str(e)

# Routes
@app.route("/", methods=["GET", "POST"])
def index():
    title = error = None
    if request.method == "POST":
        video_url = request.form.get("video_url")
        if video_url:
            title, error = download_and_convert(video_url)
    files = get_cached_titles()
    return render_template_string(HTML, title=title, error=error, files=files)

@app.route("/download/video/<filename>")
def download_video(filename):
    return send_file(os.path.join(DOWNLOAD_DIR, filename), as_attachment=True)

@app.route("/download/audio/<filename>")
def download_audio(filename):
    return send_file(os.path.join(DOWNLOAD_DIR, filename), as_attachment=True)

@app.route("/remove/<base>")
def remove_file(base):
    mp4 = os.path.join(DOWNLOAD_DIR, f"{base}_360p.mp4")
    mp3 = os.path.join(DOWNLOAD_DIR, f"{base}.mp3")
    if os.path.exists(mp4): os.remove(mp4)
    if os.path.exists(mp3): os.remove(mp3)
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)