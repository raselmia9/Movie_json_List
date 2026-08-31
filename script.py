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
    cleaned = re.sub(r'(s\d+e\d+|season\s*\d+|ep\s*\d+|\bpart\s*\d+|\b\d{4}\b|\b1080p\b|\b720p\b|\b4k\b|\bhd\b|\bweb[-]?dl\b)', '', title, flags=re.IGNORECASE)
    cleaned = re.sub(r'\b[nN]\b$', '', cleaned)
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

            if tree_key in bag_of_trees:
                bag_of_trees[tree_key]["links_list"].append((current_title, link))
                bag_of_trees[tree_key]["date"] = current_time
            else:
                clean_display_title = re.split(r'(?i)\b(season|s\d+|ep|episode|part|\d{4})\b', current_title)[0].strip(" -:_[]()")
                if not clean_display_title:
                    clean_display_title = current_title

                bag_of_trees[tree_key] = {
                    "title": clean_display_title,
                    "details": "Director : N/A\nCast(s) : N/A\nLanguage : Default\nQuality : WEB-DL\nResolution : HD",
                    "img": current_logo,
                    "date": current_time,
                    "links_list": [(current_title, link)]
                }

            current_title = ""
            current_logo = "https://via.placeholder.com/300"

    movies_list = []
    for tree_key, item in bag_of_trees.items():
        links_data = item.pop("links_list")
        
        if len(links_data) == 1:
            item["link"] = links_data[0][1]
        else:
            links_data.reverse() 

            formatted_links = ""
            for i, (t_title, t_link) in enumerate(links_data):
                if i == 0:
                    formatted_links = f"{t_title},,{t_link}"
                else:
                    formatted_links = f"{t_title},,{t_link},){formatted_links}"
            item["link"] = formatted_links

        movies_list.append(item)

    try:
        movies_list.sort(key=lambda x: datetime.strptime(x.get("date", "01/01/2026 12:00:00 am"), "%m/%d/%Y %I:%M:%S %p"), reverse=True)
    except Exception:
        pass

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(movies_list, f, ensure_ascii=False, indent=4)
    
    print(f"Successfully processed with 'Default' language! Total items: {len(movies_list)}")

if __name__ == "__main__":
    process_m3u_to_json()
