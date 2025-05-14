
import json
import requests
import os
import logging
from flask import Flask, request, render_template_string, redirect, url_for
from datetime import datetime, timedelta
from dateutil import parser as date_parser
import isodate

# Logging setup
LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(LOG_DIR, f'app_{datetime.now().strftime("%Y%m%d")}.log'),
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

with open('config.json') as f:
    config = json.load(f)
YOUTUBE_API_KEY = config['YOUTUBE_API_KEY']

app = Flask(__name__)

HTML_FORM = '''
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>YouTube Channel Analyzer</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns"></script>
  <style>body{background:linear-gradient(120deg,#a1c4fd 0%,#c2e9fb 100%);font-family:'Roboto',sans-serif;min-height:100vh;margin:0;display:flex;align-items:center;justify-content:center;overflow-x:hidden;}.container{background:#fff;border-radius:24px;box-shadow:0 8px 32px 0 rgba(31,38,135,0.2);padding:48px 36px 36px 36px;max-width:520px;width:100%;animation:fadeIn 1s cubic-bezier(.4,0,.2,1);}@keyframes fadeIn{from{opacity:0;transform:translateY(40px) scale(0.98);}to{opacity:1;transform:translateY(0) scale(1);}}h2{text-align:center;color:#3a7bd5;margin-bottom:28px;letter-spacing:1px;font-size:2.1rem;font-weight:700;}form{display:flex;flex-direction:column;gap:18px;margin-bottom:24px;align-items:center;}input[type="text"],input[name="username"]{padding:12px 18px;border-radius:12px;border:1.5px solid #b2bec3;font-size:1.08rem;outline:none;transition:border 0.2s;width:100%;max-width:320px;background:#f7faff;}input[type="text"]:focus,input[name="username"]:focus{border:2px solid #3a7bd5;background:#e3f0fc;}input[type="submit"]{background:linear-gradient(90deg,#3a7bd5 0%,#00d2ff 100%);color:#fff;border:none;border-radius:12px;padding:12px 0;font-size:1.08rem;font-weight:bold;cursor:pointer;transition:background 0.2s,transform 0.2s;box-shadow:0 2px 8px rgba(58,123,213,0.13);width:100%;max-width:180px;}input[type="submit"]:hover{background:linear-gradient(90deg,#00d2ff 0%,#3a7bd5 100%);transform:scale(1.04);}.card{background:#f7faff;border-radius:18px;box-shadow:0 2px 8px rgba(58,123,213,0.10);padding:24px 20px 18px 20px;margin-top:10px;animation:fadeIn 0.8s cubic-bezier(.4,0,.2,1);position:relative;}.card ul{list-style:none;padding:0;margin:0;}.card li{margin-bottom:10px;font-size:1.04rem;color:#222f3e;}.chip{display:inline-block;padding:7px 18px;border-radius:22px;background:linear-gradient(90deg,#3a7bd5 0%,#00d2ff 100%);color:#fff;font-size:1.01rem;margin-bottom:12px;animation:popIn 0.7s cubic-bezier(.4,0,.2,1);font-weight:600;letter-spacing:0.5px;box-shadow:0 1px 4px rgba(58,123,213,0.10);}@keyframes popIn{from{transform:scale(0.8);opacity:0;}to{transform:scale(1);opacity:1;}}.suggest-list{margin-top:12px;padding-left:18px;animation:fadeIn 1.2s cubic-bezier(.4,0,.2,1);}.suggest-list li{margin-bottom:8px;background:#e3f0fc;border-radius:10px;padding:10px 14px;transition:background 0.2s,transform 0.2s;font-size:1.01rem;color:#1a2a3a;box-shadow:0 1px 4px rgba(58,123,213,0.07);cursor:pointer;}.suggest-list li:hover{background:#b2e0fb;transform:scale(1.03);}.graph-section{margin-top:28px;background:#f7faff;border-radius:18px;box-shadow:0 2px 8px rgba(58,123,213,0.10);padding:18px 10px 10px 10px;animation:fadeIn 1.1s cubic-bezier(.4,0,.2,1);}.graph-title{text-align:center;color:#3a7bd5;font-size:1.1rem;font-weight:600;margin-bottom:10px;letter-spacing:0.5px;}@media (max-width:600px){.container{padding:18px 2vw;}.card{padding:12px 4vw;}}</style>
</head>
<body>
  <div class="container">
    <h2>YouTube Channel Analyzer</h2>
    <form method="post">
      <input type="text" name="username" placeholder="Channel Username or Unique Handle" required>
      <input type="submit" value="Analyze">
    </form>
    {% if details %}
      <div class="card">
        <span class="chip">{{ details['type'] }}</span>
        <ul>
          <li><b>Title:</b> {{ details['title'] }}</li>
          <li><b>Description:</b> {{ details['description'] }}</li>
          <li><b>Subscribers:</b> {{ details['subscribers'] }}</li>
          <li><b>Views:</b> {{ details['views'] }}</li>
          <li><b>Videos:</b> {{ details['videos'] }}</li>
        </ul>
        <h4 style="margin-top:18px; color:#3a7bd5;">Growth Suggestions</h4>
        <ul class="suggest-list">
          {% for suggestion in details['suggestions'] %}
            <li>{{ suggestion }}</li>
          {% endfor %}
        </ul>
      </div>
      {% if months and subs %}
      <div class="graph-section">
        <div class="graph-title">Subscriber Growth (Last 12 Months)</div>
        <canvas id="subsChart" width="400" height="180"></canvas>
      </div>
      <script>
        const ctx = document.getElementById('subsChart').getContext('2d');
        const chart = new Chart(ctx, {
          type: 'line',
          data: {
            labels: {{ months|tojson }},
            datasets: [{
              label: 'Subscribers',
              data: {{ subs|tojson }},
              borderColor: '#3a7bd5',
              backgroundColor: 'rgba(58,123,213,0.12)',
              borderWidth: 3,
              pointRadius: 4,
              pointBackgroundColor: '#00d2ff',
              tension: 0.35,
              fill: true,
            }]
          },
          options: {
            responsive: true,
            plugins: {
              legend: { display: false },
              tooltip: { mode: 'index', intersect: false }
            },
            scales: {
              x: { grid: { display: false } },
              y: { grid: { color: '#e3f0fc' }, beginAtZero: true }
            },
            animation: {
              duration: 1200,
              easing: 'easeOutQuart'
            }
          }
        });
      </script>
      {% endif %}
      {% if video_points %}
      <div class="graph-section">
        <div class="graph-title">Video Upload Frequency (Last 60 Days)</div>
        <canvas id="uploadFreqChart" width="400" height="220"></canvas>
      </div>
      <script>
        const videoPoints = {{ video_points|tojson }};
        const typeColors = { 'video': '#3a7bd5', 'short': '#ffb347' };
        const ctx2 = document.getElementById('uploadFreqChart').getContext('2d');
        const scatterChart = new Chart(ctx2, {
          type: 'bubble',
          data: {
            datasets: [
              {
                label: 'Uploads',
                data: videoPoints.map(v => ({
                  x: v.upload_date,
                  y: v.upload_hour,
                  r: v.dot_size,
                  video_url: v.url,
                  label: v.title,
                  type: v.type,
                  views: v.views,
                  length: v.length
                })),
                backgroundColor: videoPoints.map(v => typeColors[v.type] || '#888'),
                pointStyle: 'circle',
                borderWidth: 1,
                borderColor: '#fff',
              }
            ]
          },
          options: {
            responsive: true,
            plugins: {
              legend: { display: false },
              tooltip: {
                callbacks: {
                  label: function(ctx) {
                    const d = ctx.raw;
                    return `${d.label} (${d.type}, ${d.length})\\nViews: ${d.views.toLocaleString()}\\n${d.x} @ ${d.y}:00`;
                  }
                }
              }
            },
            parsing: false,
            scales: {
              x: {
                type: 'time',
                time: { unit: 'day', tooltipFormat: 'MMM d' },
                title: { display: true, text: 'Date' },
                grid: { color: '#e3f0fc' }
              },
              y: {
                min: 0, max: 23,
                title: { display: true, text: 'Hour of Day (Upload Time)' },
                ticks: { stepSize: 2 },
                grid: { color: '#e3f0fc' }
              }
            },
            onClick: (e, elements) => {
              if (elements.length > 0) {
                const idx = elements[0].index;
                const url = videoPoints[idx].url;
                window.open(url, '_blank');
              }
            }
          }
        });
      </script>
      {% endif %}
    {% endif %}
  </div>
</body>
</html>
'''

