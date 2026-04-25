import pandas as pd

def score_influencers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate post-level data to influencer-level and compute scores.

    Scoring logic:
    - avg_likes: average likes per post
    - avg_comments: average comments per post
    - engagement_score: weighted sum (comments worth 2x likes)
    - consistency_score: number of posts scraped (proxy for activity)
    - final_score: combined metric, normalised 0-100
    """

    if df.empty:
        print("[Scorer] Empty dataframe.")
        return df

    # Aggregate by influencer
    agg = df.groupby("ownerUsername").agg(
        owner_full_name=("ownerFullName", "first"),
        owner_id=("ownerId", "first"),
        total_posts=("id", "count"),
        total_likes=("likesCount", "sum"),
        total_comments=("commentsCount", "sum"),
        avg_likes=("likesCount", "mean"),
        avg_comments=("commentsCount", "mean"),
        niches=("hashtags", lambda x: ", ".join(set(", ".join(x).split(", ")))),
        last_post=("timestamp", "max")
    ).reset_index()

    # Engagement score: likes + 2x comments (comments signal deeper engagement)
    agg["engagement_score"] = agg["avg_likes"] + (agg["avg_comments"] * 2)

    # Consistency score: more posts in dataset = more active poster
    agg["consistency_score"] = agg["total_posts"]

    # Final score: normalise engagement 0-100
    max_eng = agg["engagement_score"].max()
    if max_eng > 0:
        agg["final_score"] = (agg["engagement_score"] / max_eng * 100).round(2)
    else:
        agg["final_score"] = 0.0

    # Profile URL
    agg["profile_url"] = "https://www.instagram.com/" + agg["ownerUsername"] + "/"

    # Sort by final score descending
    agg = agg.sort_values("final_score", ascending=False).reset_index(drop=True)

    print(f"[Scorer] Scored {len(agg)} influencers.")
    return agg


if __name__ == "__main__":
    from pipeline.cleaner import load_and_clean
    df = load_and_clean()
    scored = score_influencers(df)
    print(scored[["ownerUsername", "avg_likes", "avg_comments", "engagement_score", "final_score"]].head(10))