import json
import re
from datetime import datetime
import requests

M3U_URL = "https://raw.githubusercontent.com/srhady/join_telegram_chennal-livesportsplay/refs/heads/main/latest_movies.m3u"
OUTPUT_FILE = "Popular movie.json"

def fetch_m3u():
    try:
        res = requests.get(M3U_URL)
        return res.text
    except Exception as e:
        print(f"Error fetching M3U: {e}")
        return ""

def clean_series_title(title):
    cleaned = re.sub(r'(episodes?|ep|season|s\d+e\d+|\d+)', '', title, flags=re.IGNORECASE)
    return cleaned.strip()

def extract_logo_and_title(extinf_line):
    # tvg-logo="..." থেকে লোগো বের করার জন্য আরও ফ্লেক্সিবল রেগুলার এক্সপ্রেশন
    logo_match = re.search(r'tvg-logo=["\'](.*?)["\']', extinf_line, re.IGNORECASE)
    logo_url = logo_match.group(1) if logo_match and logo_match.group(1).strip() else "https://via.placeholder.com/300"
    
    # টাইটেল বের করা (সাধারণত কমার পরের অংশ)
    parts = extinf_line.split(',')
    title = parts[-1].strip() if len(parts) > 1 else "Unknown"
    
    return title, logo_url

def process_m3u_to_json():
    content = fetch_m3u()
    if not content:
        return

    lines = content.strip().split('\n')
    movies_dict = {}
    current_time = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")

    current_title = ""
    current_logo = "https://via.placeholder.com/300"
    
    for line in lines:
        line = line.strip()
        if line.startswith('#EXTINF:'):
            current_title, current_logo = extract_logo_and_title(line)
        elif line and not line.startswith('#'):
            link = line
            if not current_title:
                continue

            base_key = clean_series_title(current_title)
            if not base_key:
                base_key = current_title

            if base_key in movies_dict:
                existing_item = movies_dict[base_key]
                existing_links = existing_item.get("link", "")
                
                if existing_links:
                    existing_item["link"] = f"{current_title},,{link},){existing_links}"
                else:
                    existing_item["link"] = f"{current_title},,{link}"
                
                existing_item["date"] = current_time
                # যদি আগের লোগো না থাকে বা ডিফল্ট থাকে, তবে নতুন লোগো আপডেট করবে
                if current_logo and "placeholder" in existing_item.get("img", ""):
                    existing_item["img"] = current_logo
            else:
                new_entry = {
                    "title": current_title,
                    "details": "Director : N/A\nCast(s) : N/A\nLanguage : Bengali\nQuality : WEB-DL\nResolution : HD",
                    "img": current_logo,  # M3U থেকে পাওয়া আসল থামনেল/লোগো লিংক
                    "date": current_time,
                    "link": f"{current_title},,{link}"
                }
                movies_dict[base_key] = new_entry

            current_title = ""
            current_logo = "https://via.placeholder.com/300"

    movies_list = list(movies_dict.values())
    try:
        movies_list.sort(key=lambda x: datetime.strptime(x.get("date", "01/01/2026 12:00:00 am"), "%m/%d/%Y %I:%M:%S %p"), reverse=True)
    except Exception:
        pass

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(movies_list, f, ensure_ascii=False, indent=4)
    print("Successfully generated Popular movie.json with thumbnails!")

if __name__ == "__main__":
    process_m3u_to_json()
