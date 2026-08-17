"""Small shared constants used across ranking, prefs, and the API layer."""

# Only these two countries get "national" treatment for now. Adding a
# third later means: add it here, add a source feed tagged with that
# country code, add its flag/name on the frontend.
SUPPORTED_COUNTRIES = ["in", "us"]

COUNTRY_INFO = {
    "in": {"name": "India", "flag": "\U0001F1EE\U0001F1F3"},
    "us": {"name": "United States", "flag": "\U0001F1FA\U0001F1F8"},
}

# Applies when logged out, or when a logged-in user hasn't picked any
# (valid) countries yet.
DEFAULT_COUNTRIES = ["in"]