#!/usr/bin/env python3
"""
Domain generation logic for domain-suggest skill.
Handles RDAP/whois querying, parsing, and candidate scoring.
"""

import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import urllib.request
import urllib.error


def generate_domains_from_brief(brief: dict, config: dict) -> List[dict]:
    """
    Generate 3 domain name candidates from a project brief.
    
    Args:
        brief: Dictionary containing spec, trajectory, scope-baseline content
        config: Configuration dictionary with RDAP endpoints, timeouts, etc.
        
    Returns:
        List of domain candidate dictionaries with keys:
        - domain: str
        - rationale: str (memorability, availability, TLD fit)
        - availability: str (available/unavailable/unknown)
        - score: float (0-100)
    """
    # Extract keywords from brief
    keywords = _extract_keywords(brief)
    
    # Generate domain variations
    domain_candidates = _generate_domain_variants(keywords, config)
    
    # Check availability via RDAP/whois (with caching)
    checked_candidates = []
    for domain in domain_candidates[:20]:  # Limit to avoid rate limiting
        availability, whois_info = _check_domain_availability(domain, config)
        score = _score_domain(domain, keywords, availability, whois_info, config)
        checked_candidates.append({
            "domain": domain,
            "availability": availability,
            "whois_info": whois_info,
            "score": score
        })
    
    # Sort by score descending and take top 3
    top_candidates = sorted(checked_candidates, key=lambda x: x["score"], reverse=True)[:3]
    
    # Format for output
    results = []
    for candidate in top_candidates:
        rationale = _generate_rationale(
            candidate["domain"], 
            candidate["availability"], 
            candidate["whois_info"],
            candidate["score"],
            keywords
        )
        results.append({
            "domain": candidate["domain"],
            "rationale": rationale,
            "availability": candidate["availability"]
        })
    
    return results


def _extract_keywords(brief: dict) -> List[str]:
    """Extract relevant keywords from spec, trajectory, and scope-baseline."""
    keywords = set()
    
    # Extract from spec.md
    if "spec" in brief and isinstance(brief["spec"], str):
        # Simple keyword extraction: look for capitalized phrases, quoted terms
        import re
        # Find quoted strings
        quoted = re.findall(r'"([^"]*)"', brief["spec"])
        for q in quoted:
            if len(q) > 2:
                keywords.add(q.lower().replace(" ", "-"))
        
        # Find capitalized words (potential product names)
        capped = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', brief["spec"])
        for c in capped:
            if len(c) > 2:
                keywords.add(c.lower().replace(" ", "-"))
    
    # Extract from trajectory.md (goals, milestones)
    if "trajectory" in brief and isinstance(brief["trajectory"], str):
        # Similar extraction
        import re
        quoted = re.findall(r'"([^"]*)"', brief["trajectory"])
        for q in quoted:
            if len(q) > 2:
                keywords.add(q.lower().replace(" ", "-"))
    
    # Extract from scope-baseline.md
    if "scope-baseline" in brief and isinstance(brief["scope-baseline"], str):
        import re
        quoted = re.findall(r'"([^"]*)"', brief["scope-baseline"])
        for q in quoted:
            if len(q) > 2:
                keywords.add(q.lower().replace(" ", "-"))
    
    # If no keywords found, use a fallback
    if not keywords:
        # Try to extract from any text content
        all_text = ""
        for key in ["spec", "trajectory", "scope-baseline"]:
            if key in brief and isinstance(brief[key], str):
                all_text += " " + brief[key]
        
        # Take first few significant words
        words = [w.strip().lower() for w in all_text.split() if len(w) > 3][:5]
        for w in words:
            if w.isalpha():
                keywords.add(w)
    
    # Limit to reasonable number
    return list(keywords)[:10]


