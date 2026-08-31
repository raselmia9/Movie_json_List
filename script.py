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

def get_clean_tree_key(title):
    cleaned = re.sub(r'(episodes?|ep|season|s\d+e\d+|\bpart\s*\d+|\b\d{4}\b|\b1080p\b|\b720p\b|\b4k\b|\bhd\b|\bweb[-]?dl\b)', '', title, flags=re.IGNORECASE)
    cleaned = re.sub(r'[\(\)\[\]\-:_]', ' ', cleaned)
    return ' '.join(cleaned.split()).lower()

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

def process_m3u_to_json():
    content = fetch_m3u()
    if not content:
        return

    lines = content.strip().split('\n')
    bag_of_trees = {}
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

            tree_key = get_clean_tree_key(current_title)
            if not tree_key:
                tree_key = current_title.lower()

            if tree_key in bag_of_trees:
                existing_item = bag_of_trees[tree_key]
                existing_links = existing_item.get("link", "")
                
                # যদি এটি দ্বিতীয় বা তার বেশি লিংক হয়, তবেই কম্বাইন্ড ফরম্যাট হবে
                if existing_links:
                    # যদি আগের লিংকটি সিঙ্গেল থাকে (যাতে প্রথমবার টাইটেল যুক্ত হয়)
                    if ",," not in existing_links:
                        prev_title = existing_item.get("first_title", current_title)
                        existing_item["link"] = f"{current_title},,{link},){prev_title},,{existing_links}"
                    else:
                        existing_item["link"] = f"{current_title},,{link},){existing_links}"
                else:
                    existing_item["link"] = f"{current_title},,{link}"
                
                existing_item["date"] = current_time
            else:
                clean_display_title = re.split(r'(?i)\b(season|s\d+|ep|episode|part|\d{4})\b', current_title)[0].strip(" -:_[]()")
                if not clean_display_title:
                    clean_display_title = current_title

                new_entry = {
                    "title": clean_display_title,
                    "details": "Director : N/A\nCast(s) : N/A\nLanguage : English\nQuality : WEB-DL\nResolution : HD",
                    "img": current_logo,
                    "date": current_time,
                    "link": link,  # সিঙ্গেল আইটেমের জন্য শুরুতে শুধু সরাসরি লিংক থাকবে (কোনো টাইটেল বা এক্সট্রা টেক্সট নয়)
                    "first_title": current_title
                }
                bag_of_trees[tree_key] = new_entry

            current_title = ""
            current_logo = "https://via.placeholder.com/300"

    # ফাইনাল লিস্ট তৈরির সময় টেম্পোরারি 'first_title' ফিল্ডটি মুছে ফেলা
    movies_list = []
    for item in bag_of_trees.values():
        if "first_title" in item:
            del item["first_title"]
        movies_list.append(item)
    
    try:
        movies_list.sort(key=lambda x: datetime.strptime(x.get("date", "01/01/2026 12:00:00 am"), "%m/%d/%Y %I:%M:%S %p"), reverse=True)
    except Exception:
        pass

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(movies_list, f, ensure_ascii=False, indent=4)
    
    print(f"Successfully processed! Total items: {len(movies_list)}")

if __name__ == "__main__":
    process_m3u_to_json()
