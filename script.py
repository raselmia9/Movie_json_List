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

def get_master_tree_key(title):
    # টাইটেল থেকে সিজন, এপিসোড বা সংখ্যাগুলো খুব সতর্কভাবে আলাদা করে মূল 'গাছ' বা সিরিজের নাম বের করা
    # যাতে একই সিরিজের বিভিন্ন এপিসোড একই গাছের চাবি (Key) হিসেবে কাজ করে
    cleaned = re.sub(r'(episodes?|ep|season|s\d+e\d+|\bpart\s*\d+|\b\d+\b)', '', title, flags=re.IGNORECASE)
    cleaned = re.sub(r'[\(\)\[\]\-:_]', ' ', cleaned) # অতিরিক্ত ব্র্যাকেট বা হাইফেন দূর করা
    return ' '.join(cleaned.split()).lower()

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
    bag_of_trees = {}  # আমাদের 'ব্যাগ' যেখানে গাছ ও তার ফলগুলো জমা থাকবে
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

            # গাছের মূল নাম (Master Tree Key) তৈরি করা
            tree_key = get_master_tree_key(current_title)
            if not tree_key:
                tree_key = current_title.lower()

            # ব্যাগ চেক করা: এই গাছ কি ইতিমধ্যে ব্যাগে আছে?
            if tree_key in bag_of_trees:
                # গাছ আগে থেকেই আছে, তাই শুধু 'ফল' (লিংক) নিয়ে আগের গাছের সাথে যুক্ত করব
                existing_item = bag_of_trees[tree_key]
                existing_links = existing_item.get("link", "")
                
                if existing_links:
                    existing_item["link"] = f"{current_title},,{link},){existing_links}"
                else:
                    existing_item["link"] = f"{current_title},,{link}"
                
                existing_item["date"] = current_time
            else:
                # গাছ ব্যাগে নেই, তাই সম্পূর্ণ নতুন গাছসহ আইটেমটি ব্যাগে তুলব
                new_entry = {
                    "title": current_title,
                    "details": "Director : N/A\nCast(s) : N/A\nLanguage : English\nQuality : WEB-DL\nResolution : HD",
                    "img": current_logo,
                    "date": current_time,
                    "link": f"{current_title},,{link}"
                }
                bag_of_trees[tree_key] = new_entry

            # রিসেট
            current_title = ""
            current_logo = "https://via.placeholder.com/300"

    # ব্যাগ থেকে সব গাছগুলোকে লিস্টে রূপান্তর করা
    movies_list = list(bag_of_trees.values())
    
    # লেটেস্ট আপডেট অনুযায়ী সাজানো
    try:
        movies_list.sort(key=lambda x: datetime.strptime(x.get("date", "01/01/2026 12:00:00 am"), "%m/%d/%Y %I:%M:%S %p"), reverse=True)
    except Exception:
        pass

    # ফাইনাল জেসন ফাইলে সেভ করা
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(movies_list, f, ensure_ascii=False, indent=4)
    
    print(f"Successfully processed! Total unique trees (bundles) in bag: {len(movies_list)}")

if __name__ == "__main__":
    process_m3u_to_json()
