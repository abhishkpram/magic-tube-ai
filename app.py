
import json
import requests
import os
import logging
from flask import Flask, request, render_template_string, redirect, url_for
from datetime import datetime, timedelta
from dateutil import parser as date_parser
import isodate



with open('config.json') as f:
    config = json.load(f)
YOUTUBE_API_KEY = config['YOUTUBE_API_KEY']


app = Flask(__name__)

SIMPLE_TEMPLATE = '''
<html><head><title>YouTube Channel Analyzer</title></head><body>
<h2>YouTube Channel Analyzer</h2>
<form method="post">
  <input name="username" placeholder="Channel Username or Handle" required value="{{ username or '' }}">
  <input name="compare_username" placeholder="Compare with (optional)" value="{{ compare_username or '' }}">
  <input type="submit" value="Analyze">
</form>
{% if details %}
<h3>{{ details['title'] }}</h3>
<div><b>Description:</b> {{ details['description'] }}</div>
<div><b>Subscribers:</b> {{ details['subscribers'] }}</div>
<div><b>Views:</b> {{ details['views'] }}</div>
<div><b>Videos:</b> {{ details['videos'] }}</div>
<div><b>Channel Type:</b> {{ details['type'] }}</div>
<div><b>Replies to Comments (last 5 videos):</b> {{ details['reply_count'] }}</div>
<div><b>Total Comments Analyzed:</b> {{ details['total_comments'] }}</div>
<div><b>Avg. Reply Time (hrs):</b> {{ details['avg_reply_time_hours']|round(2) if details['avg_reply_time_hours'] is not none else '?' }}</div>
<div><b>Channel Age:</b> {{ details['channel_age_years'] or '?' }} years {{ details['channel_age_months'] or '' }} months</div>
<div><b>Avg. Views/Video:</b> {{ details['avg_views_per_video']|round(2) if details['avg_views_per_video'] is not none else '?' }}</div>
<div><b>Avg. Subs/Video:</b> {{ details['avg_subs_per_video']|round(2) if details['avg_subs_per_video'] is not none else '?' }}</div>
<div><b>Upload Freq/Month:</b> {{ details['upload_freq_per_month']|round(2) if details['upload_freq_per_month'] is not none else '?' }}</div>
<div><b>Subs/Year:</b> {{ details['subs_per_year']|round(2) if details['subs_per_year'] is not none else '?' }}</div>
<div><b>Views/Year:</b> {{ details['views_per_year']|round(2) if details['views_per_year'] is not none else '?' }}</div>
<div><b>All Comments (last 5 videos, up to 20 each):</b></div>
<ul>
{% for c in details.get('all_comments', []) %}
<li><b>{{ c['author'] }}</b>: {{ c['text'] }}</li>
{% endfor %}
</ul>
{% endif %}
{% if compare_details %}
<h4>Comparison with {{ compare_details['title'] }}</h4>
<div>Subscribers: {{ details['subscribers'] }} vs {{ compare_details['subscribers'] }}</div>
<div>Views: {{ details['views'] }} vs {{ compare_details['views'] }}</div>
<div>Videos: {{ details['videos'] }} vs {{ compare_details['videos'] }}</div>
<div>Replies to Comments: {{ details['reply_count'] }} vs {{ compare_details['reply_count'] }}</div>
<div>Total Comments: {{ details['total_comments'] }} vs {{ compare_details['total_comments'] }}</div>
<div>Avg. Reply Time (hrs): {{ details['avg_reply_time_hours']|round(2) if details['avg_reply_time_hours'] is not none else '?' }} vs {{ compare_details['avg_reply_time_hours']|round(2) if compare_details['avg_reply_time_hours'] is not none else '?' }}</div>
{% endif %}
</body></html>
'''

# Replace all render_template_string calls to use TEMPLATE

