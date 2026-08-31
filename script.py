import json
import re
from datetime import datetime
from difflib import SequenceMatcher
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
    # সিজন, এপিসোড, সাল, রেজোলিউশন (1080p, 720p), পার্ট ইত্যাদি রিমুভ করে শুধু মূল নাম রাখা
    cleaned = re.sub(r'(episodes?|ep|season|s\d+e\d+|\bpart\s*\d+|\b\d{4}\b|\b1080p\b|\b720p\b|\b4k\b|\bhd\b|\bweb[-]?dl\b|\b\d+\b)', '', title, flags=re.IGNORECASE)
    cleaned = re.sub(r'[\(\)\[\]\-:_]', ' ', cleaned) # ব্র্যাকেট বা হাইফেন দূর করা
    return ' '.join(cleaned.split()).lower()

def text_similarity(str1, str2):
    # দুটি টেক্সটের মধ্যে কত পার্সেন্ট মিল আছে তা বের করা (০ থেকে ১ এর মধ্যে ভ্যালু দেয়)
    return SequenceMatcher(None, str1, str2).ratio()

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

    # মূল টাইটেল বের করা
    parts = extinf_line.split(',')
    title = parts[-1].strip() if len(parts) > 1 else "Unknown"
    
    return title, logo_url

def process_m3u_to_json():
    content = fetch_m3u()
    if not content:
        return

    lines = content.strip().split('\n')
    bag_of_trees = {}  # মাস্টার গাছ ও ফলের ব্যাগ
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

            raw_clean_title = clean_series_title(current_title)
            if not raw_clean_title:
                raw_clean_title = current_title.lower()

            # ব্যাগ চেক করা: অন্তত ৩০% (0.3) বা তার বেশি মিল পাওয়া যায় কি না দেখা
            matched_key = None
            for existing_key in bag_of_trees.keys():
                similarity = text_similarity(raw_clean_title, existing_key)
                if similarity >= 0.3:  # ৩০% বা বেশি মিললেই একই গাছ হিসেবে ধরবে
                    matched_key = existing_key
                    break

            if matched_key:
                # যদি মিলে যায়, তবে শুধু 'ফল' (লিংক) আগের গাছের সাথে যুক্ত করব
                existing_item = bag_of_trees[matched_key]
                existing_links = existing_item.get("link", "")
                
                if existing_links:
                    existing_item["link"] = f"{current_title},,{link},){existing_links}"
                else:
                    existing_item["link"] = f"{current_title},,{link}"
                
                existing_item["date"] = current_time
            else:
                # না মিললে সম্পূর্ণ নতুন গাছ বা বান্ডিল হিসেবে ব্যাগে তুলব
                # কিন্তু কার্ডের ডিসপ্লে টাইটেল থেকে অতিরিক্ত অংশ (যেমন S05E111) বাদ দিয়ে শুধু মূল নাম রাখব
                display_title_parts = re.split(r'(?i)\b(season|s\d+|ep|episode|part|\d{4})\b', current_title)
                clean_display_title = display_title_parts[0].strip(" -:_[]()")
                if not clean_display_title:
                    clean_display_title = current_title

                new_entry = {
                    "title": clean_display_title,  # শুধুমাত্র সিরিজের মূল নাম
                    "details": "Director : N/A\nCast(s) : N/A\nLanguage : English\nQuality : WEB-DL\nResolution : HD",
                    "img": current_logo,
                    "date": current_time,
                    "link": f"{current_title},,{link}"
                }
                bag_of_trees[raw_clean_title] = new_entry

            # রিসেট
            current_title = ""
            current_logo = "https://via.placeholder.com/300"

    movies_list = list(bag_of_trees.values())
    
    try:
        movies_list.sort(key=lambda x: datetime.strptime(x.get("date", "01/01/2026 12:00:00 am"), "%m/%d/%Y %I:%M:%S %p"), reverse=True)
    except Exception:
        pass

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(movies_list, f, ensure_ascii=False, indent=4)
    
    print(f"Successfully processed with 30%+ similarity! Total bundles: {len(movies_list)}")

if __name__ == "__main__":
    process_m3u_to_json()
