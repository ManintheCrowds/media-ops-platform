"""Shared job-source names for search and scheduled runs."""

# Adzuna stays listed so existing callers keep working. USAJOBS and The Muse
# are the official API sources that replace it when Adzuna is unset.
DEFAULT_SEARCH_SOURCES = [
    "adzuna",
    "indeed",
    "linkedin",
    "glassdoor",
    "ziprecruiter",
    "the_muse",
    "usajobs",
]

# These sources must use their official APIs. Never fall through to scraping.
OFFICIAL_API_SOURCES = frozenset({"the_muse", "usajobs"})
