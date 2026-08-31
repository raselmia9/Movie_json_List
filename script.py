import json
import re
from datetime import datetime
from difflib import SequenceMatcher
import requests

JSON_URL = "https://raw.githubusercontent.com/raselmia9/SNTT-ALL-DATA/refs/heads/main/Popular%20movie.json"
M3U_URL = "https://raw.githubusercontent.com/srhady/join_telegram_chennal-livesportsplay/refs/heads/main/latest_movies.m3u"
OUTPUT_FILE = "Popular movie.json"

def fetch_data():
    try:
        res_json = requests.get(JSON_URL)
        movies = res_json.json()
    except Exception:
        movies = []

    try:
        res_m3u = requests.get(M3U_URL)
        m3u_content = res_m3u.text
    except Exception:
        m3u_content = ""

    return movies, m3u_content

def parse_m3u(content):
    lines = content.strip().split('\n')
    parsed_items = []
    current_title = ""
    for line in lines:
        line = line.strip()
        if line.startswith('#EXTINF:'):
            parts = line.split(',')
            current_title = parts[-1].strip()
        elif line and not line.startswith('#'):
            if current_title:
                parsed_items.append({"title": current_title, "link": line})
                current_title = ""
    return parsed_items

def clean_title(title):
    cleaned = re.sub(r'(episodes?|ep|season|s\d+e\d+|\d+)', '', title, flags=re.IGNORECASE)
    return cleaned.strip().lower()

def update_movies():
    movies, m3u_content = fetch_data()
    m3u_items = parse_m3u(m3u_content)

    current_time = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")

    for m3u_item in m3u_items:
        m3u_title = m3u_item["title"]
        m3u_link = m3u_item["link"]
        
        matched_movie = None
        highest_sim = 0
        
        for movie in movies:
            sim = SequenceMatcher(None, clean_title(m3u_title), clean_title(movie["title"])).ratio()
            if sim > 0.70 and sim > highest_sim:
                highest_sim = sim
                matched_movie = movie

        if matched_movie:
            existing_links = matched_movie.get("link", "")
            if existing_links:
                matched_movie["link"] = f"{m3u_title},,{m3u_link},){existing_links}"
            else:
                matched_movie["link"] = f"{m3u_title},,{m3u_link}"
            matched_movie["date"] = current_time  # লেটেস্ট ডেটা আপডেট করার জন্য সময় দেওয়া
        else:
            new_entry = {
                "title": m3u_title,
                "details": "Director : N/A\nCast(s) : N/A\nLanguage : Bengali\nQuality : WEB-DL\nResolution : HD",
                "img": "https://via.placeholder.com/300",
                "date": current_time,
                "link": f"{m3u_title},,{m3u_link}"
            }
            movies.insert(0, new_entry)  # নতুন আইটেম সবার উপরে যোগ হবে

    # তারিখ অনুযায়ী সাজানো যাতে লেটেস্টগুলো সবসময় উপরে থাকে
    try:
        movies.sort(key=lambda x: datetime.strptime(x.get("date", "01/01/2026 12:00:00 am"), "%m/%d/%Y %I:%M:%S %p"), reverse=True)
    except Exception:
        pass

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(movies, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    update_movies()
      
