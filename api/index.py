import json, re, requests, statistics
from datetime import datetime

HEADERS = {"User-Agent": "Mozilla/5.0"}

def handler(request):
    try:
        username = request["query"].get("username")
    except:
        username = None

    if not username:
        return response({"error": "username parameter missing"}, 400)

    url = f"https://www.instagram.com/{username}/?__a=1&__d=dis"
    r = requests.get(url, headers=HEADERS)

    if r.status_code != 200:
        return response({"error": "profile not accessible"}, 404)

    u = r.json()["graphql"]["user"]

    posts = get_posts(u)
    hours = [p["hour"] for p in posts]

    data = {
        "status": "success",
        "username": username,
        "followers": u["edge_followed_by"]["count"],
        "following": u["edge_follow"]["count"],
        "posting_time_analysis": analyze_hours(hours),
        "engagement": calculate_engagement(posts, u["edge_followed_by"]["count"]),
        "fake_account_score": fake_score(u, posts)
    }

    return response(data, 200)

# ---------------- HELPERS ----------------

def get_posts(u, limit=12):
    posts = []
    edges = u["edge_owner_to_timeline_media"]["edges"][:limit]
    for e in edges:
        n = e["node"]
        posts.append({
            "likes": n["edge_liked_by"]["count"],
            "comments": n["edge_media_to_comment"]["count"],
            "hour": datetime.fromtimestamp(n["taken_at_timestamp"]).hour
        })
    return posts

def analyze_hours(hours):
    if not hours:
        return {"timezone": "unknown", "confidence": "low"}
    common = statistics.mode(hours)
    return {
        "most_active_hour": common,
        "timezone_guess": "IST" if 9 <= common <= 23 else "unknown",
        "confidence": "high"
    }

def calculate_engagement(posts, followers):
    if not posts or followers == 0:
        return 0
    avg_likes = sum(p["likes"] for p in posts) / len(posts)
    avg_comments = sum(p["comments"] for p in posts) / len(posts)
    return round(((avg_likes + avg_comments) / followers) * 100, 2)

def fake_score(u, posts):
    score = 100
    if u["edge_followed_by"]["count"] < 50: score -= 25
    if len(posts) < 3: score -= 20
    if not u.get("biography"): score -= 10
    return score

def response(data, status):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(data, indent=2)
    }
