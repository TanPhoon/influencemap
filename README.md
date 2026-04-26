# Background :

I am 19 year old and I code as a hobby (not on github, locally). I also work as a Social Media Marketer as a sidehustle. While working I realized there was a gap in the Marketing Agency and Influencers domain. If an agency wanted an influencer for a certain _Niche_ (such as food vlogger, cafe-hopper, etc) for a _specific_ budget, they would manually look for influencer and filter them out, which is honestly kinda boring. So I built a system to find creators from certain niche for **brand** collaborations.

**Here you go, all the specifics are listed below:**

# The Problem :

Small restaurants, cafes, and local businesses want to do influencer marketing but have no idea where to start. They either pay too much for macro-influencers who don't convert, or they waste hours manually searching Instagram for relevant micro-influencers in their city. Marketing agencies dealing with these clients face the same issue at scale.
There's no clean, affordable way to get a shortlist of vetted local micro-influencers for a specific niche. InfluenceMap tries to fix that.

## What Exactly Happens:

You pick a niche — say, "pune food blogger" — and the pipeline scrapes Instagram for relevant posts using hyper-local hashtags, cleans the data, scores each account by engagement, and stores everything in a database. A FastAPI interface lets you filter, search, and export the results as a CSV.
The scraper runs automatically every 24 hours so the data stays fresh without manual intervention.

# Deployed Link:

So before all that technical jargon, just use the link below to test the solution out. I have built a dashboard and hosted it.

https://web-production-f5ea0.up.railway.app

# Architecture:

The project has three main parts:

**Scraper** — Uses Apify's Instagram actor to pull public post data from hashtag pages. We use hyper-local hashtags (like #punefoodblogger, #punecafe) instead of generic ones to avoid getting flooded with irrelevant global content.

**Pipeline** — Raw JSON from Apify gets cleaned with pandas (fixing negative counts, standardising timestamps, dropping foreign-language posts), then inserted into a SQLite database. An aggregation step computes per-influencer stats from the post-level data. A scheduler runs this whole sequence every 24 hours using APScheduler.

**Interface** — FastAPI serves a minimal HTML frontend and three API endpoints. The frontend lets you filter by engagement score, post count, and niche keyword, and export results to CSV. There's also a "Scrape New Niche" button that triggers a fresh pipeline run in the background for any hashtag you want.

## Techstack

> Python 3.10

> Apify (Instagram scraper actor)

> pandas for cleaning

> SQLite for storage

> APScheduler for automation

> FastAPI + Uvicorn for the API and frontend

> Vanilla HTML/CSS/JS (no framework)

# API Endpoints:

> **GET /** — serves the frontend

> **GET /api/influencers** — returns a filtered, scored list of influencers. Query params: min_engagement, min_posts, niche.

> **GET /api/stats** — returns total influencer count, total posts scraped, and last updated timestamp.

> **POST /api/scrape?hashtag=yourhashtag** — triggers a fresh scrape for a given hashtag and indexes the results. Runs in the background, takes about 30 seconds.

# Run Locally

## Prerequisites:

- Python 3.10+
- An Apify account with API token (Free tier works)
- Git

```
git clone https://github.com/TanPhoon/influencemap.git

cd influencemap

pip install -r requirements.txt
```

### Environment Variables:

Create a .env file in the project root:

`APIFY_API_TOKEN=your_apify_token_here `

You can get your token from https://console.apify.com/settings/integrations

**Seed the database**

This runs the full pipeline once to populate the database:

`python -m pipeline.scheduler`

Press Ctrl+C after the first run completes (it will then wait 24 hours for the next run).

**Start the server**

`uvicorn app.main:app --reload`

## Scoring Logic

Since Apify's free tier returns post-level data rather than profile-level data, we don't have follower counts. The engagement score is computed as:

`engagement_score = avg_likes + (avg_comments × 2)`

_Comments are weighted higher than likes because commenting takes more effort and signals stronger audience connection._ This is a proxy for true engagement rate (which would require follower counts), and it works reasonably well for relative ranking within a dataset.

## Design Decisions & Trade-offs:

While executing I found random infuencers i.e from anywhere in the world joining the data. So I created a location filter .

The location filter in cleaner.py uses a keyword exclusion approach to drop posts with clear foreign signals (city names, country names in captions/hashtags). This keeps the dataset locally relevant without needing a full language detection model.

**The trade-off:** posts with no location signal at all — neither Indian nor foreign — are kept by default. This means a small number of neutral global posts make it through. The alternative (dropping everything with no India signal) was too aggressive and removed legitimate English-language posts from Indian creators.

> A better approach with more time would be to use a lightweight language detection library like langdetect combined with Instagram's location tags when available.

# Known Limitations

Follower counts aren't available on Apify's free tier without running a separate profile scrape per account, which burns credits quickly. The engagement score is therefore a relative ranking metric, not an absolute engagement rate.
The dataset size depends on Apify's free tier limits. Each scrape run pulls around 20-50 posts per hashtag. For a production version you'd want a paid Apify plan and a proper database like PostgreSQL.
The SQLite database resets on Railway's free tier between deploys.

# Repository:

https://github.com/TanPhoon/influencemap
