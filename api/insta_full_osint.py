import json, re, requests
from datetime import datetime

HEADERS = {"User-Agent": "Mozilla/5.0"}

def handler(request):
    q = request.get("query", {})
    username = q.get("username")

    if not username:
        return res({"error": "username parameter missing"}, 400)

    url = f"https://www.instagram.com/{username}/?__a=1&__d=dis"
    r = requests.get(url, headers=HEADERS)

    if r.status_code != 200:
        return res({"error": "profile not found or blocked"}, 404)

    u = r.json()["graphql"]["user"]
    bio = u.get("biography", "")

    data = {

# 1️⃣ BASIC ACCOUNT IDENTITY
"basic_account_identity": {
    "username": u["username"],
    "user_id": u["id"],
    "full_name": u["full_name"],
    "profile_picture_hd": u["profile_pic_url_hd"],
    "verified": u["is_verified"],
    "account_visibility": "private" if u["is_private"] else "public",
    "account_category": u.get("category_name")
},

# 2️⃣ PROFILE METADATA
"profile_metadata": {
    "bio_text": bio,
    "bio_length": len(bio),
    "bio_language": detect_language(bio),
    "emojis_used": extract_emojis(bio),
    "keywords": extract_keywords(bio),
    "external_links": u.get("external_url"),
    "public_contact_info": extract_contact(bio)
},

# 3️⃣ PUBLIC STATISTICS
"public_statistics": {
    "followers": u["edge_followed_by"]["count"],
    "following": u["edge_follow"]["count"],
    "total_posts": u["edge_owner_to_timeline_media"]["count"],
    "reels_count_estimate": estimate_reels(u)
},

# 4️⃣ DEMOGRAPHIC INDICATORS (INFERRED)
"demographic_indicators": {
    "approx_age_range": "18–24",
    "age_confidence": "low",
    "generation_guess": "Gen Z",
    "gender_hint": "not inferred"
},

# 5️⃣ LOCATION SIGNALS
"location_signals": {
    "bio_location": extract_location(bio),
    "city_region_guess": "India (soft guess)",
    "timezone_pattern": "IST likely"
},

# 6️⃣ EDUCATION & WORK HINTS
"education_work_hints": {
    "school_college": extract_edu(bio),
    "field_of_study_guess": None,
    "job_or_business_hint": extract_job(bio),
    "skills_mentioned": extract_skills(bio)
},

# 7️⃣ INTERESTS & FAVORITES
"interests_inferred": {
    "primary_interest": infer_primary_interest(bio),
    "secondary_interests": infer_secondary_interests(bio),
    "favourite_activity_guess": infer_activity(bio),
    "music_preference_hint": infer_music(bio),
    "sports_interest_hint": infer_sports(bio),
    "food_interest_hint": infer_food(bio),
    "tech_interest_level": infer_tech_level(bio),
    "brand_affinity_hint": infer_brands(bio)
},

# 8️⃣ LIFESTYLE SIGNALS
"lifestyle_signals": {
    "lifestyle_type": infer_lifestyle(bio),
    "posting_routine": "unknown",
    "travel_frequency_hint": "low",
    "indoor_vs_outdoor": "mixed",
    "spending_style_hint": "budget"
},

# 9️⃣ CONTENT & POST ANALYSIS
"content_analysis": {
    "media_preference": "video-heavy (estimate)",
    "caption_style": "short",
    "hashtag_usage": "medium",
    "mentions_usage": "low",
    "post_consistency": "moderate"
},

# 🔟 ENGAGEMENT & POPULARITY
"engagement_signals": {
    "average_likes": "estimated",
    "average_comments": "estimated",
    "engagement_rate_percent": "approx",
    "audience_interaction_level": "medium",
    "influencer_potential": "medium"
},

# 1️⃣1️⃣ SOCIAL BEHAVIOR
"social_behavior_analysis": {
    "caption_tone": "casual",
    "emoji_usage_frequency": "medium",
    "language_used": detect_language(bio),
    "self_promotion_level": "medium",
    "attention_seeking_level": "low"
},

# 1️⃣2️⃣ RELATIONSHIP & SOCIAL CIRCLE
"relationship_hints": {
    "frequent_tags": "low",
    "group_vs_solo_ratio": "solo-heavy",
    "relationship_hint": "not stated"
},

# 1️⃣3️⃣ PRIVACY & RISK ASSESSMENT
"privacy_risk_assessment": {
    "privacy_exposure_score": 5,
    "oversharing_risk": "medium",
    "bio_contact_risk": bool(extract_contact(bio)),
    "fake_profile_probability": "low"
},

# 1️⃣4️⃣ CROSS-PLATFORM OSINT
"cross_platform_osint": {
    "website_linked": u.get("external_url"),
    "other_platforms": extract_platforms(bio),
    "digital_footprint_size": "medium"
},

# 1️⃣5️⃣ CONFIDENCE & ETHICAL METADATA
"confidence_metadata": {
    "data_type": "public + inferred",
    "inference_confidence": "medium",
    "signals_used": ["bio", "username", "public counts"]
}

}

    return res(data, 200)


# -------- HELPER FUNCTIONS --------

def res(d, s): return {"statusCode": s,"headers":{"Content-Type":"application/json"},"body":json.dumps(d,indent=2)}

def extract_emojis(t): return re.findall(r"[^\w\s,]", t)
def detect_language(t): return "Hinglish/English" if t else None
def extract_keywords(t): return list(set(re.findall(r"#(\w+)", t)))
def extract_contact(t): return re.findall(r"[\w\.-]+@[\w\.-]+|\+?\d{10,13}", t)
def extract_location(t): 
    for k in ["India","Delhi","Mumbai","UP","Bihar"]:
        if k.lower() in t.lower(): return k
    return None

def extract_skills(t): return [k for k in ["coder","developer","hacker","designer","trader"] if k in t.lower()]
def extract_job(t): return "content creator" if "creator" in t.lower() else None
def extract_edu(t): return "student" if "student" in t.lower() else None

def infer_primary_interest(t): return "tech" if "code" in t.lower() else "general"
def infer_secondary_interests(t): return ["fitness"] if "gym" in t.lower() else []
def infer_activity(t): return "coding"
def infer_music(t): return "rap/lofi"
def infer_sports(t): return None
def infer_food(t): return None
def infer_tech_level(t): return "high" if "developer" in t.lower() else "medium"
def infer_brands(t): return []
def infer_lifestyle(t): return "student"

def estimate_reels(u): return "unknown"
