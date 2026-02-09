"""Utility functions for extracting conference/venue information from Semantic Scholar data"""
from typing import Optional


def extract_conference_from_ss_data(data: dict) -> Optional[str]:
    """
    Extract conference abbreviation from Semantic Scholar API response.

    Args:
        data: Semantic Scholar API response containing venue/publicationVenue/year fields

    Returns:
        Conference string with year suffix (e.g., "KDD'23", "NeurIPS'24") or None
    """
    year = data.get("year")
    year_suffix = f"'{str(year)[-2:]}" if year else ""

    # Try publicationVenue first - prefer abbreviation from alternate_names
    pub_venue = data.get("publicationVenue")
    if pub_venue:
        # Look for short uppercase abbreviations (e.g., "KDD", "WWW", "ICML")
        alt_names = pub_venue.get("alternate_names", [])
        for name in alt_names:
            if name.isupper() and len(name) <= 10:
                return f"{name}{year_suffix}"
        # Fall back to first alternate name or full name
        if alt_names:
            return f"{alt_names[0]}{year_suffix}"
        if pub_venue.get("name"):
            return f"{pub_venue['name']}{year_suffix}"

    # Fall back to venue string
    venue = data.get("venue")
    if venue and venue.lower() not in ("arxiv", "arxiv.org"):
        return f"{venue}{year_suffix}"

    return None
