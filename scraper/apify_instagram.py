import os
import json
import time
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
RAW_DATA_PATH = "data/raw"

# Hyper-local hashtags — only real local influencers use these
DEFAULT_HASHTAGS = [
    "punefoodblogger",
    "punefoodies",
    "puneeats",
    "punecafehop",
    "puneinfluencer",
    "foodiepune",
    "punefoodie",
    "cafehoppingpune",
    "punerestaurant",
    "punecafe"
]


def scrape_instagram_hashtag(hashtag: str, max_results: int = 50) -> list[dict]:
    client = ApifyClient(APIFY_API_TOKEN)

    run_input = {
        "directUrls": [f"https://www.instagram.com/explore/tags/{hashtag}/"],
        "resultsType": "posts",
        "resultsLimit": max_results,
    }

    print(f"[Apify] Scraping #{hashtag} ...")

    try:
        run = client.actor("apify/instagram-scraper").call(run_input=run_input)
    except Exception as e:
        print(f"[Apify] Actor run failed: {e}")
        return []

    results = []
    try:
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            results.append(item)
    except Exception as e:
        print(f"[Apify] Failed to fetch results: {e}")
        return []

    # Tag each post with which hashtag found it
    for item in results:
        item["searchQuery"] = hashtag

    print(f"[Apify] Fetched {len(results)} posts for #{hashtag}")
    return results


def save_raw(data: list[dict], label: str):
    os.makedirs(RAW_DATA_PATH, exist_ok=True)
    filename = f"{RAW_DATA_PATH}/{label}_{int(time.time())}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[Raw] Saved to {filename}")
    return filename


def run_scraper(hashtags: list[str] = None, max_results: int = 50) -> list[dict]:
    if not hashtags:
        hashtags = DEFAULT_HASHTAGS

    all_results = []
    for tag in hashtags:
        data = scrape_instagram_hashtag(tag, max_results)
        if data:
            save_raw(data, tag)
            all_results.extend(data)

    print(f"[Scraper] Total raw posts collected: {len(all_results)}")
    return all_results


if __name__ == "__main__":
    results = run_scraper(["punefoodblogger", "punefoodies"], max_results=20)
    print(f"Total: {len(results)}")