HTML_FORM = '''
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>YouTube Channel Analyzer</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns"></script>
  <style>body{background:linear-gradient(120deg,#a1c4fd 0%,#c2e9fb 100%);font-family:'Roboto',sans-serif;min-height:100vh;margin:0;display:flex;align-items:center;justify-content:center;overflow-x:hidden;}.container{background:#fff;border-radius:24px;box-shadow:0 8px 32px 0 rgba(31,38,135,0.2);padding:48px 0 36px 0;width:100vw;max-width:none;animation:fadeIn 1s cubic-bezier(.4,0,.2,1);}@keyframes fadeIn{from{opacity:0;transform:translateY(40px) scale(0.98);}to{opacity:1;transform:translateY(0) scale(1);}}h2{text-align:center;color:#3a7bd5;margin-bottom:28px;letter-spacing:1px;font-size:2.1rem;font-weight:700;}form{display:flex;flex-direction:column;gap:18px;margin-bottom:24px;align-items:center;}input[type="text"],input[name="username"]{padding:12px 18px;border-radius:12px;border:1.5px solid #b2bec3;font-size:1.08rem;outline:none;transition:border 0.2s;width:100%;max-width:320px;background:#f7faff;}input[type="text"]:focus,input[name="username"]:focus{border:2px solid #3a7bd5;background:#e3f0fc;}input[type="submit"]{background:linear-gradient(90deg,#3a7bd5 0%,#00d2ff 100%);color:#fff;border:none;border-radius:12px;padding:12px 0;font-size:1.08rem;font-weight:bold;cursor:pointer;transition:background 0.2s,transform 0.2s;box-shadow:0 2px 8px rgba(58,123,213,0.13);width:100%;max-width:180px;}input[type="submit"]:hover{background:linear-gradient(90deg,#00d2ff 0%,#3a7bd5 100%);transform:scale(1.04);}.card{background:#f7faff;border-radius:18px;box-shadow:0 2px 8px rgba(58,123,213,0.10);padding:24px 20px 18px 20px;margin-top:10px;animation:fadeIn 0.8s cubic-bezier(.4,0,.2,1);position:relative;}.card ul{list-style:none;padding:0;margin:0;}.card li{margin-bottom:10px;font-size:1.04rem;color:#222f3e;}.chip{display:inline-block;padding:7px 18px;border-radius:22px;background:linear-gradient(90deg,#3a7bd5 0%,#00d2ff 100%);color:#fff;font-size:1.01rem;margin-bottom:12px;animation:popIn 0.7s cubic-bezier(.4,0,.2,1);font-weight:600;letter-spacing:0.5px;box-shadow:0 1px 4px rgba(58,123,213,0.10);}@keyframes popIn{from{transform:scale(0.8);opacity:0;}to{transform:scale(1);opacity:1;}}.suggest-list{margin-top:12px;padding-left:18px;animation:fadeIn 1.2s cubic-bezier(.4,0,.2,1);}.suggest-list li{margin-bottom:8px;background:#e3f0fc;border-radius:10px;padding:10px 14px;transition:background 0.2s,transform 0.2s;font-size:1.01rem;color:#1a2a3a;box-shadow:0 1px 4px rgba(58,123,213,0.07);cursor:pointer;}.suggest-list li:hover{background:#b2e0fb;transform:scale(1.03);}.graph-section{margin-top:28px;background:#f7faff;border-radius:18px;box-shadow:0 2px 8px rgba(58,123,213,0.10);padding:18px 10px 10px 10px;animation:fadeIn 1.1s cubic-bezier(.4,0,.2,1);}.graph-title{text-align:center;color:#3a7bd5;font-size:1.1rem;font-weight:600;margin-bottom:10px;letter-spacing:0.5px;}@media (max-width:600px){.container{padding:18px 0;}.card{padding:12px 4vw;}}</style>
</head>
<body>
  <div class="container">
    <h2>YouTube Channel Analyzer</h2>
    <form method="post">
      <input type="text" name="username" placeholder="Channel Username or Unique Handle" required value="{{ username or '' }}">
      <input type="text" name="compare_username" placeholder="Compare with (optional)" value="{{ compare_username or '' }}">
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
          <li><b>Channel Age:</b> {{ details['channel_age_years'] or '?' }} years {{ details['channel_age_months'] or '' }} months</li>
          <li><b>Avg. Views/Video:</b> {{ details['avg_views_per_video']|round(2) if details['avg_views_per_video'] is not none else '?' }}</li>
          <li><b>Avg. Subs/Video:</b> {{ details['avg_subs_per_video']|round(2) if details['avg_subs_per_video'] is not none else '?' }}</li>
          <li><b>Upload Freq/Month:</b> {{ details['upload_freq_per_month']|round(2) if details['upload_freq_per_month'] is not none else '?' }}</li>
          <li><b>Subs/Year:</b> {{ details['subs_per_year']|round(2) if details['subs_per_year'] is not none else '?' }}</li>
          <li><b>Views/Year:</b> {{ details['views_per_year']|round(2) if details['views_per_year'] is not none else '?' }}</li>
          <li><b>Replies to Comments (last 5 videos):</b> {{ details['reply_count'] }}</li>
          <li><b>Total Comments Analyzed:</b> {{ details['total_comments'] }}</li>
          <li><b>Avg. Reply Time (hrs):</b> {{ details['avg_reply_time_hours']|round(2) if details['avg_reply_time_hours'] is not none else '?' }}</li>
        </ul>
        <h4 style="margin-top:18px; color:#3a7bd5;">Growth Suggestions</h4>
        <ul class="suggest-list">
          {% for suggestion in details['suggestions'] %}
            <li>{{ suggestion }}</li>
          {% endfor %}
        </ul>
      </div>
      {% if compare_details %}
      <div class="card" style="margin-top:18px; background:#e3f0fc;">
        <span class="chip">Comparison with {{ compare_details['title'] }}</span>
        <ul>
          <li><b>Subscribers:</b> {{ details['subscribers'] }} vs {{ compare_details['subscribers'] }}</li>
          <li><b>Views:</b> {{ details['views'] }} vs {{ compare_details['views'] }}</li>
          <li><b>Videos:</b> {{ details['videos'] }} vs {{ compare_details['videos'] }}</li>
          <li><b>Channel Age:</b> {{ details['channel_age_years'] or '?' }}y vs {{ compare_details['channel_age_years'] or '?' }}y</li>
          <li><b>Avg. Views/Video:</b> {{ details['avg_views_per_video']|round(2) if details['avg_views_per_video'] is not none else '?' }} vs {{ compare_details['avg_views_per_video']|round(2) if compare_details['avg_views_per_video'] is not none else '?' }}</li>
          <li><b>Avg. Subs/Video:</b> {{ details['avg_subs_per_video']|round(2) if details['avg_subs_per_video'] is not none else '?' }} vs {{ compare_details['avg_subs_per_video']|round(2) if compare_details['avg_subs_per_video'] is not none else '?' }}</li>
          <li><b>Upload Freq/Month:</b> {{ details['upload_freq_per_month']|round(2) if details['upload_freq_per_month'] is not none else '?' }} vs {{ compare_details['upload_freq_per_month']|round(2) if compare_details['upload_freq_per_month'] is not none else '?' }}</li>
          <li><b>Subs/Year:</b> {{ details['subs_per_year']|round(2) if details['subs_per_year'] is not none else '?' }} vs {{ compare_details['subs_per_year']|round(2) if compare_details['subs_per_year'] is not none else '?' }}</li>
          <li><b>Views/Year:</b> {{ details['views_per_year']|round(2) if details['views_per_year'] is not none else '?' }} vs {{ compare_details['views_per_year']|round(2) if compare_details['views_per_year'] is not none else '?' }}</li>
          <li><b>Replies to Comments (last 5 videos):</b> {{ details['reply_count'] }} vs {{ compare_details['reply_count'] }}</li>
          <li><b>Total Comments Analyzed:</b> {{ details['total_comments'] }} vs {{ compare_details['total_comments'] }}</li>
          <li><b>Avg. Reply Time (hrs):</b> {{ details['avg_reply_time_hours']|round(2) if details['avg_reply_time_hours'] is not none else '?' }} vs {{ compare_details['avg_reply_time_hours']|round(2) if compare_details['avg_reply_time_hours'] is not none else '?' }}</li>
        </ul>
        <h4 style="margin-top:18px; color:#3a7bd5;">Improvement Opportunities</h4>
        <ul class="suggest-list">
          {% for suggestion in improvement_opportunities %}
            <li>{{ suggestion }}</li>
          {% endfor %}
        </ul>
      </div>
      {% endif %}
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
    # Fetch channel info first
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
    channel_id = item['id']
    # Fetch uploads for comment analysis
    uploads = get_channel_uploads(channel_id)
    video_ids = [v['id'] for v in uploads]
    comment_stats = get_comment_reply_stats(channel_id, video_ids, username)
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
    # --- DERIVED METRICS ---
    published_at = snippet.get('publishedAt', '')
    channel_age_years = channel_age_months = None
    if published_at:
        try:
            dt = date_parser.parse(published_at)
            from datetime import timezone
            now = datetime.now(timezone.utc)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            delta = now - dt
            channel_age_years = delta.days // 365
            channel_age_months = (delta.days % 365) // 30
        except Exception:
            pass
    try:
        avg_views_per_video = int(views.replace(',', '')) / max(1, int(videos.replace(',', '')))
    except Exception:
        avg_views_per_video = None
    try:
        avg_subs_per_video = int(subscribers.replace(',', '')) / max(1, int(videos.replace(',', '')))
    except Exception:
        avg_subs_per_video = None
    try:
        total_months = (channel_age_years or 0) * 12 + (channel_age_months or 0)
        upload_freq_per_month = int(videos.replace(',', '')) / max(1, total_months)
    except Exception:
        upload_freq_per_month = None
    try:
        subs_per_year = int(subscribers.replace(',', '')) / max(1, (channel_age_years or 1))
    except Exception:
        subs_per_year = None
    try:
        views_per_year = int(views.replace(',', '')) / max(1, (channel_age_years or 1))
    except Exception:
        views_per_year = None
    return {
        'title': title,
        'description': description,
        'subscribers': subscribers,
        'views': views,
        'videos': videos,
        'type': channel_type,
        'suggestions': suggestions,
        'published_at': published_at,
        'channel_age_years': channel_age_years,
        'channel_age_months': channel_age_months,
        'avg_views_per_video': avg_views_per_video,
        'avg_subs_per_video': avg_subs_per_video,
        'upload_freq_per_month': upload_freq_per_month,
        'subs_per_year': subs_per_year,
        'views_per_year': views_per_year,
        'reply_count': comment_stats['reply_count'],
        'total_comments': comment_stats['total_comments'],
        'avg_reply_time_hours': comment_stats['avg_reply_time_hours']
    }

def compare_channels(details1, details2):
    """
    Compare two channel details dicts and return a list of improvement opportunities for channel 1.
    """
    suggestions = []
    try:
        subs1 = int(str(details1['subscribers']).replace(',', ''))
        subs2 = int(str(details2['subscribers']).replace(',', ''))
        views1 = int(str(details1['views']).replace(',', ''))
        views2 = int(str(details2['views']).replace(',', ''))
        vids1 = int(str(details1['videos']).replace(',', ''))
        vids2 = int(str(details2['videos']).replace(',', ''))
    except Exception:
        return ["Unable to compare stats due to missing data."]
    if subs2 > subs1:
        suggestions.append(f"Your competitor has more subscribers ({subs2:,}). Consider increasing your upload frequency, collaborating, or improving content quality.")
    else:
        suggestions.append("You have more subscribers. Keep up the good work and continue innovating!")
    if views2 > views1:
        suggestions.append(f"Your competitor has more total views ({views2:,}). Try optimizing your video SEO and promoting your channel.")
    if vids2 > vids1:
        suggestions.append(f"Your competitor has uploaded more videos ({vids2:,}). Consider increasing your content output if quality can be maintained.")
    if details1['type'] != details2['type']:
        suggestions.append(f"Channel types differ: yours is '{details1['type']}', competitor is '{details2['type']}'. Consider if their approach is more effective for your audience.")
    return suggestions



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

def get_comment_reply_stats(channel_id, video_ids, username, max_videos=5, max_comments=20):
    """
    For a list of video IDs, fetch comments and replies, and calculate:
    - Number of replies made by the channel owner
    - Average reply time (in hours)
    Saves all API responses in the data folder.
    """
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    reply_count = 0
    reply_times = []
    total_comments = 0
    all_comments = []
    for vid in video_ids[:max_videos]:
        # Fetch top-level comments (commentThreads)
        thread_url = f"https://www.googleapis.com/youtube/v3/commentThreads?part=snippet,replies&videoId={vid}&maxResults={max_comments}&key={YOUTUBE_API_KEY}"
        thread_resp = requests.get(thread_url)
        thread_data = thread_resp.json()
        with open(os.path.join(data_dir, f'{username}_{vid}_commentThreads.json'), 'w', encoding='utf-8') as f:
            json.dump(thread_data, f, ensure_ascii=False, indent=2)
        for item in thread_data.get('items', []):
            top_comment = item['snippet']['topLevelComment']['snippet']
            comment_id = item['snippet']['topLevelComment']['id']
            comment_author = top_comment.get('authorChannelId', {}).get('value', '')
            comment_time = top_comment.get('publishedAt')
            total_comments += 1
            all_comments.append({'id': comment_id, 'text': top_comment.get('textDisplay', ''), 'author': comment_author, 'time': comment_time})
            # Fetch all replies to this comment using comments endpoint
            replies_url = f"https://www.googleapis.com/youtube/v3/comments?part=snippet&parentId={comment_id}&maxResults=100&key={YOUTUBE_API_KEY}"
            replies_resp = requests.get(replies_url)
            replies_data = replies_resp.json()
            with open(os.path.join(data_dir, f'{username}_{vid}_{comment_id}_replies.json'), 'w', encoding='utf-8') as f:
                json.dump(replies_data, f, ensure_ascii=False, indent=2)
            for reply in replies_data.get('items', []):
                reply_snippet = reply['snippet']
                reply_author = reply_snippet.get('authorChannelId', {}).get('value', '')
                reply_time = reply_snippet.get('publishedAt')
                if reply_author == channel_id:
                    reply_count += 1
                    try:
                        t1 = date_parser.parse(comment_time)
                        t2 = date_parser.parse(reply_time)
                        delta = (t2 - t1).total_seconds() / 3600.0
                        if delta >= 0:
                            reply_times.append(delta)
                    except Exception:
                        pass
    avg_reply_time = sum(reply_times) / len(reply_times) if reply_times else None
    return {
        'reply_count': reply_count,
        'total_comments': total_comments,
        'avg_reply_time_hours': avg_reply_time,
        'all_comments': all_comments
    }
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
    compare_details = None
    improvement_opportunities = []
    months = []
    subs = []
    video_points = []
    username = ''
    compare_username = ''
    if request.method == 'POST':
        username = request.form['username'].strip()
        compare_username = request.form.get('compare_username', '').strip()
        force_refresh = 'refresh' in request.form
        details = get_channel_details(username, force_refresh=force_refresh)
        if not details:
            details = {'title': 'Not found', 'description': '', 'subscribers': '', 'views': '', 'videos': '', 'type': '', 'suggestions': ['Channel not found.']}
        # If compare_username is provided, fetch and compare
        if compare_username:
            compare_details = get_channel_details(compare_username, force_refresh=force_refresh)
            if compare_details:
                improvement_opportunities = compare_channels(details, compare_details)
    return render_template_string(SIMPLE_TEMPLATE, details=details, username=username, compare_username=compare_username, compare_details=compare_details)
    return render_template_string(SIMPLE_TEMPLATE, details=details, username=username, compare_username=compare_username, compare_details=compare_details)

# Add a refresh button to the form
@app.route('/refresh', methods=['POST'])
def refresh():
    username = request.form['username'].strip()
    return redirect(url_for('index', username=username, refresh='1'))

if __name__ == '__main__':
    app.run(debug=True)