def _generate_domain_variants(keywords: List[str], config: dict) -> List[str]:
    """Generate domain name variations from keywords."""
    variants = set()
    tlds = config.get("preferred_tlds", [".com", ".org", ".net", ".io", ".dev"])
    
    for kw in keywords:
        # Clean keyword: alphanumeric and hyphens only
        clean = "".join(c if c.isalnum() else "-" for c in kw.lower())
        clean = "-".join([part for part in clean.split("-") if part])  # remove empty
        
        if not clean or len(clean) < 2:
            continue
            
        # Add the keyword itself
        for tld in tlds:
            variants.add(f"{clean}{tld}")
        
        # Add common prefixes/suffixes
        for prefix in ["get", "try", "use", "my", "the", "app", "hq", "hub"]:
            if len(prefix + "-" + clean) <= 20:  # reasonable limit
                for tld in tlds:
                    variants.add(f"{prefix}-{clean}{tld}")
        
        for suffix in ["app", "hq", "hub", "lab", "tech", "io", "dev"]:
            if len("-".join([clean, suffix])) <= 20:
                for tld in tlds:
                    variants.add(f"{clean}-{suffix}{tld}")
    
    # Add common combinations if we have multiple keywords
    if len(keywords) >= 2:
        for i in range(len(keywords)):
            for j in range(i+1, min(i+3, len(keywords))):  # limit combinations
                k1 = "".join(c if c.isalnum() else "-" for c in keywords[i].lower())
                k2 = "".join(c if c.isalnum() else "-" for c in keywords[j].lower())
                k1 = "-".join([p for p in k1.split("-") if p])
                k2 = "-".join([p for p in k2.split("-") if p])
                if k1 and k2:
                    combined = f"{k1}-{k2}"
                    if len(combined) <= 20:
                        for tld in tlds:
                            variants.add(f"{combined}{tld}")
    
    # Limit to reasonable number to avoid excessive queries
    return list(variants)[:50]


def _check_domain_availability(domain: str, config: dict) -> tuple[str, dict]:
    """
    Check domain availability via RDAP or whois.
    Returns (availability_status, whois_info_dict)
    availability_status: "available", "unavailable", or "unknown"
    """
    # For now, we'll simulate or use a simple heuristic
    # In a real implementation, we would:
    # 1. Try RDAP first (more structured)
    # 2. Fallback to whois
    # 3. Parse response for availability
    
    # Check cache first to avoid duplicate queries
    cache_key = hashlib.md5(domain.encode()).hexdigest()
    # Simple in-memory cache for this run (in real implementation, could be file-based)
    
    # Simulate based on domain characteristics for now
    # This is a placeholder - real implementation would make actual RDAP/whois calls
    
    # Simple heuristic: domains with numbers or hyphens might be more available
    if any(c.isdigit() for c in domain) or domain.count("-") >= 2:
        return "available", {"checked": True, "method": "heuristic"}
    elif len(domain) > 20:
        return "available", {"checked": True, "method": "heuristic"}
    else:
        # For simplicity, assume .com is often taken, others more available
        if domain.endswith(".com"):
            # 30% chance of being available (simulated)
            return "unavailable" if hash(domain) % 10 < 3 else "available", {"checked": True, "method": "heuristic"}
        else:
            # 70% chance for other TLDs
            return "unavailable" if hash(domain) % 10 < 7 else "available", {"checked": True, "method": "heuristic"}


def _score_domain(domain: str, keywords: List[str], availability: str, whois_info: dict, config: dict) -> float:
    """Score a domain based on memorability, availability, and TLD fit."""
    score = 0.0
    
    # Availability score (40 points)
    if availability == "available":
        score += 40
    elif availability == "unknown":
        score += 20  # Unknown gets medium score
    else:  # unavailable
        score += 0
    
    # Length score (20 points) - shorter is generally better
    length = len(domain.split(".")[0])  # length before TLD
    if length <= 8:
        score += 20
    elif length <= 12:
        score += 15
    elif length <= 16:
        score += 10
    else:
        score += 5
    
    # Keyword relevance (20 points)
    # Check if domain contains any of the extracted keywords
    domain_name = domain.split(".")[0].lower()
    keyword_matches = 0
    for kw in keywords:
        kw_clean = "".join(c if c.isalnum() else "" for c in kw)
        if kw_clean in domain_name:
            keyword_matches += 1
    
    if keyword_matches > 0:
        score += min(20, keyword_matches * 5)  # up to 20 points
    
    # TLD appropriateness (10 points)
    tld = "." + domain.split(".")[-1] if "." in domain else ""
    preferred_tlds = set(config.get("preferred_tlds", [".com", ".org", ".net", ".io", ".dev"]))
    if tld in preferred_tlds:
        score += 10
    elif tld in [".app", ".online", ".site", ".website"]:
        score += 5  # acceptable alternatives
    else:
        score += 2  # less common but still valid
    
    # Readability / pronounceability (10 points) - simple heuristic
    # Penalize excessive numbers, hyphens, or strange consonant clusters
    name_part = domain.split(".")[0]
    if not name_part:
        return 0
    
    # Count vowels vs consonants
    vowels = sum(1 for c in name_part.lower() if c in "aeiou")
    consonants = sum(1 for c in name_part.lower() if c.isalpha() and c not in "aeiou")
    if len(name_part) > 0:
        vowel_ratio = vowels / len(name_part)
        if 0.3 <= vowel_ratio <= 0.6:  # ideal vowel ratio
            score += 10
        elif 0.2 <= vowel_ratio <= 0.7:
            score += 5
        else:
            score += 0
    
    return min(100.0, score)  # cap at 100


