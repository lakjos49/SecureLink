"""
SecureLink CLI Tester
Run from backend with:
    python test_shortener.py
or
    python test_shortener.py https://example.com --alias custom123
"""

import argparse
import asyncio
from datetime import datetime, timezone
from urllib.parse import urlparse

from motor.motor_asyncio import AsyncIOMotorClient

from app.utils.helpers import generate_short_code, serialize_doc
from app.services.security.url_analyzer import analyze_url
from app.core.config import settings


def normalize_url(raw_url: str) -> str:
    raw_url = raw_url.strip()
    if not raw_url:
        raise ValueError("URL is required.")

    parsed = urlparse(raw_url)
    if not parsed.scheme:
        raw_url = f"https://{raw_url}"
        parsed = urlparse(raw_url)

    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Please provide a valid URL starting with http:// or https://")

    return raw_url


def print_header():
    print("\n🔗 SecureLink CLI URL Shortener")
    print("=" * 60)


def print_success(summary: dict):
    print("\n✅ URL Shortened Successfully!")
    print("-" * 60)
    print(f"Original URL:    {summary['original_url']}")
    print(f"Short Code:      {summary['short_code']}")
    print(f"Short URL:       {summary['short_url']}")
    print(f"Risk Score:      {summary['risk_score']}/100")
    print(f"Classification:  {summary['classification']}")
    print(f"Stored in DB id: {summary['id']}")
    print("-" * 60)

    if summary.get("details"):
        print("Security details:")
        for key, value in summary["details"].items():
            print(f"  {key}: {value}")
    print()


async def shorten_url(original_url: str, custom_alias: str = None, dry_run: bool = False):
    original_url = normalize_url(original_url)

    if custom_alias:
        custom_alias = custom_alias.strip()
        if not custom_alias:
            custom_alias = None

    if custom_alias:
        print(f"Using custom alias: {custom_alias}")
    else:
        print("Generating a short code...")

    analysis = analyze_url(original_url)
    short_code = custom_alias

    if not short_code:
        client = AsyncIOMotorClient(settings.MONGO_URI)
        urls_collection = client[settings.DB_NAME]["urls"]
        for _ in range(10):
            candidate = generate_short_code()
            if not await urls_collection.find_one({"short_code": candidate}):
                short_code = candidate
                break
        client.close()

        if not short_code:
            raise RuntimeError("Unable to generate a unique short code.")

    if dry_run:
        summary = {
            "original_url": original_url,
            "short_code": short_code,
            "short_url": f"{settings.BASE_URL}/r/{short_code}",
            "risk_score": analysis["risk_score"],
            "classification": analysis["classification"],
            "details": analysis["details"],
            "id": "dry-run",
        }
        print_success(summary)
        return summary

    client = AsyncIOMotorClient(settings.MONGO_URI)
    urls_collection = client[settings.DB_NAME]["urls"]

    if custom_alias:
        existing = await urls_collection.find_one({"short_code": custom_alias})
        if existing:
            client.close()
            raise ValueError(f"Alias '{custom_alias}' is already taken.")

    doc = {
        "original_url": original_url,
        "short_code": short_code,
        "risk_score": analysis["risk_score"],
        "classification": analysis["classification"],
        "analysis_details": analysis["details"],
        "status": "active",
        "clicks": 0,
        "created_at": datetime.now(timezone.utc),
        "expires_at": None,
        "qr_path": None,
    }

    result = await urls_collection.insert_one(doc)
    created = await urls_collection.find_one({"_id": result.inserted_id})
    client.close()

    created = serialize_doc(created)
    summary = {
        "original_url": created["original_url"],
        "short_code": created["short_code"],
        "short_url": f"{settings.BASE_URL}/r/{created['short_code']}",
        "risk_score": created["risk_score"],
        "classification": created["classification"],
        "details": analysis["details"],
        "id": created["_id"],
    }

    print_success(summary)
    return summary


async def main():
    parser = argparse.ArgumentParser(description="SecureLink terminal URL shortener")
    parser.add_argument("url", nargs="?", help="URL to shorten")
    parser.add_argument("--alias", "-a", help="Custom short code alias")
    parser.add_argument("--dry-run", action="store_true", help="Show the result without saving to MongoDB")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show analysis details")
    args = parser.parse_args()

    print_header()

    try:
        if not args.url:
            args.url = input("Enter URL to shorten: ").strip()
            if not args.url:
                raise ValueError("A URL is required.")

        summary = await shorten_url(args.url, args.alias, dry_run=args.dry_run)

        if args.verbose:
            print("Verbose mode enabled. Showing full security analysis above.")

    except ValueError as exc:
        print(f"\n❌ {exc}")
    except Exception as exc:
        print(f"\n❌ Unexpected error: {exc}")


if __name__ == "__main__":
    asyncio.run(main())
