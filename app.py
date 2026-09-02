import os
import json
import uuid
import yt_dlp
from flask import Flask, request, jsonify, send_file, send_from_directory
import threading

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.environ.get('SECRET_KEY', 'downloader-faster-secret-key')

DOWNLOAD_DIR = os.environ.get('DOWNLOAD_DIR', '/tmp/downloads')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

download_progress = {}

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/facebook-video-downloader.html')
def facebook(): return send_from_directory('.', 'facebook-video-downloader.html')

@app.route('/instagram-video-downloader.html')
def instagram(): return send_from_directory('.', 'instagram-video-downloader.html')

@app.route('/tiktok-video-downloader.html')
def tiktok(): return send_from_directory('.', 'tiktok-video-downloader.html')

@app.route('/twitter-video-downloader.html')
def twitter(): return send_from_directory('.', 'twitter-video-downloader.html')

@app.route('/pinterest-video-downloader.html')
def pinterest(): return send_from_directory('.', 'pinterest-video-downloader.html')

@app.route('/youtube-video-downloader.html')
def youtube(): return send_from_directory('.', 'youtube-video-downloader.html')

@app.route('/vimeo-video-downloader.html')
def vimeo(): return send_from_directory('.', 'vimeo-video-downloader.html')

@app.route('/reddit-video-downloader.html')
def reddit(): return send_from_directory('.', 'reddit-video-downloader.html')

@app.route('/dailymotion-video-downloader.html')
def dailymotion(): return send_from_directory('.', 'dailymotion-video-downloader.html')

@app.route('/linkedin-video-downloader.html')
def linkedin(): return send_from_directory('.', 'linkedin-video-downloader.html')

@app.route('/threads-video-downloader.html')
def threads(): return send_from_directory('.', 'threads-video-downloader.html')

@app.route('/tumblr-video-downloader.html')
def tumblr(): return send_from_directory('.', 'tumblr-video-downloader.html')

@app.route('/imgur-video-downloader.html')
def imgur(): return send_from_directory('.', 'imgur-video-downloader.html')

@app.route('/tedtalks-video-downloader.html')
def tedtalks(): return send_from_directory('.', 'tedtalks-video-downloader.html')

@app.route('/online-video-downloader.html')
def online(): return send_from_directory('.', 'online-video-downloader.html')

@app.route('/contact-us.html')
def contact(): return send_from_directory('.', 'contact-us.html')

@app.route('/privacy-policy.html')
def privacy(): return send_from_directory('.', 'privacy-policy.html')

@app.route('/terms-conditions.html')
def terms(): return send_from_directory('.', 'terms-conditions.html')

@app.route('/api/info', methods=['POST'])
def api_info():
    data = request.get_json()
    url = data.get('url', '').strip()
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    try:
        ydl_opts = {'quiet': True, 'no_warnings': True, 'skip_download': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info is None:
                return jsonify({'error': 'Could not fetch video info'}), 400
            formats = []
            seen_qualities = set()
            if 'formats' in info:
                for f in info['formats']:
                    if f.get('vcodec') == 'none' and f.get('acodec') != 'none':
                        format_id = f.get('format_id', '')
                        ext = f.get('ext', 'mp3')
                        abr = f.get('abr', 0)
                        if f'audio_{ext}' not in seen_qualities:
                            seen_qualities.add(f'audio_{ext}')
                            formats.append({
                                'format_id': format_id, 'type': 'audio',
                                'quality': f'{int(abr)}kbps' if abr else 'Best',
                                'ext': ext, 'filesize': f.get('filesize') or f.get('filesize_approx'),
                                'label': f'Audio ({ext.upper()}) - {int(abr)}kbps' if abr else f'Audio ({ext.upper()})'
                            })
                    elif f.get('vcodec') != 'none':
                        height = f.get('height')
                        ext = f.get('ext', 'mp4')
                        format_id = f.get('format_id', '')
                        fps = f.get('fps', 30)
                        if height:
                            quality_label = f'{height}p'
                            if quality_label not in seen_qualities:
                                seen_qualities.add(quality_label)
                                formats.append({
                                    'format_id': format_id, 'type': 'video',
                                    'quality': quality_label, 'ext': ext,
                                    'height': height, 'fps': fps,
                                    'filesize': f.get('filesize') or f.get('filesize_approx'),
                                    'label': f'{quality_label} {ext.upper()} {fps}fps'
                                })
            formats.sort(key=lambda x: x.get('height', 0) if x['type'] == 'video' else 0, reverse=True)
            formats.insert(0, {'format_id': 'best', 'type': 'merged', 'quality': 'Best Quality', 'ext': 'mp4', 'label': 'Best Quality (Video + Audio) MP4'})
            formats.append({'format_id': 'bestaudio', 'type': 'audio', 'quality': 'Best Audio', 'ext': 'mp3', 'label': 'Audio Only (MP3)'})
            return jsonify({
                'id': info.get('id', ''), 'title': info.get('title', 'Unknown'),
                'thumbnail': info.get('thumbnail', ''), 'duration': info.get('duration', 0),
                'uploader': info.get('uploader', 'Unknown'), 'formats': formats
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download', methods=['POST'])
def api_download():
    data = request.get_json()
    url = data.get('url', '').strip()
    format_id = data.get('format_id', 'best')
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    download_id = str(uuid.uuid4())
    thread = threading.Thread(target=process_download, args=(download_id, url, format_id))
    thread.daemon = True
    thread.start()
    return jsonify({'id': download_id, 'status': 'processing', 'message': 'Download started'})

def process_download(download_id, url, format_id):
    download_progress[download_id] = {'status': 'downloading', 'progress': 0, 'filename': None, 'error': None}
    try:
        output_dir = os.path.join(DOWNLOAD_DIR, download_id)
        os.makedirs(output_dir, exist_ok=True)
        def progress_hook(d):
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded = d.get('downloaded_bytes', 0)
                if total > 0:
                    download_progress[download_id]['progress'] = int((downloaded / total) * 100)
            elif d['status'] == 'finished':
                download_progress[download_id]['status'] = 'processing'
                download_progress[download_id]['progress'] = 100
        if format_id in ['best', 'bestaudio']:
            if format_id == 'bestaudio':
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
                    'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
                    'progress_hooks': [progress_hook],
                }
            else:
                ydl_opts = {
                    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                    'merge_output_format': 'mp4',
                    'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
                    'progress_hooks': [progress_hook],
                }
        else:
            ydl_opts = {
                'format': format_id,
                'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
                'progress_hooks': [progress_hook],
            }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if format_id == 'bestaudio':
                filename = os.path.splitext(filename)[0] + '.mp3'
            download_progress[download_id].update({'status': 'completed', 'filename': os.path.basename(filename), 'filepath': filename})
    except Exception as e:
        download_progress[download_id].update({'status': 'error', 'error': str(e)})

@app.route('/api/status/<download_id>')
def api_status(download_id):
    if download_id not in download_progress:
        return jsonify({'error': 'Download not found'}), 404
    return jsonify(download_progress[download_id])

@app.route('/api/file/<download_id>')
def api_file(download_id):
    if download_id not in download_progress:
        return jsonify({'error': 'Download not found'}), 404
    progress = download_progress[download_id]
    if progress['status'] != 'completed':
        return jsonify({'error': 'Download not completed'}), 400
    filepath = progress.get('filepath')
    if not filepath or not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    return send_file(filepath, as_attachment=True, download_name=progress['filename'])

@app.errorhandler(404)
def page_not_found(e):
    return send_from_directory('.', 'index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
