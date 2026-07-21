#!/usr/bin/env python3
"""
Validation logic for domain-suggest skill.
Handles input validation, output validation, and sanity checks.
"""

import re
from typing import Tuple, List, Dict, Any


def validate_brief_input(brief: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate that the brief contains required information.
    
    Args:
        brief: Dictionary with keys 'spec', 'trajectory', 'scope-baseline'
        
    Returns:
        Tuple of (is_valid, list_of_error_messages)
    """
    errors = []
    
    # Check that at least one of the three sections is present and non-empty
    has_content = False
    for key in ["spec", "trajectory", "scope-baseline"]:
        if key in brief:
            value = brief[key]
            if isinstance(value, str) and value.strip():
                has_content = True
                break
            elif isinstance(value, dict) and value:
                # Allow dict format too
                has_content = True
                break
    
    if not has_content:
        errors.append("Brief must contain at least one of: spec, trajectory, or scope-baseline with non-empty content")
    
    # Validate each field if present
    for key in ["spec", "trajectory", "scope-baseline"]:
        if key in brief:
            value = brief[key]
            if not isinstance(value, (str, dict)):
                errors.append(f"Field '{key}' must be a string or dictionary")
            elif isinstance(value, str) and len(value.strip()) == 0:
                # Empty string is OK - we'll check above that at least one is non-empty
                pass
    
    return len(errors) == 0, errors


def validate_output_structure(output: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate that the output matches the expected schema.
    
    Expected structure:
    {
        "status": "success" | "error",
        "artifacts": [list of strings],
        "domain_candidates": [
            {
                "domain": str (valid domain format),
                "rationale": str (non-empty),
                "availability": "available" | "unavailable" | "unknown"
            }
        ],
        "hitl_gate_required": bool,
        "hitl_gate_passed": bool
    }
    """
    errors = []
    
    # Check required top-level keys
    required_keys = ["status", "artifacts", "domain_candidates", "hitl_gate_required", "hitl_gate_passed"]
    for key in required_keys:
        if key not in output:
            errors.append(f"Missing required key: {key}")
    
    if errors:
        return False, errors
    
    # Validate status
    if output["status"] not in ["success", "error"]:
        errors.append("Status must be 'success' or 'error'")
    
    # Validate artifacts
    if not isinstance(output["artifacts"], list):
        errors.append("'artifacts' must be a list")
    else:
        for i, artifact in enumerate(output["artifacts"]):
            if not isinstance(artifact, str):
                errors.append(f"artifacts[{i}] must be a string")
    
    # Validate domain_candidates
    if not isinstance(output["domain_candidates"], list):
        errors.append("'domain_candidates' must be a list")
    else:
        if len(output["domain_candidates"]) != 3:
            errors.append(f"Expected exactly 3 domain candidates, got {len(output['domain_candidates'])}")
        
        for i, candidate in enumerate(output["domain_candidates"]):
            if not isinstance(candidate, dict):
                errors.append(f"domain_candidates[{i}] must be a dictionary")
                continue
                
            # Check required fields
            for field in ["domain", "rationale", "availability"]:
                if field not in candidate:
                    errors.append(f"domain_candidates[{i}] missing required field: {field}")
            
            if "domain" in candidate:
                domain = candidate["domain"]
                if not isinstance(domain, str):
                    errors.append(f"domain_candidates[{i}].domain must be a string")
                elif not _is_valid_domain_format(domain):
                    errors.append(f"domain_candidates[{i}].domain '{domain}' is not a valid domain format")
            
            if "rationale" in candidate:
                rationale = candidate["rationale"]
                if not isinstance(rationale, str):
                    errors.append(f"domain_candidates[{i}].rationale must be a string")
                elif len(rationale.strip()) == 0:
                    errors.append(f"domain_candidates[{i}].rationale must not be empty")
            
            if "availability" in candidate:
                avail = candidate["availability"]
                if avail not in ["available", "unavailable", "unknown"]:
                    errors.append(f"domain_candidates[{i}].availability must be 'available', 'unavailable', or 'unknown', got '{avail}'")
    
    # Validate HITL fields
    if not isinstance(output["hitl_gate_required"], bool):
        errors.append("'hitl_gate_required' must be a boolean")
    
    if not isinstance(output["hitl_gate_passed"], bool):
        errors.append("'hitl_gate_passed' must be a boolean")
    
    return len(errors) == 0, errors


def _is_valid_domain_format(domain: str) -> bool:
    """Check if a string looks like a valid domain name."""
    if not isinstance(domain, str) or len(domain) == 0:
        return False
    
    # Domain should consist of labels separated by dots
    # Each label: 1-63 chars, alphanumeric and hyphens, not starting/ending with hyphen
    # TLD should be all letters (we're lenient about this)
    
    # Split into labels
    labels = domain.split(".")
    if len(labels) < 2:
        return False  # Need at least domain.tld
    
    # Check each label
    for label in labels:
        if len(label) == 0 or len(label) > 63:
            return False
        if not re.match(r'^[a-z0-9]([a-z0-9\-]*[a-z0-9])?$', label, re.IGNORECASE):
            return False
        if label.startswith('-') or label.endswith('-'):
            return False
    
    return True


def validate_no_fabrication(output: Dict[str, Any], input_brief: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Check that the output doesn't contain fabricated specific details.
    Specifically, availability status should not claim certainty without evidence,
    and rationales should not invent specific registration dates, prices, etc.
    """
    errors = []
    warnings = []
    
    if "domain_candidates" not in output:
        return True, []  # Skip if structure is wrong (will be caught elsewhere)
    
    for i, candidate in enumerate(output["domain_candidates"]):
        if not isinstance(candidate, dict):
            continue
            
        availability = candidate.get("availability", "")
        rationale = candidate.get("rationale", "")
        
        # Check for obviously fabricated specifics in rationale
        forbidden_patterns = [
            r"registered on\s+\d{4}-\d{2}-\d{2}",  # specific dates
            r"expires\s+\d{4}-\d{2}-\d{2}",
            r"costs?\s*\$\d+",  # specific prices
            r"price\s*:?\s*\$", 
            r"registrar\s+[A-Z][a-z]+",  # specific registrar names (unless generic)
            r"whois\s+record\s+shows",  # claiming to have seen specific whois data
            r"created\s+\d{4}-\d{2}-\d{2}",  # creation dates
            r"updated\s+\d{4}-\d{2}-\d{2}",  # update dates
        ]
        
        for pattern in forbidden_patterns:
            if re.search(pattern, rationale, re.IGNORECASE):
                errors.append(f"domain_candidates[{i}].rationale appears to contain fabricated specifics: {pattern}")
        
        # If availability is claimed as available/unavailable, the rationale should not
        # assert specific knowledge we couldn't have obtained
        if availability in ["available", "unavailable"]:
            # Check for overly specific claims
            specific_claims = [
                r"registered\s+to\s+[A-Z][a-z]+",  # registered to specific entity
                r"expires\s+in\s+\d+\s+days",
                r"last\s+updated\s+\d{4}-\d{2}-\d{2}",
                r"created\s+\d{4}-\d{2}-\d{2}",
            ]
            for pattern in specific_claims:
                if re.search(pattern, rationale, re.IGNORECASE):
                    warnings.append(f"domain_candidates[{i}].rationale may contain overly specific claims: {pattern}")
    
    # If there are errors, return False; warnings don't fail validation
    return len(errors) == 0, errors


def sanitize_output_for_unknowns(output: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure that unknown information is represented as TODO: rather than fabricated.
    Specifically, if availability is unknown, the rationale should reflect uncertainty.
    """
    if "domain_candidates" not in output:
        return output
    
    for candidate in output["domain_candidates"]:
        if not isinstance(candidate, dict):
            continue
            
        availability = candidate.get("availability", "")
        rationale = candidate.get("rationale", "")
        
        # If availability is unknown, ensure rationale doesn't claim certainty
        if availability == "unknown":
            # If rationale doesn't already indicate uncertainty, add a note
            if not any(word in rationale.lower() for word in ["unknown", "uncertain", "check", "verify", "todo"]):
                # Append a note about needing verification
                if rationale.endswith("."):
                    rationale = rationale[:-1] + ". Availability should be verified via manual whois/RDAP check."
                else:
                    rationale = rationale + ". Availability should be verified via manual whois/RDAP check."
                candidate["rationale"] = rationale
    
    return output


if __name__ == "__main__":
    # Simple test
    test_brief = {
        "spec": "Test project for bamboo supply chain tracking",
        "trajectory": "MVP -> Beta -> Launch",
        "scope-baseline": "Track bamboo lots with basic ESG metrics"
    }
    
    is_valid, errors = validate_brief_input(test_brief)
    print(f"Brief validation: {'PASS' if is_valid else 'FAIL'}")
    if errors:
        print("Errors:", errors)
    
    test_output = {
        "status": "success",
        "artifacts": ["domain-recommendations.md"],
        "domain_candidates": [
            {
                "domain": "bamboooo.com",
                "rationale": "Available, short, memorable, .com TLD preferred",
                "availability": "available"
            },
            {
                "domain": "bamboo-track.org",
                "rationale": "Contains relevant keyword, .org suitable for ESG focus",
                "availability": "unavailable"
            },
            {
                "domain": "eco-bamboo.dev",
                "rationale": "Availability unknown - requires manual check",
                "availability": "unknown"
            }
        ],
        "hitl_gate_required": False,
        "hitl_gate_passed": True
    }
    
    is_valid, errors = validate_output_structure(test_output)
    print(f"Output validation: {'PASS' if is_valid else 'FAIL'}")
    if errors:
        print("Errors:", errors)
    
    is_fabricated, fab_errors = validate_no_fabrication(test_output, test_brief)
    print(f"No fabrication check: {'PASS' if is_fabricated else 'FAIL'}")
    if not is_fabricated:
        print("Fabrication errors:", fab_errors)