import json
import re
from datetime import datetime
import requests

M3U_URL = "https://raw.githubusercontent.com/srhady/join_telegram_chennal-livesportsplay/refs/heads/main/latest_movies.m3u"
OLD_JSON_URL = "https://raw.githubusercontent.com/raselmia9/SNTT-ALL-DATA/refs/heads/main/Popular%20movie.json"
OUTPUT_FILE = "Popular movie.json"

def fetch_m3u():
    try:
        res = requests.get(M3U_URL)
        return res.text
    except Exception as e:
        print(f"Error fetching M3U: {e}")
        return ""

def fetch_old_json():
    try:
        res = requests.get(OLD_JSON_URL)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print(f"Error fetching Old JSON: {e}")
    return []

def extract_info(extinf_line):
    logo_match = re.search(r'tvg-logo="(.*?)"', extinf_line)
    if not logo_match:
        logo_match = re.search(r'https?://[^\s"]+\.(?:jpg|jpeg|png|webp)', extinf_line, re.IGNORECASE)
        logo_url = logo_match.group(0) if logo_match else "https://via.placeholder.com/300"
    else:
        logo_url = logo_match.group(1)

    if not logo_url or logo_url.strip() == "":
        logo_url = "https://via.placeholder.com/300"

    parts = extinf_line.split(',')
    title = parts[-1].strip() if len(parts) > 1 else "Unknown"
    
    return title, logo_url

def convert_m3u_to_json():
    # ১. পুরোনো জেসন ডেটাগুলো হুবহু নিয়ে আসা
    old_movies_list = fetch_old_json()
    if not isinstance(old_movies_list, list):
        old_movies_list = []

    # ২. নতুন M3U ডেটা ফেচ করা
    content = fetch_m3u()
    new_movies_list = []
    
    if content:
        lines = content.strip().split('\n')
        current_time = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")

        current_title = ""
        current_logo = "https://via.placeholder.com/300"

        for line in lines:
            line = line.strip()
            if line.startswith('#EXTINF:'):
                current_title, current_logo = extract_info(line)
            elif line and not line.startswith('#'):
                link = line
                if not current_title:
                    continue

                movie_item = {
                    "title": current_title,
                    "details": "Director : N/A\nCast(s) : N/A\nLanguage : Default\nQuality : WEB-DL\nResolution : HD",
                    "img": current_logo,
                    "date": current_time,
                    "link": link
                }
                new_movies_list.append(movie_item)

                current_title = ""
                current_logo = "https://via.placeholder.com/300"

    # ৩. পুরোনো ডেটাগুলোকে নতুন ডেটার ঠিক উপরে বা শুরুতে বসিয়ে দেওয়া
    final_movies_list = old_movies_list + new_movies_list

    # ৪. ফাইনাল ফাইল সেভ করা
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_movies_list, f, ensure_ascii=False, indent=4)
    
    print(f"Successfully merged! Old items: {len(old_movies_list)}, New items: {len(new_movies_list)}, Total: {len(final_movies_list)}")

if __name__ == "__main__":
    convert_m3u_to_json()
