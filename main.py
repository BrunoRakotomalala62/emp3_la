from flask import Flask, request, jsonify, Response, send_file
import json
import yt_dlp
import os
import tempfile
import threading
import time
from functools import lru_cache

app = Flask(__name__)

DOWNLOADS_DIR = "/tmp/downloads"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# Cache pour les résultats de recherche (expire après 5 minutes)
search_cache = {}
CACHE_DURATION = 300  # 5 minutes

def format_duration(seconds):
    """Convert seconds to MM:SS format"""
    if not seconds:
        return "N/A"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"

def format_size(bytes_size):
    """Convert bytes to MB format"""
    if not bytes_size:
        return "N/A"
    mb = bytes_size / (1024 * 1024)
    return f"{mb:.2f} MB"

def get_cached_results(query, max_results):
    """Check if we have cached results for this query"""
    cache_key = f"{query}:{max_results}"
    if cache_key in search_cache:
        cached_time, results = search_cache[cache_key]
        if time.time() - cached_time < CACHE_DURATION:
            return results
        else:
            del search_cache[cache_key]
    return None

def set_cached_results(query, max_results, results):
    """Cache search results"""
    cache_key = f"{query}:{max_results}"
    search_cache[cache_key] = (time.time(), results)

def search_music(query, max_results=10):
    """Search for music using yt-dlp - OPTIMIZED VERSION"""
    
    # Check cache first
    cached = get_cached_results(query, max_results)
    if cached is not None:
        return cached
    
    results = []
    
    # Use extract_flat=True for FAST search (no metadata fetching per video)
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,  # IMPORTANT: Fast mode - only basic info
        'default_search': 'ytsearch',
        'noplaylist': True,
        'skip_download': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_query = f"ytsearch{max_results}:{query}"
            info = ydl.extract_info(search_query, download=False)
            
            if 'entries' in info:
                for entry in info['entries']:
                    if entry is None:
                        continue
                    
                    video_id = entry.get('id', '')
                    title = entry.get('title', 'Unknown')
                    duration = entry.get('duration', 0)
                    
                    # Get best available thumbnail
                    thumbnail = entry.get('thumbnail', '')
                    if not thumbnail:
                        thumbnails = entry.get('thumbnails', [])
                        if thumbnails:
                            thumbnail = thumbnails[-1].get('url', '')
                    
                    # If no thumbnail from API, use YouTube default
                    if not thumbnail and video_id:
                        thumbnail = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
                    
                    results.append({
                        'titre': title,
                        'duree': format_duration(duration),
                        'duree_secondes': duration,
                        'image_url': thumbnail,
                        'taille_mp3': "~3-5 MB",  # Estimate - actual size fetched on download
                        'taille_mp4': "~10-50 MB",  # Estimate
                        'video_id': video_id,
                        'youtube_url': f"https://www.youtube.com/watch?v={video_id}",
                        'telecharger_mp3': f"/telecharger/mp3/{video_id}",
                        'telecharger_mp4': f"/telecharger/mp4/{video_id}",
                        'stream_mp3': f"/stream/mp3/{video_id}"
                    })
        
        # Cache the results
        set_cached_results(query, max_results, results)
                    
    except Exception as e:
        return {'error': str(e)}
    
    return results


@app.route('/')
def home():
    response_data = {
        'message': 'API MP3 Juice - Recherche et téléchargement de musique',
        'routes': {
            'recherche': '/recherche?audio=<votre_recherche>',
            'telecharger_mp3': '/telecharger/mp3/<video_id>',
            'telecharger_mp4': '/telecharger/mp4/<video_id>',
            'stream_mp3': '/stream/mp3/<video_id>'
        },
        'exemple': '/recherche?audio=odyai'
    }
    return Response(
        json.dumps(response_data, ensure_ascii=False, indent=2),
        mimetype='application/json; charset=utf-8'
    )


@app.route('/recherche', methods=['GET'])
def recherche():
    audio = request.args.get('audio', '')
    limit = request.args.get('limit', '10')
    
    try:
        limit = int(limit)
        limit = min(max(1, limit), 20)
    except:
        limit = 10
    
    if not audio:
        return jsonify({
            'error': 'Paramètre "audio" requis',
            'usage': '/recherche?audio=<votre_recherche>&limit=10'
        }), 400
    
    results = search_music(audio, max_results=limit)
    
    if isinstance(results, dict) and 'error' in results:
        response_data = {
            'recherche': audio,
            'error': results['error'],
            'resultats': []
        }
    else:
        response_data = {
            'recherche': audio,
            'nombre_resultats': len(results),
            'resultats': results
        }
    
    response = Response(
        json.dumps(response_data, ensure_ascii=False, indent=2),
        mimetype='application/json; charset=utf-8'
    )
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


@app.route('/telecharger/mp3/<video_id>', methods=['GET'])
def telecharger_mp3(video_id):
    """Download audio as MP3"""
    try:
        output_path = os.path.join(DOWNLOADS_DIR, f"{video_id}.mp3")
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(DOWNLOADS_DIR, f"{video_id}.%(ext)s"),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
        }
        
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', video_id)
        
        if os.path.exists(output_path):
            return send_file(
                output_path,
                as_attachment=True,
                download_name=f"{title}.mp3",
                mimetype='audio/mpeg'
            )
        else:
            for ext in ['m4a', 'webm', 'opus']:
                alt_path = os.path.join(DOWNLOADS_DIR, f"{video_id}.{ext}")
                if os.path.exists(alt_path):
                    return send_file(
                        alt_path,
                        as_attachment=True,
                        download_name=f"{title}.{ext}",
                        mimetype='audio/mpeg'
                    )
        
        return jsonify({'error': 'Fichier non trouvé après téléchargement'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/telecharger/mp4/<video_id>', methods=['GET'])
def telecharger_mp4(video_id):
    """Download video as MP4 in lowest quality (360p or less)"""
    try:
        output_path = os.path.join(DOWNLOADS_DIR, f"{video_id}.mp4")
        
        ydl_opts = {
            'format': 'worstvideo[ext=mp4][height<=360]+worstaudio[ext=m4a]/worst[ext=mp4][height<=360]/worstvideo[ext=mp4]+worstaudio[ext=m4a]/worst[ext=mp4]/worst',
            'outtmpl': output_path,
            'merge_output_format': 'mp4',
            'quiet': True,
        }
        
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', video_id)
        
        if os.path.exists(output_path):
            return send_file(
                output_path,
                as_attachment=True,
                download_name=f"{title}.mp4",
                mimetype='video/mp4'
            )
        
        return jsonify({'error': 'Fichier non trouvé après téléchargement'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/stream/mp3/<video_id>', methods=['GET'])
def stream_mp3(video_id):
    """Get direct streaming URL for MP3"""
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
        }
        
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info.get('url')
            
            if audio_url:
                return jsonify({
                    'titre': info.get('title'),
                    'stream_url': audio_url,
                    'duree': format_duration(info.get('duration')),
                })
        
        return jsonify({'error': 'URL non trouvée'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
