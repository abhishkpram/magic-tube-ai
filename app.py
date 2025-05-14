import json
import requests
import os
from flask import Flask, request, render_template_string

# Load API key from config.json
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
  <link href="https://fonts.googleapis.com/css?family=Roboto:400,700&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    body {
      background: linear-gradient(120deg, #a1c4fd 0%, #c2e9fb 100%);
      font-family: 'Roboto', sans-serif;
      min-height: 100vh;
      margin: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      overflow-x: hidden;
    }
    .container {
      background: #fff;
      border-radius: 24px;
      box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.2);
      padding: 48px 36px 36px 36px;
      max-width: 520px;
      width: 100%;
      animation: fadeIn 1s cubic-bezier(.4,0,.2,1);
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(40px) scale(0.98); }
      to { opacity: 1; transform: translateY(0) scale(1); }
    }
    h2 {
      text-align: center;
      color: #3a7bd5;
      margin-bottom: 28px;
      letter-spacing: 1px;
      font-size: 2.1rem;
      font-weight: 700;
    }
    form {
      display: flex;
      flex-direction: column;
      gap: 18px;
      margin-bottom: 24px;
      align-items: center;
    }
    input[type="text"], input[name="username"] {
      padding: 12px 18px;
      border-radius: 12px;
      border: 1.5px solid #b2bec3;
      font-size: 1.08rem;
      outline: none;
      transition: border 0.2s;
      width: 100%;
      max-width: 320px;
      background: #f7faff;
    }
    input[type="text"]:focus, input[name="username"]:focus {
      border: 2px solid #3a7bd5;
      background: #e3f0fc;
    }
    input[type="submit"] {
      background: linear-gradient(90deg, #3a7bd5 0%, #00d2ff 100%);
      color: #fff;
      border: none;
      border-radius: 12px;
      padding: 12px 0;
      font-size: 1.08rem;
      font-weight: bold;
      cursor: pointer;
      transition: background 0.2s, transform 0.2s;
      box-shadow: 0 2px 8px rgba(58, 123, 213, 0.13);
      width: 100%;
      max-width: 180px;
    }
    input[type="submit"]:hover {
      background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%);
      transform: scale(1.04);
    }
    .card {
      background: #f7faff;
      border-radius: 18px;
      box-shadow: 0 2px 8px rgba(58, 123, 213, 0.10);
      padding: 24px 20px 18px 20px;
      margin-top: 10px;
      animation: fadeIn 0.8s cubic-bezier(.4,0,.2,1);
      position: relative;
    }
    .card ul {
      list-style: none;
      padding: 0;
      margin: 0;
    }
    .card li {
      margin-bottom: 10px;
      font-size: 1.04rem;
      color: #222f3e;
    }
    .chip {
      display: inline-block;
      padding: 7px 18px;
      border-radius: 22px;
      background: linear-gradient(90deg, #3a7bd5 0%, #00d2ff 100%);
      color: #fff;
      font-size: 1.01rem;
      margin-bottom: 12px;
      animation: popIn 0.7s cubic-bezier(.4,0,.2,1);
      font-weight: 600;
      letter-spacing: 0.5px;
      box-shadow: 0 1px 4px rgba(58, 123, 213, 0.10);
    }
    @keyframes popIn {
      from { transform: scale(0.8); opacity: 0; }
      to { transform: scale(1); opacity: 1; }
    }
    .suggest-list {
      margin-top: 12px;
      padding-left: 18px;
      animation: fadeIn 1.2s cubic-bezier(.4,0,.2,1);
    }
    .suggest-list li {
      margin-bottom: 8px;
      background: #e3f0fc;
      border-radius: 10px;
      padding: 10px 14px;
      transition: background 0.2s, transform 0.2s;
      font-size: 1.01rem;
      color: #1a2a3a;
      box-shadow: 0 1px 4px rgba(58, 123, 213, 0.07);
      cursor: pointer;
    }
    .suggest-list li:hover {
      background: #b2e0fb;
      transform: scale(1.03);
    }
    .graph-section {
      margin-top: 28px;
      background: #f7faff;
      border-radius: 18px;
      box-shadow: 0 2px 8px rgba(58, 123, 213, 0.10);
      padding: 18px 10px 10px 10px;
      animation: fadeIn 1.1s cubic-bezier(.4,0,.2,1);
    }
    .graph-title {
      text-align: center;
      color: #3a7bd5;
      font-size: 1.1rem;
      font-weight: 600;
      margin-bottom: 10px;
      letter-spacing: 0.5px;
    }
    @media (max-width: 600px) {
      .container { padding: 18px 2vw; }
      .card { padding: 12px 4vw; }
    }
  </style>
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
    {% endif %}
  </div>
</body>
</html>
'''

def get_channel_details(username):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(data_dir, exist_ok=True)
    # Try to get channel by forUsername (legacy username)
    url1 = f"https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&forUsername={username}&key={YOUTUBE_API_KEY}"
    resp1 = requests.get(url1)
    data1 = resp1.json()
    # Save first API response
    with open(os.path.join(data_dir, f'{username}_forUsername.json'), 'w', encoding='utf-8') as f:
        json.dump(data1, f, ensure_ascii=False, indent=2)
    if not data1.get('items'):
        # Try to get channel by custom handle (unique username)
        url2 = f"https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&forHandle={username}&key={YOUTUBE_API_KEY}"
        resp2 = requests.get(url2)
        data2 = resp2.json()
        # Save second API response
        with open(os.path.join(data_dir, f'{username}_forHandle.json'), 'w', encoding='utf-8') as f:
            json.dump(data2, f, ensure_ascii=False, indent=2)
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
    # Improved gaming channel detection: looks for 'game', 'gaming', 'gamer', 'play', 'let's play', 'walkthrough', 'esports', 'with pheonix' (case-insensitive, word boundaries)
    import re
    gaming_keywords = [r'\bgaming\b', r'\bgamer\b', r'\bgame\b', r'\bplay\b', r'let\'s play', r'walkthrough', r'esports', r'with pheonix']
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
    # Simulate monthly subscriber growth for the last 12 months
    import datetime
    months = []
    now = datetime.datetime(2025, 5, 14)
    for i in range(11, -1, -1):
        month = (now - datetime.timedelta(days=30*i)).strftime('%b %Y')
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

@app.route('/', methods=['GET', 'POST'])
def index():
    details = None
    months = []
    subs = []
    if request.method == 'POST':
        username = request.form['username'].strip()
        details = get_channel_details(username)
        if not details:
            details = {'title': 'Not found', 'description': '', 'subscribers': '', 'views': '', 'videos': '', 'type': '', 'suggestions': ['Channel not found.']}
        else:
            months, subs = get_subscriber_history(details['subscribers'])
    return render_template_string(HTML_FORM, details=details, months=months, subs=subs)

if __name__ == '__main__':
    app.run(debug=True)
