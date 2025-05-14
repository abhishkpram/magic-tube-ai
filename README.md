
# YouTube Channel Analyzer

## Features
- Enter a YouTube channel username or unique handle to fetch channel details.
- Detects if the channel is a gaming channel using improved keyword logic (keywords: `game`, `gaming`, `gamer`, `play`, `let's play`, `walkthrough`, `esports`, `with pheonix`).
- Displays channel details: title, description, subscribers, views, videos, and channel type.
- Provides growth suggestions based on channel type.
- Shows a simulated animated graph of subscriber growth for the last 12 months.
- All API responses are saved in the `data/` folder for transparency and debugging.
- Modern, animated, and responsive UI.

## How It Works
1. **Channel Lookup:**
   - Tries both `forUsername` and `forHandle` endpoints of the YouTube Data API v3.
   - Saves each API response as a JSON file in the `data/` folder.
2. **Gaming Channel Detection:**
   - Checks for the presence of gaming-related keywords in the channel's title or description (case-insensitive, word boundaries).
   - If any keyword matches, the channel is classified as a Gaming Channel.
   - Otherwise, it is classified as Not Gaming Channel.
3. **Growth Suggestions:**
   - For gaming channels: suggests collaborations, streaming, and trending content.
   - For other channels: suggests niche focus, engagement, and collaborations.
4. **Subscriber Growth Graph:**
   - The YouTube API does not provide historical subscriber data for free.
   - The app simulates subscriber growth: starts at 60% of the current subscriber count 12 months ago and grows linearly to the current value.
   - The graph is rendered using Chart.js and is fully animated.

## How to Run
1. Install requirements:
   ```sh
   pip install flask requests
   ```
2. Run the app:
   ```sh
   python app.py
   ```
3. Open your browser at [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

## Data Storage
- All API responses are saved in the `data/` folder as JSON files, named after the username and the API endpoint used.
- Example: `data/gamingwithpheonix_forUsername.json`, `data/gamingwithpheonix_forHandle.json`

## Limitations
- **Gaming Channel Detection:**
  - Relies on keywords in the title or description. If a gaming channel does not mention any of the keywords, it may not be detected.
  - For more accuracy, consider analyzing video topics or using the YouTube Analytics API (requires OAuth).
- **Subscriber Growth Graph:**
  - The graph is simulated and does not reflect real historical data due to API limitations.

## Last Updated
- May 14, 2025

---

Feel free to improve the detection logic or UI further as needed!