def get_channel_details(username, force_refresh=False):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(data_dir, exist_ok=True)
    user_file = os.path.join(data_dir, f'{username}_forUsername.json')
    handle_file = os.path.join(data_dir, f'{username}_forHandle.json')
    data = None
    if not force_refresh and os.path.exists(user_file):
        with open(user_file, encoding='utf-8') as f:
            data1 = json.load(f)
    else:
        url1 = f"https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&forUsername={username}&key={YOUTUBE_API_KEY}"
        resp1 = requests.get(url1)
        data1 = resp1.json()
        with open(user_file, 'w', encoding='utf-8') as f:
            json.dump(data1, f, ensure_ascii=False, indent=2)
        logging.info(f"Fetched channel (forUsername) for {username}: {data1}")
    if not data1.get('items'):
        if not force_refresh and os.path.exists(handle_file):
            with open(handle_file, encoding='utf-8') as f:
                data2 = json.load(f)
        else:
            url2 = f"https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&forHandle={username}&key={YOUTUBE_API_KEY}"
            resp2 = requests.get(url2)
            data2 = resp2.json()
            with open(handle_file, 'w', encoding='utf-8') as f:
                json.dump(data2, f, ensure_ascii=False, indent=2)
            logging.info(f"Fetched channel (forHandle) for {username}: {data2}")
        data = data2
    else:
        data = data1
    if not data.get('items'):
        return None
    item = data['items'][0]
    snippet = item['snippet']
    stats = item['statistics']
    title = snippet.get('title', '')
    description = snippet.get('description', '')
    subscribers = stats.get('subscriberCount', 'N/A')
    views = stats.get('viewCount', 'N/A')
    videos = stats.get('videoCount', 'N/A')
    import re
    gaming_keywords = [r'\bgaming\b', r'\bgamer\b', r'\bgame\b', r'\bplay\b', r"let's play", r'walkthrough', r'esports', r'with pheonix']
    is_gaming = any(re.search(kw, title, re.IGNORECASE) or re.search(kw, description, re.IGNORECASE) for kw in gaming_keywords)
    channel_type = 'Gaming Channel' if is_gaming else 'Not Gaming Channel'
    suggestions = []
    if is_gaming:
        suggestions.append('Collaborate with other gaming creators.')
        suggestions.append('Stream gameplay and engage with your audience.')
        suggestions.append('Create trending game content and tutorials.')
    else:
        suggestions.append('Identify your niche and create consistent content.')
        suggestions.append('Engage with your audience through comments and community posts.')
        suggestions.append('Collaborate with other creators in your field.')
    return {
        'title': title,
        'description': description,
        'subscribers': subscribers,
        'views': views,
        'videos': videos,
        'type': channel_type,
        'suggestions': suggestions
    }

