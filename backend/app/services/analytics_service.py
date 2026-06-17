"""
Analytics Service
=================
Parses User-Agent strings and stores click events in MongoDB.
"""

from datetime import datetime, timezone
from bson import ObjectId
from user_agents import parse as ua_parse
from app.database.collections import analytics_collection


async def record_click(url_id: str, ip_address: str, user_agent_str: str) -> None:
    """
    Parse the request's User-Agent and insert an analytics record.

    Parameters
    ----------
    url_id : str
        String representation of the URL document's ObjectId.
    ip_address : str
        Client IP address.
    user_agent_str : str
        Raw User-Agent header value.
    """
    ua = ua_parse(user_agent_str)

    record = {
        "url_id": ObjectId(url_id),
        "ip_address": ip_address,
        "user_agent": user_agent_str,
        "browser": ua.browser.family,
        "device": "Mobile" if ua.is_mobile else ("Tablet" if ua.is_tablet else "Desktop"),
        "os": ua.os.family,
        "timestamp": datetime.now(timezone.utc),
    }

    await analytics_collection().insert_one(record)


async def get_analytics_for_url(url_id: str) -> dict:
    """
    Aggregate click analytics for a specific URL.

    Returns
    -------
    dict
        total_clicks, click_history (last 100), browser_breakdown, device_breakdown, daily_counts
    """
    collection = analytics_collection()
    oid = ObjectId(url_id)

    cursor = collection.find({"url_id": oid}).sort("timestamp", -1).limit(100)
    records = await cursor.to_list(length=100)

    total_clicks = await collection.count_documents({"url_id": oid})

    browser_breakdown: dict[str, int] = {}
    device_breakdown: dict[str, int] = {}
    daily_counts: dict[str, int] = {}

    for r in records:
        browser = r.get("browser", "Unknown")
        device = r.get("device", "Unknown")
        day = r["timestamp"].strftime("%Y-%m-%d")

        browser_breakdown[browser] = browser_breakdown.get(browser, 0) + 1
        device_breakdown[device] = device_breakdown.get(device, 0) + 1
        daily_counts[day] = daily_counts.get(day, 0) + 1

    click_history = [
        {
            "ip_address": r.get("ip_address"),
            "browser": r.get("browser"),
            "device": r.get("device"),
            "os": r.get("os"),
            "timestamp": r["timestamp"].isoformat(),
        }
        for r in records
    ]

    return {
        "url_id": url_id,
        "total_clicks": total_clicks,
        "click_history": click_history,
        "browser_breakdown": browser_breakdown,
        "device_breakdown": device_breakdown,
        "daily_counts": daily_counts,
    }