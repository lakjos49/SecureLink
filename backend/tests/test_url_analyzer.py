"""
Unit tests for the URL security analysis engine.
Run with:  pytest tests/
"""

import pytest
from app.services.security.url_analyzer import analyze_url


def test_safe_url():
    result = analyze_url("https://www.google.com")
    assert result["risk_score"] <= 25
    assert result["classification"] == "SAFE"


def test_no_https_adds_score():
    result = analyze_url("http://example.com")
    assert result["details"]["has_https"] is False
    assert result["risk_score"] >= 10


def test_ip_address_in_url():
    result = analyze_url("http://192.168.1.1/login")
    assert result["details"]["has_ip"] is True
    assert result["risk_score"] >= 30


def test_at_symbol_in_url():
    result = analyze_url("http://legit.com@evil.com/path")
    assert result["details"]["has_at_symbol"] is True
    assert result["risk_score"] >= 25


def test_suspicious_keywords():
    result = analyze_url("https://secure-bank-login-verify.xyz/account")
    assert len(result["details"]["suspicious_keywords"]) > 0
                                                                             
    assert result["risk_score"] > 25


def test_very_long_url():
    long_url = "https://example.com/" + "a" * 90
    result = analyze_url(long_url)
    assert result["details"]["is_very_long"] is True
    assert result["risk_score"] >= 20


def test_high_risk_url():
                                                                    
    url = "http://192.168.0.1/login-bank-verify-wallet?account=update&free=reward"
    result = analyze_url(url)
    assert result["classification"] in ("SUSPICIOUS", "HIGH_RISK")
    assert result["risk_score"] >= 51


def test_classification_boundaries():
                                                               
    result = analyze_url("https://example.com")
    score = result["risk_score"]
    if score <= 25:
        assert result["classification"] == "SAFE"
    elif score <= 50:
        assert result["classification"] == "LOW_RISK"
    elif score <= 75:
        assert result["classification"] == "SUSPICIOUS"
    else:
        assert result["classification"] == "HIGH_RISK"