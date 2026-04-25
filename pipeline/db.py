import sqlite3
import os

DB_PATH = "influencemap.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS posts (
            id TEXT PRIMARY KEY,
            owner_username TEXT,
            owner_full_name TEXT,
            owner_id TEXT,
            post_url TEXT,
            caption TEXT,
            hashtags TEXT,
            likes_count INTEGER DEFAULT 0,
            comments_count INTEGER DEFAULT 0,
            post_type TEXT,
            timestamp TEXT,
            scraped_hashtag TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS influencers (
            owner_username TEXT PRIMARY KEY,
            owner_full_name TEXT,
            owner_id TEXT,
            total_posts INTEGER DEFAULT 0,
            total_likes INTEGER DEFAULT 0,
            total_comments INTEGER DEFAULT 0,
            avg_likes REAL DEFAULT 0,
            avg_comments REAL DEFAULT 0,
            engagement_score REAL DEFAULT 0,
            niches TEXT,
            profile_url TEXT,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    conn.close()
    print("[DB] Tables initialized.")

def insert_posts(records: list[dict]):
    conn = get_connection()
    cursor = conn.cursor()
    inserted = 0

    for r in records:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO posts (
                    id, owner_username, owner_full_name, owner_id,
                    post_url, caption, hashtags, likes_count,
                    comments_count, post_type, timestamp, scraped_hashtag
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                r.get("id"),
                r.get("ownerUsername"),
                r.get("ownerFullName"),
                r.get("ownerId"),
                r.get("url"),
                r.get("caption", ""),
                ", ".join(r.get("hashtags", [])),
                r.get("likesCount", 0),
                r.get("commentsCount", 0),
                r.get("type"),
                r.get("timestamp"),
                r.get("inputUrl", "").split("/tags/")[-1].strip("/")
            ))
            inserted += 1
        except Exception as e:
            print(f"[DB] Skipped post {r.get('id')}: {e}")

    conn.commit()
    conn.close()
    print(f"[DB] Inserted {inserted} posts.")

def aggregate_influencers():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO influencers (
            owner_username, owner_full_name, owner_id,
            total_posts, total_likes, total_comments,
            avg_likes, avg_comments, engagement_score,
            niches, profile_url, last_updated
        )
        SELECT
            owner_username,
            owner_full_name,
            owner_id,
            COUNT(*) as total_posts,
            SUM(likes_count) as total_likes,
            SUM(comments_count) as total_comments,
            AVG(likes_count) as avg_likes,
            AVG(comments_count) as avg_comments,
            (AVG(likes_count) + AVG(comments_count) * 2) as engagement_score,
            GROUP_CONCAT(DISTINCT scraped_hashtag) as niches,
            'https://www.instagram.com/' || owner_username || '/' as profile_url,
            CURRENT_TIMESTAMP
        FROM posts
        WHERE owner_username IS NOT NULL
        GROUP BY owner_username;
    """)

    conn.commit()
    conn.close()
    print("[DB] Influencers aggregated.")

if __name__ == "__main__":
    init_db()