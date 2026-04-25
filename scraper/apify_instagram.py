import os
import json
import time
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
RAW_DATA_PATH = "data/raw"

def scrape_instagram_hashtag(hashtag: str, max_results: int = 50) -> list[dict]:
    """
    Scrape public Instagram posts by hashtag using Apify.
    Returns a list of raw post/profile dicts.
    """
    client = ApifyClient(APIFY_API_TOKEN)

    run_input = {
    "directUrls": [f"https://www.instagram.com/explore/tags/{hashtag}/"],
    "resultsType": "posts",
    "resultsLimit": max_results,
}

    print(f"[Apify] Starting scrape for #{hashtag} ...")

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

    print(f"[Apify] Fetched {len(results)} results for #{hashtag}")
    return results


def save_raw(data: list[dict], hashtag: str):
    """Save raw JSON dump to data/raw/"""
    os.makedirs(RAW_DATA_PATH, exist_ok=True)
    filename = f"{RAW_DATA_PATH}/{hashtag}_{int(time.time())}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[Raw] Saved to {filename}")
    return filename


def run_scraper(hashtags: list[str], max_results: int = 50):
    """
    Main entry point. Scrapes each hashtag and saves raw output.
    Returns all results combined.
    """
    all_results = []
    for tag in hashtags:
        data = scrape_instagram_hashtag(tag, max_results)
        if data:
            save_raw(data, tag)
            all_results.extend(data)
    return all_results


if __name__ == "__main__":
    # Test run — food niche
    results = run_scraper(["foodblogger", "punefood"], max_results=20)
    print(f"Total records scraped: {len(results)}")