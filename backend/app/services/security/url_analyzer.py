"""
URL Security Analysis Engine
=============================
Analyzes a URL and returns a risk score (0–100) and classification label.

Scoring weights
---------------
No HTTPS               +10
Contains IP address    +30
Contains @ symbol      +25
Suspicious keyword     +15 each (capped at 30)
Very long URL (>100)   +20
High dot count (>4)    +10
High hyphen count (>3) +10
High digit ratio (>30%)+10
High entropy (>4.5)    +15
"""

import re
import math
from urllib.parse import urlparse


SUSPICIOUS_KEYWORDS = [
    "login", "verify", "bank", "wallet", "secure", "account",
    "payment", "bonus", "gift", "crypto", "free", "reward",
]

                                      
IP_PATTERN = re.compile(
    r"^(\d{1,3}\.){3}\d{1,3}$"
)


def _shannon_entropy(text: str) -> float:
    """Calculate Shannon entropy of a string."""
    if not text:
        return 0.0
    freq = {}
    for ch in text:
        freq[ch] = freq.get(ch, 0) + 1
    length = len(text)
    return -sum((c / length) * math.log2(c / length) for c in freq.values())


def analyze_url(url: str) -> dict:
    """
    Analyze a URL for security risk.

    Parameters
    ----------
    url : str
        The raw URL string submitted by the user.

    Returns
    -------
    dict
        {
            "risk_score": int,          # 0–100
            "classification": str,      # SAFE | LOW_RISK | SUSPICIOUS | HIGH_RISK
            "details": dict             # breakdown of every feature checked
        }
    """
    score = 0
    details = {}

    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    path_and_query = (parsed.path or "") + (parsed.query or "")
    full_url_lower = url.lower()

                                                                               
    has_https = parsed.scheme == "https"
    if not has_https:
        score += 10
    details["has_https"] = has_https

                                                                                
    has_ip = bool(IP_PATTERN.match(hostname))
    if has_ip:
        score += 30
    details["has_ip"] = has_ip

                                                                                
    has_at = "@" in url
    if has_at:
        score += 25
    details["has_at_symbol"] = has_at

                                                                                
    found_keywords = [kw for kw in SUSPICIOUS_KEYWORDS if kw in full_url_lower]
    keyword_penalty = min(len(found_keywords) * 15, 30)
    score += keyword_penalty
    details["suspicious_keywords"] = found_keywords
    details["keyword_penalty"] = keyword_penalty

                                                                                
    url_length = len(url)
    is_very_long = url_length > 100
    if is_very_long:
        score += 20
    details["url_length"] = url_length
    details["is_very_long"] = is_very_long

                                                                                
    dot_count = hostname.count(".")
    if dot_count > 4:
        score += 10
    details["dot_count"] = dot_count

                                                                                
    hyphen_count = hostname.count("-")
    if hyphen_count > 3:
        score += 10
    details["hyphen_count"] = hyphen_count

                                                                                
    digit_count = sum(c.isdigit() for c in url)
    digit_ratio = (digit_count / len(url) * 100) if url else 0
    if digit_ratio > 30:
        score += 10
    details["digit_count"] = digit_count
    details["digit_ratio_pct"] = round(digit_ratio, 2)

                                                                                
    entropy = _shannon_entropy(path_and_query)
    if entropy > 4.5:
        score += 15
    details["entropy"] = round(entropy, 4)

                                                                                
    risk_score = min(score, 100)

    if risk_score <= 25:
        classification = "SAFE"
    elif risk_score <= 50:
        classification = "LOW_RISK"
    elif risk_score <= 75:
        classification = "SUSPICIOUS"
    else:
        classification = "HIGH_RISK"

    return {
        "risk_score": risk_score,
        "classification": classification,
        "details": details,
    }