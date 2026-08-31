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
    # গাছের মূল নাম বের করা (সিজন বা এপিসোড কোড বাদ দিয়ে)
    cleaned = re.sub(r'(episodes?|ep\d*|season\s*\d+|s\d+e\d+|\bpart\s*\d+)', '', title, flags=re.IGNORECASE)
    cleaned = re.sub(r'[\(\)\[\]\-:_]', ' ', cleaned)
    key = ' '.join(cleaned.split()).lower()
    return key if key else title.lower()

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
        print("M3U content is empty!")
        return

    lines = content.strip().split('\n')
    bag_of_trees = {}  # আমাদের ব্যাগ যেখানে গাছগুলো জমা থাকবে
    current_time = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")

    current_title = ""
    current_logo = "https://via.placeholder.com/300"
    
    total_items_scanned = 0

    for line in lines:
        line = line.strip()
        if line.startswith('#EXTINF:'):
            current_title, current_logo = extract_info(line)
        elif line and not line.startswith('#'):
            link = line
            if not current_title:
                continue

            total_items_scanned += 1
            tree_key = get_clean_tree_key(current_title)

            # ব্যাগ চেক করা: গাছটি কি অলরেডি ব্যাগে আছে?
            if tree_key in bag_of_trees:
                # গাছ ব্যাগে আছে! তাই গাছ ডাস্টবিনে যাবে (নতুন গাছ বানাবো না), 
                # এবং শুধু 'ফল' (লিংক ও টাইটেল) আগের গাছের ঝুলিতে যোগ করব।
                bag_of_trees[tree_key]["links_list"].append((current_title, link))
                bag_of_trees[tree_key]["date"] = current_time
            else:
                # গাছ ব্যাগে নেই! তাই গাছসহ ফল নতুন এন্ট্রি হিসেবে ব্যাগে তুলব।
                clean_display_title = re.split(r'(?i)\b(season|s\d+|ep|episode|part|\d{4})\b', current_title)[0].strip(" -:_[]()")
                if not clean_display_title:
                    clean_display_title = current_title

                bag_of_trees[tree_key] = {
                    "title": clean_display_title,
                    "details": "Director : N/A\nCast(s) : N/A\nLanguage : English\nQuality : WEB-DL\nResolution : HD",
                    "img": current_logo,
                    "date": current_time,
                    "links_list": [(current_title, link)]
                }

            current_title = ""
            current_logo = "https://via.placeholder.com/300"

    print(f"Total valid items scanned from field: {total_items_scanned}")

    # ব্যাগ থেকে সাজিয়ে ফাইনাল লিস্ট তৈরি করা
    movies_list = []
    for item in bag_of_trees.values():
        links_data = item.pop("links_list")
        
        if len(links_data) == 1:
            # সিঙ্গেল আইটেম হলে শুধু সরাসরি লিংক
            item["link"] = links_data[0][1]
        else:
            # একাধিক এপিসোড বা ফল থাকলে আপনার কাঙ্ক্ষিত ফরম্যাট
            formatted_links = ""
            for i, (t_title, t_link) in enumerate(links_data):
                if i == 0:
                    formatted_links = f"{t_title},,{t_link}"
                else:
                    formatted_links = f"{t_title},,{t_link},){formatted_links}"
            item["link"] = formatted_links

        movies_list.append(item)

    # লেটেস্ট ডেটা উপরে সাজানো
    try:
        movies_list.sort(key=lambda x: datetime.strptime(x.get("date", "01/01/2026 12:00:00 am"), "%m/%d/%Y %I:%M:%S %p"), reverse=True)
    except Exception:
        pass

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(movies_list, f, ensure_ascii=False, indent=4)
    
    print(f"Successfully finished! Total unique trees in bag: {len(movies_list)}")

if __name__ == "__main__":
    process_m3u_to_json()