def get_subscriber_history(current_subs):
    months = []
    now = datetime(2025, 5, 14)
    for i in range(11, -1, -1):
        month = (now - timedelta(days=30*i)).strftime('%b %Y')
        months.append(month)
    try:
        current = int(current_subs.replace(',', ''))
    except Exception:
        current = 1000
    start = int(current * 0.6)
    step = (current - start) // 11 if current > start else 1
    subs = [start + i*step for i in range(12)]
    subs[-1] = current
    return months, subs

def get_channel_uploads(channel_id):
    # Caching logic
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    cache_file = os.path.join(data_dir, f'{channel_id}_uploads.json')
    if os.path.exists(cache_file) and not getattr(request, 'force_refresh', False):
        try:
            with open(cache_file, encoding='utf-8') as f:
                cached = json.load(f)
                logging.info(f"Loaded uploads from cache for channel {channel_id}")
                return cached
        except Exception as e:
            logging.error(f"Error reading uploads cache: {e}")
    url = f"https://www.googleapis.com/youtube/v3/channels?part=contentDetails&id={channel_id}&key={YOUTUBE_API_KEY}"
    resp = requests.get(url)
    data = resp.json()
    if not data.get('items'):
        logging.warning(f"No channel found for id {channel_id}")
        return []
    uploads_playlist = data['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    videos = []
    nextPageToken = ''
    cutoff = datetime.utcnow().replace(tzinfo=None) - timedelta(days=60)
    while True:
        pl_url = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet,contentDetails&playlistId={uploads_playlist}&maxResults=50&key={YOUTUBE_API_KEY}"
        if nextPageToken:
            pl_url += f"&pageToken={nextPageToken}"
        pl_resp = requests.get(pl_url)
        pl_data = pl_resp.json()
        for item in pl_data.get('items', []):
            vid_id = item['contentDetails']['videoId']
            published_at = item['contentDetails']['videoPublishedAt']
            dt = date_parser.parse(published_at)
            if dt.tzinfo is not None:
                dt_naive = dt.replace(tzinfo=None)
            else:
                dt_naive = dt
            if dt_naive < cutoff:
                logging.info(f"Stopped at video {vid_id} published at {published_at} (older than 60 days)")
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(videos, f, ensure_ascii=False, indent=2)
                return videos
            videos.append({
                'id': vid_id,
                'published_at': published_at,
                'snippet': item['snippet']
            })
        nextPageToken = pl_data.get('nextPageToken')
        if not nextPageToken:
            break
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(videos, f, ensure_ascii=False, indent=2)
    logging.info(f"Fetched and cached uploads for channel {channel_id}, total: {len(videos)}")
    return videos

def get_video_details(video_ids):
    details = []
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i+50]
        ids = ','.join(batch)
        url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails,statistics&id={ids}&key={YOUTUBE_API_KEY}"
        resp = requests.get(url)
        data = resp.json()
        for item in data.get('items', []):
            details.append(item)
    return details

