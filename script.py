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
    # এপিসোড, সিজন বা সংখ্যা বাদ দিয়ে মূল সিরিজের নাম আলাদা করা, যাতে একই সিরিজের সব পর্ব এক জায়গায় আসে
    cleaned = re.sub(r'(episodes?|ep|season|s\d+e\d+|\d+)', '', title, flags=re.IGNORECASE)
    return cleaned.strip().lower()

def extract_info(extinf_line):
    # লোগো বা থামনেল খোঁজা
    logo_match = re.search(r'tvg-logo="(.*?)"', extinf_line)
    if not logo_match:
        logo_match = re.search(r'https?://[^\s"]+\.(?:jpg|jpeg|png|webp)', extinf_line, re.IGNORECASE)
        logo_url = logo_match.group(0) if logo_match else "https://via.placeholder.com/300"
    else:
        logo_url = logo_match.group(1)

    if not logo_url or logo_url.strip() == "":
        logo_url = "https://via.placeholder.com/300"

    # টাইটেল বের করা
    parts = extinf_line.split(',')
    title = parts[-1].strip() if len(parts) > 1 else "Unknown"
    
    return title, logo_url

def process_m3u_to_json():
    content = fetch_m3u()
    if not content:
        return

    lines = content.strip().split('\n')
    movies_dict = {}  # সমস্ত আইটেম স্টোর করার জন্য মাস্টার ডিকশনারি
    current_time = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")

    current_title = ""
    current_logo = "https://via.placeholder.com/300"
    
    # পুরো ফাইলের এক প্রান্ত থেকে অন্য প্রান্ত পর্যন্ত সব লাইন চেক করার লুপ
    for line in lines:
        line = line.strip()
        if line.startswith('#EXTINF:'):
            current_title, current_logo = extract_info(line)
        elif line and not line.startswith('#'):
            link = line
            if not current_title:
                continue

            # মূল নাম বা কি তৈরি করা যার মাধ্যমে মিল পাওয়া যাবে
            base_key = clean_series_title(current_title)
            if not base_key:
                base_key = current_title.lower()

            # যদি এই সিরিজের বান্ডিল আগে থেকেই তৈরি করা থাকে
            if base_key in movies_dict:
                existing_item = movies_dict[base_key]
                existing_links = existing_item.get("link", "")
                
                # নতুন লিংকটি আগের লিংকের সাথে আপনার নির্দিষ্ট ফরম্যাটে যুক্ত করা
                if existing_links:
                    existing_item["link"] = f"{current_title},,{link},){existing_links}"
                else:
                    existing_item["link"] = f"{current_title},,{link}"
                
                existing_item["date"] = current_time
            else:
                # নতুন সিরিজ বা মুভি পেলে নতুন বান্ডিল বা এন্ট্রি তৈরি করা
                new_entry = {
                    "title": current_title,
                    "details": "Director : N/A\nCast(s) : N/A\nLanguage : English\nQuality : WEB-DL\nResolution : HD",
                    "img": current_logo,
                    "date": current_time,
                    "link": f"{current_title},,{link}"
                }
                movies_dict[base_key] = new_entry

            # পরবর্তী আইটেমের জন্য রিসেট করা
            current_title = ""
            current_logo = "https://via.placeholder.com/300"

    # সব আইটেম প্রসেস করার পর সেগুলোকে লিস্টে রূপান্তর করা
    movies_list = list(movies_dict.values())
    
    # লেটেস্ট আপডেটগুলো উপরে রাখার জন্য সর্ট করা
    try:
        movies_list.sort(key=lambda x: datetime.strptime(x.get("date", "01/01/2026 12:00:00 am"), "%m/%d/%Y %I:%M:%S %p"), reverse=True)
    except Exception:
        pass

    # ফাইনাল JSON ফাইলে সেভ করা
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(movies_list, f, ensure_ascii=False, indent=4)
    
    print(f"Successfully processed all items! Total unique bundles: {len(movies_list)}")

if __name__ == "__main__":
    process_m3u_to_json()
