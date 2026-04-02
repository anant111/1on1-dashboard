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


OVERALL_COLS = {
    'Total Payments': 'total_payments',
    'New Payments': 'new_payments',
    'Repeat Payments': 'repeat_payments',
    'Total Revenue': 'total_revenue',
    'New Revenue': 'new_revenue',
    'Repeat Revenue': 'repeat_revenue',
    'ARPU': 'arpu',
    'New ARPU': 'new_arpu',
    'Repeat ARPU': 'repeat_arpu',
}

PLATFORM_COLS = {
    'Total Payments': 'total_payments',
    'Web': 'web',
    'Android': 'android',
    'iOS': 'ios',
    'Total Revenue': 'total_revenue',
    'Web Rev': 'web_revenue',
    'Android Rev': 'android_revenue',
    'iOS Rev': 'ios_revenue',
    'Total ARPU': 'total_arpu',
    'Web ARPU': 'web_arpu',
    'Android ARPU': 'android_arpu',
    'iOS ARPU': 'ios_arpu',
}


def clean_df(df, tab):
    """Parse dates, convert currency columns to float, drop rows with bad dates."""
    df = df.copy()
    df['date'] = df['Date'].apply(parse_date)
    df = df[df['date'].notna()].copy()

    col_map = PLATFORM_COLS if tab == 'platform' else OVERALL_COLS
    for src, dst in col_map.items():
        if src in df.columns:
            df[dst] = df[src].apply(clean_currency)

    return df


def read_sheet(gc, sheet_name):
    """Read a Google Sheet worksheet into a DataFrame."""
    spreadsheet = gc.open_by_key(SHEET_ID)
    ws = spreadsheet.worksheet_by_title(sheet_name)
    raw = ws.get_all_values()
    headers = raw[0]
    rows = [r for r in raw[1:] if any(c.strip() for c in r)]
    return pd.DataFrame(rows, columns=headers)
