import time
from apscheduler.schedulers.blocking import BlockingScheduler
from scraper.apify_instagram import run_scraper
from pipeline.cleaner import load_and_clean
from pipeline.scorer import score_influencers
from pipeline.db import init_db, insert_posts, aggregate_influencers

# Hashtags to scrape — expand this list for more niches
HASHTAGS = [
    "punefood",
    "foodblogger",
    "punefoodies",
    "punecafe",
    "punerestaurant"
]

MAX_RESULTS_PER_TAG = 50


def run_pipeline():
    print("\n========== Pipeline Started ==========")

    # Step 1 — Scrape
    print("[Pipeline] Step 1: Scraping...")
    raw_data = run_scraper(HASHTAGS, max_results=MAX_RESULTS_PER_TAG)

    if not raw_data:
        print("[Pipeline] No data scraped. Aborting run.")
        return

    # Step 2 — Clean (pass raw data directly, don't re-read from disk)
    print("[Pipeline] Step 2: Cleaning...")
    import pandas as pd
    from pipeline.cleaner import clean
    df = clean(pd.DataFrame(raw_data))

    if df.empty:
        print("[Pipeline] Cleaned data is empty. Aborting run.")
        return

    # Step 3 — Insert posts to DB
    print("[Pipeline] Step 3: Inserting posts to DB...")
    insert_posts(df.to_dict(orient="records"))

    # Step 4 — Aggregate influencers
    print("[Pipeline] Step 4: Scoring influencers...")
    aggregate_influencers()

    print("========== Pipeline Complete ==========\n")

    
if __name__ == "__main__":
    # Always initialise DB first
    init_db()

    # Run once immediately on start
    run_pipeline()

    # Then schedule every 24 hours
    scheduler = BlockingScheduler()
    scheduler.add_job(run_pipeline, "interval", hours=24)

    print("[Scheduler] Running. Next refresh in 24 hours. Press Ctrl+C to stop.")
    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("[Scheduler] Stopped.")