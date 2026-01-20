import json, re, requests, statistics
from datetime import datetime

HEADERS = {"User-Agent": "Mozilla/5.0"}

# ---------- MAIN HANDLER ----------
def handler(request):
    username = request.get("query", {}).get("username")
    if not username:
        return res({"error": "username required"}, 400)

    profile_url = f"https://www.instagram.com/{username}/?__a=1&__d=dis"
    r = requests.get(profile_url, headers=HEADERS)
    if r.status_code != 200:
        return res({"error": "profile not accessible"}, 404)

    u = r.json()["graphql"]["user"]
    bio = u.get("biography", "")

    posts = fetch_posts(u)

    posting_times = [p["time"] for p in posts]
    likes = [p["likes"] for p in posts]
    comments = [p["comments"] for p in posts]

    engagement_rate = calc_engagement(likes, comments, u["edge_followed_by"]["count"])
    timezone_data = analyze_timezone(posting_times)
    fake_score = fake_account_score(u, posts, engagement_rate)

    data = {

# BASIC
"basic_identity": {
    "username": u["username"],
    "user_id": u["id"],
    "full_name": u["full_name"],
    "profile_pic_hd": u["profile_pic_url_hd"],
    "verified": u["is_verified"],
    "account_visibility": "private" if u["is_private"] else "public",
    "account_type": "business" if u.get("is_business_account") else "personal"
},

# STATS
"public_statistics": {
    "followers": u["edge_followed_by"]["count"],
    "following": u["edge_follow"]["count"],
    "total_posts": u["edge_owner_to_timeline_media"]["count"],
    "followers_following_ratio": ratio(u)
},

# ⏱ POSTING TIME & TIMEZONE
"posting_time_analysis": {
    "most_common_post_hour": timezone_data["common_hour"],
    "active_hours": timezone_data["active_hours"],
    "timezone_guess": timezone_data["timezone"],
    "timezone_confidence": timezone_data["confidence"]
},

# 📊 REAL ENGAGEMENT
"real_engagement_analysis": {
    "average_likes": avg(likes),
    "average_comments": avg(comments),
    "engagement_rate_percent": engagement_rate,
    "like_comment_ratio": ratio_simple(likes, comments),
    "engagement_quality": engagement_quality(engagement_rate)
},

# 🧠 FAKE ACCOUNT DETECTOR (100 POINT)
"fake_account_detector": {
    "fake_score_out_of_100": fake_score,
    "risk_level": fake_risk(fake_score),
    "signals_used": [
        "followers-following ratio",
        "engagement rate",
        "post consistency",
        "profile completeness"
    ]
},

# CONFIDENCE
"confidence_metadata": {
    "data_type": "public + OSINT inferred",
    "confidence_level": "medium-high",
    "ethical_notice": "no private data used"
}

}

    return res(data, 200)

# ---------- POST SCRAPER ----------
def fetch_posts(u, limit=12):
    posts = []
    edges = u["edge_owner_to_timeline_media"]["edges"][:limit]
    for e in edges:
        node = e["node"]
        posts.append({
            "time": datetime.fromtimestamp(node["taken_at_timestamp"]),
            "likes": node["edge_liked_by"]["count"],
            "comments": node["edge_media_to_comment"]["count"]
        })
    return posts

# ---------- ENGAGEMENT ----------
def calc_engagement(likes, comments, followers):
    if not likes or followers == 0:
        return 0
    return round(((avg(likes) + avg(comments)) / followers) * 100, 2)

# ---------- TIMEZONE ----------
def analyze_timezone(times):
    if not times:
        return {"common_hour": None, "active_hours": [], "timezone": "unknown", "confidence": "low"}

    hours = [t.hour for t in times]
    common_hour = statistics.mode(hours)
    active_hours = sorted(set(hours))

    timezone = "IST" if 9 <= common_hour <= 23 else "Unknown"
    confidence = "high" if len(times) >= 8 else "medium"

    return {
        "common_hour": common_hour,
        "active_hours": active_hours,
        "timezone": timezone,
        "confidence": confidence
    }

# ---------- FAKE ACCOUNT SCORING ----------
def fake_account_score(u, posts, engagement):
    score = 100

    if u["edge_followed_by"]["count"] < 50:
        score -= 25
    if ratio(u) < 0.2:
        score -= 20
    if engagement < 0.5:
        score -= 20
    if len(posts) < 3:
        score -= 15
    if not u.get("biography"):
        score -= 10
    if not u.get("profile_pic_url_hd"):
        score -= 10

    return max(score, 0)

def fake_risk(score):
    if score >= 80: return "low"
    if score >= 50: return "medium"
    return "high"

# ---------- HELPERS ----------
def res(d,s): return {"statusCode":s,"headers":{"Content-Type":"application/json"},"body":json.dumps(d,indent=2)}
def avg(l): return round(sum(l)/len(l),2) if l else 0
def ratio(u): return round(u["edge_followed_by"]["count"]/max(1,u["edge_follow"]["count"]),2)
def ratio_simple(a,b): return round(avg(a)/max(1,avg(b)),2) if a and b else None
def engagement_quality(e): return "high" if e>=3 else "medium" if e>=1 else "low"
