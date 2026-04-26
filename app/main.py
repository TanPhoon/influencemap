from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import sqlite3
import os

DB_PATH = "influencemap.db"

app = FastAPI(
    title="InfluenceMap API",
    description="B2B Micro-Influencer Lead Generator for Marketing Agencies",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/")
def serve_frontend():
    return FileResponse("app/static/index.html")


@app.get("/api/influencers")
def get_influencers(
    min_engagement: float = Query(default=0, description="Minimum engagement score"),
    min_posts: int = Query(default=1, description="Minimum posts in dataset"),
    niche: str = Query(default="", description="Filter by niche keyword")
):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            owner_username,
            owner_full_name,
            total_posts,
            total_likes,
            total_comments,
            ROUND(avg_likes, 1) as avg_likes,
            ROUND(avg_comments, 1) as avg_comments,
            ROUND(engagement_score, 2) as engagement_score,
            niches,
            profile_url,
            last_updated
        FROM influencers
        WHERE engagement_score >= ?
        AND total_posts >= ?
    """
    params = [min_engagement, min_posts]

    if niche.strip():
        query += " AND niches LIKE ?"
        params.append(f"%{niche.strip()}%")

    query += " ORDER BY engagement_score DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return {
        "count": len(rows),
        "influencers": [dict(row) for row in rows]
    }


@app.get("/api/stats")
def get_stats():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM influencers")
    total_influencers = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM posts")
    total_posts = cursor.fetchone()[0]

    cursor.execute("SELECT MAX(last_updated) FROM influencers")
    last_updated = cursor.fetchone()[0]

    conn.close()
    return {
        "total_influencers": total_influencers,
        "total_posts": total_posts,
        "last_updated": last_updated or "Never"
    }
from fastapi import BackgroundTasks
from scraper.apify_instagram import run_scraper
from pipeline.cleaner import clean
from pipeline.db import insert_posts, aggregate_influencers
import pandas as pd

@app.post("/api/scrape")
@app.post("/api/scrape")
def scrape_niche(background_tasks: BackgroundTasks, hashtag: str = Query(..., description="Hashtag to scrape")):
    def pipeline(tag: str):
        print(f"[API] Scraping #{tag}...")
    # Combine user query with pune prefix for local relevance
        local_variants = [
            tag,
            f"pune{tag}",
            f"{tag}pune",
        ]
        raw = run_scraper(local_variants, max_results=30)
        if raw:
            df = clean(pd.DataFrame(raw))
            insert_posts(df.to_dict(orient="records"))
            aggregate_influencers()
            print(f"[API] Done scraping #{tag}")

    background_tasks.add_task(pipeline, hashtag)
    return {"message": f"Scraping #{hashtag} started. Refresh results in ~30 seconds."}