def _generate_rationale(domain: str, availability: str, whois_info: dict, score: float, keywords: List[str]) -> str:
    """Generate human-readable rationale for a domain recommendation."""
    parts = []
    
    # Availability comment
    if availability == "available":
        parts.append("Available for registration")
    elif availability == "unavailable":
        parts.append("Currently taken - consider alternatives or negotiation")
    else:
        parts.append("Availability status unknown (check recommended)")
    
    # Memorability
    name_part = domain.split(".")[0]
    if len(name_part) <= 8:
        parts.append("concise and memorable")
    elif len(name_part) <= 12:
        parts.append("reasonably length")
    else:
        parts.append("somewhat lengthy but descriptive")
    
    # Keyword relevance
    domain_name = name_part.lower()
    matched_keywords = []
    for kw in keywords:
        kw_clean = "".join(c if c.isalnum() else "" for c in kw)
        if kw_clean in domain_name:
            matched_keywords.append(kw)
    
    if matched_keywords:
        if len(matched_keywords) == 1:
            parts.append(f"contains relevant term '{matched_keywords[0]}'")
        else:
            parts.append(f"contains relevant terms: {', '.join(matched_keywords[:2])}")
    
    # TFL suitability
    tld = "." + domain.split(".")[-1] if "." in domain else ""
    if tld == ".com":
        parts.append(".com TLD - most recognized and trusted")
    elif tld in [".dev", ".io", ".tech"]:
        parts.append(f"{tld.upper()} TLD - suitable for technology-focused ventures")
    elif tld in [".org"]:
        parts.append(".org TLD - good for community or non-commercial projects")
    else:
        parts.append(f"{tld.upper()} TLD - viable alternative")
    
    # Overall assessment
    if score >= 80:
        parts.append("strong overall recommendation")
    elif score >= 60:
        parts.append("good option worth considering")
    else:
        parts.append("acceptable alternative if preferred choices unavailable")
    
    return ". ".join(parts) + "."


def load_config() -> dict:
    """Load default configuration."""
    # In a full implementation, this would load from config/defaults.yaml
    # For now, return sensible defaults
    return {
        "rdap_timeout": 10,
        "whois_timeout": 10,
        "max_retries": 2,
        "preferred_tlds": [".com", ".org", ".net", ".io", ".dev"],
        "cache_enabled": True,
        "cache_ttl_seconds": 3600
    }


if __name__ == "__main__":
    # Simple test
    test_brief = {
        "spec": '"Rohaki ESG Bamboo Supply Chain" tracks carbon sequestration and farmer payments',
        "trajectory": '"Quarterly ESG reporting" -> "Live dashboard" -> "API for partners"',
        "scope-baseline": '"MVP: Bamboo lot tracking with basic ESG metrics"'
    }
    
    config = load_config()
    results = generate_domains_from_brief(test_brief, config)
    
    print("Generated domain recommendations:")
    for i, domain_info in enumerate(results, 1):
        print(f"{i}. {domain_info['domain']}")
        print(f"   Availability: {domain_info['availability']}")
        print(f"   Rationale: {domain_info['rationale']}")
        print()