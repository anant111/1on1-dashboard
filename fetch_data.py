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


def daily_records(df, tab):
    """Convert cleaned DataFrame rows to list of dicts for daily granularity."""
    records = []
    for _, row in df.iterrows():
        r = {'date': row['date'].isoformat()}
        if tab == 'platform':
            tp = row['total_payments']
            w, a, i = row['web'], row['android'], row['ios']
            r.update({
                'total_payments': int(tp),
                'web': int(w), 'android': int(a), 'ios': int(i),
                'web_pct': safe_div(w * 100, tp),
                'android_pct': safe_div(a * 100, tp),
                'ios_pct': safe_div(i * 100, tp),
                'total_revenue': row['total_revenue'],
                'web_revenue': row['web_revenue'],
                'android_revenue': row['android_revenue'],
                'ios_revenue': row['ios_revenue'],
                'total_arpu': safe_div(row['total_revenue'], tp),
                'web_arpu': safe_div(row['web_revenue'], w),
                'android_arpu': safe_div(row['android_revenue'], a),
                'ios_arpu': safe_div(row['ios_revenue'], i),
            })
        else:
            tp = row['total_payments']
            np_ = row['new_payments']
            rp = row['repeat_payments']
            r.update({
                'total_payments': int(tp),
                'new_payments': int(np_),
                'repeat_payments': int(rp),
                'new_pct': safe_div(np_ * 100, tp),
                'repeat_pct': safe_div(rp * 100, tp),
                'total_revenue': row['total_revenue'],
                'new_revenue': row['new_revenue'],
                'repeat_revenue': row['repeat_revenue'],
                'arpu': safe_div(row['total_revenue'], tp),
                'new_arpu': safe_div(row['new_revenue'], np_),
                'repeat_arpu': safe_div(row['repeat_revenue'], rp),
            })
        records.append(r)
    return records


def aggregate(df, period, tab):
    """Aggregate df by 'weekly' or 'monthly', recalculating derived fields."""
    df = df.copy()
    df['_period'] = pd.to_datetime(df['date']).dt.to_period(
        'W' if period == 'weekly' else 'M'
    )

    if tab == 'platform':
        sum_cols = ['total_payments', 'web', 'android', 'ios',
                    'total_revenue', 'web_revenue', 'android_revenue', 'ios_revenue']
        grouped = df.groupby('_period')[sum_cols].sum().reset_index()
        records = []
        for _, row in grouped.iterrows():
            tp = row['total_payments']
            w, a, i = row['web'], row['android'], row['ios']
            period_date = row['_period'].to_timestamp().date()
            records.append({
                'date': period_date.isoformat(),
                'total_payments': int(tp),
                'web': int(w), 'android': int(a), 'ios': int(i),
                'web_pct': safe_div(w * 100, tp),
                'android_pct': safe_div(a * 100, tp),
                'ios_pct': safe_div(i * 100, tp),
                'total_revenue': row['total_revenue'],
                'web_revenue': row['web_revenue'],
                'android_revenue': row['android_revenue'],
                'ios_revenue': row['ios_revenue'],
                'total_arpu': safe_div(row['total_revenue'], tp),
                'web_arpu': safe_div(row['web_revenue'], w),
                'android_arpu': safe_div(row['android_revenue'], a),
                'ios_arpu': safe_div(row['ios_revenue'], i),
            })
        return records
    else:
        sum_cols = ['total_payments', 'new_payments', 'repeat_payments',
                    'total_revenue', 'new_revenue', 'repeat_revenue']
        grouped = df.groupby('_period')[sum_cols].sum().reset_index()
        records = []
        for _, row in grouped.iterrows():
            tp = row['total_payments']
            np_ = row['new_payments']
            rp = row['repeat_payments']
            period_date = row['_period'].to_timestamp().date()
            records.append({
                'date': period_date.isoformat(),
                'total_payments': int(tp),
                'new_payments': int(np_),
                'repeat_payments': int(rp),
                'new_pct': safe_div(np_ * 100, tp),
                'repeat_pct': safe_div(rp * 100, tp),
                'total_revenue': row['total_revenue'],
                'new_revenue': row['new_revenue'],
                'repeat_revenue': row['repeat_revenue'],
                'arpu': safe_div(row['total_revenue'], tp),
                'new_arpu': safe_div(row['new_revenue'], np_),
                'repeat_arpu': safe_div(row['repeat_revenue'], rp),
            })
        return records


def build_tab_data(df, tab):
    return {
        'daily':   daily_records(df, tab),
        'weekly':  aggregate(df, 'weekly', tab),
        'monthly': aggregate(df, 'monthly', tab),
    }


def read_sheet(gc, sheet_name):
    """Read a Google Sheet worksheet into a DataFrame."""
    spreadsheet = gc.open_by_key(SHEET_ID)
    ws = spreadsheet.worksheet_by_title(sheet_name)
    raw = ws.get_all_values()
    headers = raw[0]
    rows = [r for r in raw[1:] if any(c.strip() for c in r)]
    return pd.DataFrame(rows, columns=headers)


def git_push(repo_dir):
    today = date.today().isoformat()
    subprocess.run(['git', 'add', 'data.json'], cwd=repo_dir, check=True)
    result = subprocess.run(
        ['git', 'commit', '-m', f'Update dashboard data {today}'],
        cwd=repo_dir, capture_output=True, text=True
    )
    if result.returncode != 0:
        if 'nothing to commit' in result.stdout + result.stderr:
            print("data.json unchanged, nothing to commit")
            return
        raise subprocess.CalledProcessError(result.returncode, 'git commit')
    push_result = subprocess.run(['git', 'push'], cwd=repo_dir, capture_output=True, text=True)
    if push_result.returncode != 0:
        print(f"Warning: git push failed (remote may not be configured yet): {push_result.stderr.strip()}")
    else:
        print("Pushed to GitHub")


def main():
    gc = pygsheets.authorize(service_file=CREDS_FILE)
    spreadsheet = gc.open_by_key(SHEET_ID)

    result = {'last_updated': date.today().isoformat()}

    for tab, sheet_name in SHEET_NAMES.items():
        ws = spreadsheet.worksheet_by_title(sheet_name)
        raw = ws.get_all_values()
        headers = raw[0]
        rows = [r for r in raw[1:] if any(c.strip() for c in r)]
        df = pd.DataFrame(rows, columns=headers)
        df = clean_df(df, tab)
        result[tab] = build_tab_data(df, tab)

    with open(DATA_FILE, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"Written {DATA_FILE}")

    try:
        git_push(REPO_DIR)
    except Exception as e:
        print(f"Warning: git operations failed: {e}")


if __name__ == '__main__':
    main()
