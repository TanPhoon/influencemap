import json
import os
import glob
import pandas as pd

RAW_DATA_PATH = "data/raw"

EXCLUDE_KEYWORDS = [
    "moscow", "london", "paris", "berlin", "tokyo", "seoul", "beijing",
    "new york", "sydney", "dubai", "singapore", "bangkok", "jakarta",
    "chile", "brazil", "mexico", "spain", "italy", "france", "germany",
    "russia", "china", "japan", "korea", "australia", "canada", "usa",
    "america", "turkey", "egypt", "nigeria", "kenya", "ghana"
]

INCLUDE_KEYWORDS = [
    "pune", "india", "mumbai", "delhi", "bangalore", "bengaluru",
    "hyderabad", "nashik", "kolhapur", "nagpur", "pcmc", "pimpri",
    "shivajinagar", "koregaon", "baner", "hinjewadi", "kothrud",
    "viman nagar", "wakad", "fc road", "mg road", "maharashtra",
    "marathi", "desi", "indian", "bharat", "swiggy", "zomato",
    "instapur", "instapune", "puneri", "punekar"
]

def filter_local(df: pd.DataFrame) -> pd.DataFrame:
    """
    Two-pass location filter:
    Pass 1 — Keep posts that have explicit India/Pune signals (strong include)
    Pass 2 — From remaining, drop posts with explicit foreign signals
    Decision: union approach so English-caption Indian posts aren't lost
    """
    def has_include_signal(row):
        text = f"{row.get('caption', '')} {row.get('hashtags', '')}".lower()
        return any(kw in text for kw in INCLUDE_KEYWORDS)

    def has_exclude_signal(row):
        text = f"{row.get('caption', '')} {row.get('hashtags', '')}".lower()
        return any(kw in text for kw in EXCLUDE_KEYWORDS)

    before = len(df)

    # Posts with explicit India signal — always keep
    india_posts = df[df.apply(has_include_signal, axis=1)]

    # Posts with no signal either way — keep if no foreign signal
    neutral_posts = df[
        ~df.apply(has_include_signal, axis=1) &
        ~df.apply(has_exclude_signal, axis=1)
    ]

    df = pd.concat([india_posts, neutral_posts]).drop_duplicates(subset=["id"])
    after = len(df)

    print(f"[Cleaner] Location filter: {before} → {after} records ({before - after} removed)")
    return df

def load_latest_raw(hashtag: str = None) -> pd.DataFrame:
    """
    Load the most recent raw JSON file.
    If hashtag is specified, loads latest file for that hashtag.
    """
    pattern = f"{RAW_DATA_PATH}/{hashtag}_*.json" if hashtag else f"{RAW_DATA_PATH}/*.json"
    files = glob.glob(pattern)

    if not files:
        print("[Cleaner] No raw files found.")
        return pd.DataFrame()

    latest_file = max(files, key=os.path.getctime)
    print(f"[Cleaner] Loading {latest_file}")

    with open(latest_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    return pd.DataFrame(data)


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and standardise raw Apify Instagram data.
    Documents every decision made.
    """
    if df.empty:
        print("[Cleaner] Empty dataframe, nothing to clean.")
        return df

    # 1. Drop error rows (Apify sometimes returns error objects)
    df = df[~df.get("error", pd.Series([None]*len(df))).notna()]

    # 2. Keep only relevant columns
    keep_cols = [
        "id", "ownerUsername", "ownerFullName", "ownerId",
        "url", "caption", "hashtags", "likesCount",
        "commentsCount", "type", "timestamp", "inputUrl"
    ]
    existing_cols = [c for c in keep_cols if c in df.columns]
    df = df[existing_cols]

    # 3. Drop rows missing critical identity fields
    df = df.dropna(subset=["id", "ownerUsername"])

    # 4. Fill missing numeric fields with 0
    # Decision: missing likes/comments = 0, not NaN, for safe arithmetic
    df["likesCount"] = pd.to_numeric(df.get("likesCount", 0), errors="coerce").fillna(0).astype(int).clip(lower=0)
    df["commentsCount"] = pd.to_numeric(df.get("commentsCount", 0), errors="coerce").fillna(0).astype(int).clip(lower=0)
    
    # 5. Fill missing text fields with empty string
    df["caption"] = df.get("caption", "").fillna("")
    df["ownerFullName"] = df.get("ownerFullName", "").fillna("Unknown")

    # 6. Standardise hashtags — convert list to comma-separated string
    # Decision: store as string for SQLite compatibility
    df["hashtags"] = df["hashtags"].apply(
        lambda x: ", ".join(x) if isinstance(x, list) else ""
    )

    # 7. Standardise timestamp to ISO format string
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")

    # 8. Remove duplicate post IDs
    # Decision: keep first occurrence if duplicates exist across scrape runs
    df = df.drop_duplicates(subset=["id"], keep="first")

   # 9. Strip whitespace from string fields
    df["ownerUsername"] = df["ownerUsername"].str.strip().str.lower()
    df["caption"] = df["caption"].str.strip()

    # 10. Filter to local/India-relevant posts only
    df = filter_local(df)

    print(f"[Cleaner] Cleaned {len(df)} records.")
    return df
    


def load_and_clean(hashtag: str = None) -> pd.DataFrame:
    """Main entry point — load latest raw file and clean it."""
    df = load_latest_raw(hashtag)
    return clean(df)


if __name__ == "__main__":
    df = load_and_clean()
    print(df[["ownerUsername", "likesCount", "commentsCount", "timestamp"]].head(10))