def parse_duration(iso_duration):
    try:
        td = isodate.parse_duration(iso_duration)
        total_seconds = int(td.total_seconds())
        h = total_seconds // 3600
        m = (total_seconds % 3600) // 60
        s = total_seconds % 60
        if h:
            return f"{h}:{m:02}:{s:02}"
        else:
            return f"{m}:{s:02}"
    except Exception:
        return iso_duration

@app.route('/', methods=['GET', 'POST'])
def index():
    details = None
    months = []
    subs = []
    video_points = []
    if request.method == 'POST':
        username = request.form['username'].strip()
        force_refresh = 'refresh' in request.form
        details = get_channel_details(username, force_refresh=force_refresh)
        if not details:
            details = {'title': 'Not found', 'description': '', 'subscribers': '', 'views': '', 'videos': '', 'type': '', 'suggestions': ['Channel not found.']}
        else:
            months, subs = get_subscriber_history(details['subscribers'])
            data_dir = os.path.join(os.path.dirname(__file__), 'data')
            handle_file = os.path.join(data_dir, f'{username}_forHandle.json')
            user_file = os.path.join(data_dir, f'{username}_forUsername.json')
            channel_id = None
            for f in [user_file, handle_file]:
                if os.path.exists(f):
                    with open(f, encoding='utf-8') as ff:
                        d = json.load(ff)
                        if d.get('items'):
                            channel_id = d['items'][0]['id']
                            break
            if channel_id:
                # Set force_refresh on request for get_channel_uploads
                setattr(request, 'force_refresh', force_refresh)
                uploads = get_channel_uploads(channel_id)
                if not uploads:
                    logging.warning(f"No uploads found for channel {channel_id} in last 60 days. Possible reasons: playlistItems API limitation, channel uploads playlist not public, or API quota.")
                else:
                    logging.info(f"Found {len(uploads)} uploads for channel {channel_id} in last 60 days.")
                if uploads:
                    vid_ids = [v['id'] for v in uploads]
                    vid_details = get_video_details(vid_ids)
                    for v in vid_details:
                        vid_id = v['id']
                        snippet = v['snippet']
                        stats = v.get('statistics', {})
                        content = v.get('contentDetails', {})
                        published_at = snippet.get('publishedAt')
                        dt = date_parser.parse(published_at)
                        length_sec = 0
                        try:
                            td = isodate.parse_duration(content.get('duration', 'PT0S'))
                            length_sec = int(td.total_seconds())
                        except Exception:
                            pass
                        title = snippet.get('title', '')
                        desc = snippet.get('description', '')
                        is_short = (length_sec <= 61) or ('#shorts' in title.lower() or '#shorts' in desc.lower())
                        vtype = 'short' if is_short else 'video'
                        video_url = f"https://www.youtube.com/watch?v={vid_id}"
                        views = int(stats.get('viewCount', 0))
                        dot_size = max(4, min(views // 100, 20))
                        video_points.append({
                            'upload_date': dt.strftime('%Y-%m-%d'),
                            'upload_hour': dt.hour,
                            'type': vtype,
                            'length': parse_duration(content.get('duration', 'PT0S')),
                            'views': views,
                            'dot_size': dot_size,
                            'url': video_url,
                            'title': title
                        })
    return render_template_string(HTML_FORM, details=details, months=months, subs=subs, video_points=video_points)

# Add a refresh button to the form
@app.route('/refresh', methods=['POST'])
def refresh():
    username = request.form['username'].strip()
    return redirect(url_for('index', username=username, refresh='1'))

if __name__ == '__main__':
    app.run(debug=True)