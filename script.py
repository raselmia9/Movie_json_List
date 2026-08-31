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
    # এপিসোড বা সিজন নম্বর বাদ দিয়ে মূল নাম বের করা (যেমন: "Bachelor Point S5 Ep 1" থেকে "Bachelor Point")
    cleaned = re.sub(r'(episodes?|ep|season|s\d+e\d+|\d+)', '', title, flags=re.IGNORECASE)
    return cleaned.strip()

def process_m3u_to_json():
    content = fetch_m3u()
    if not content:
        return

    lines = content.strip().split('\n')
    movies_dict = {}
    current_time = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")

    current_title = ""
    for line in lines:
        line = line.strip()
        if line.startswith('#EXTINF:'):
            parts = line.split(',')
            current_title = parts[-1].strip()
        elif line and not line.startswith('#'):
            link = line
            if not current_title:
                continue

            # মূল নাম বের করা গ্রুপ করার জন্য
            base_key = clean_series_title(current_title)
            if not base_key:
                base_key = current_title

            # যদি এই সিরিজের নাম আগে থেকেই ডিকশনারিতে থাকে
            if base_key in movies_dict:
                existing_item = movies_dict[base_key]
                existing_links = existing_item.get("link", "")
                
                # আপনার নিয়ম অনুযায়ী ডাবল কমা দিয়ে নতুন লিংকটি আগের লিংকের সাথে যুক্ত করা
                if existing_links:
                    existing_item["link"] = f"{current_title},,{link},){existing_links}"
                else:
                    existing_item["link"] = f"{current_title},,{link}"
                
                existing_item["date"] = current_time
            else:
                # নতুন সিরিজ বা মুভি হলে নতুন এন্ট্রি তৈরি করা
                new_entry = {
                    "title": current_title,
                    "details": "Director : N/A\nCast(s) : N/A\nLanguage : Bengali\nQuality : WEB-DL\nResolution : HD",
                    "img": "https://via.placeholder.com/300",
                    "date": current_time,
                    "link": f"{current_title},,{link}"
                }
                movies_dict[base_key] = new_entry

            current_title = ""

    # ডিকশনারি থেকে লিস্টে রূপান্তর এবং লেটেস্টগুলো উপরে রাখার জন্য সাজানো
    movies_list = list(movies_dict.values())
    try:
        movies_list.sort(key=lambda x: datetime.strptime(x.get("date", "01/01/2026 12:00:00 am"), "%m/%d/%Y %I:%M:%S %p"), reverse=True)
    except Exception:
        pass

    # ফাইনাল JSON ফাইলে সেভ করা
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(movies_list, f, ensure_ascii=False, indent=4)
    print("Successfully generated Popular movie.json")

if __name__ == "__main__":
    process_m3u_to_json()
