import pygsheets
import pandas as pd
import json
import subprocess
import warnings
from datetime import datetime, date
import os

warnings.filterwarnings('ignore')

SHEET_ID = "1wUwgXEnMKJSbXR90j7KyM0LM5M40E5gvTwoU0fb5M3E"
CREDS_FILE = "/Users/anant/Documents/Rails/gsheet_cred.json"
REPO_DIR = "/Users/anant/Documents/1 on 1 dashboard"
DATA_FILE = os.path.join(REPO_DIR, "data.json")

SHEET_NAMES = {
    "overall":  "1 on 1 Overall",
    "web":      "1 on 1 Web",
    "ios":      "1 on 1 iOS",
    "android":  "1 on 1 Android",
    "platform": "1 on 1 Platform wise",
}


def clean_currency(val):
    """Strip ₹ and commas, return float. Returns 0.0 for empty/invalid."""
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).replace('₹', '').replace(',', '').strip()
    return float(s) if s else 0.0


def parse_date(val):
    """Parse date string in multiple formats. Returns date or None."""
    for fmt in ('%d-%b-%y', '%d/%m/%Y', '%Y-%m-%d'):
        try:
            return datetime.strptime(str(val).strip(), fmt).date()
        except ValueError:
            continue
    return None


def safe_div(num, denom):
    """Divide, returning 0.0 if denominator is zero."""
    return round(float(num) / float(denom), 2) if denom else 0.0
