# 1on1 Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a dark, sidebar-nav dashboard (GitHub Pages) showing 1on1 payment data from Google Sheets, with a Python cron script that fetches/processes the data and pushes `data.json` to the repo.

**Architecture:** `fetch_data.py` reads 5 Google Sheet tabs via pygsheets, aggregates to daily/weekly/monthly with derived fields recalculated (not summed), writes `data.json`. `index.html` (Chart.js, dark theme) loads `data.json` and renders KPI cards + charts across Overview / Web / iOS / Android / Platform sections with a granularity toggle.

**Tech Stack:** Python 3.9, pygsheets, pandas, Chart.js 4 (CDN), vanilla JS, GitHub Pages

---

## File Map

| File | Role |
|------|------|
| `fetch_data.py` | Data pipeline: read sheet → clean → aggregate → write data.json → git push |
| `data.json` | Generated data file committed to repo, loaded by index.html at runtime |
| `index.html` | Static dashboard: sidebar nav, KPI cards, Chart.js charts |
| `requirements.txt` | Python dependencies |
| `tests/test_fetch.py` | Unit tests for cleaning and aggregation logic |
| `.gitignore` | Exclude creds, venv, pycache |

---

## Task 1: Project Scaffold

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create requirements.txt**

```
pygsheets
pandas
```

- [ ] **Step 2: Create .gitignore**

```
*.json.bak
__pycache__/
*.pyc
.env
venv/
gsheet_cred.json
.DS_Store
```

- [ ] **Step 3: Create tests/__init__.py**

Empty file:
```python
```

- [ ] **Step 4: Install dependencies**

```bash
pip install pygsheets pandas pytest
```

Expected: installs without errors.

- [ ] **Step 5: Commit scaffold**

```bash
git add requirements.txt .gitignore tests/
git commit -m "chore: project scaffold"
```

---

## Task 2: Data Cleaning Functions + Tests

**Files:**
- Create: `fetch_data.py` (partial — cleaning functions only)
- Create: `tests/test_fetch.py`

- [ ] **Step 1: Write failing tests for `clean_currency` and `parse_date`**

Create `tests/test_fetch.py`:

```python
import pytest
from fetch_data import clean_currency, parse_date
from datetime import date

def test_clean_currency_with_rupee_symbol():
    assert clean_currency('₹4,200') == 4200.0

def test_clean_currency_with_decimal():
    assert clean_currency('₹4,666.33') == 4666.33

def test_clean_currency_zero():
    assert clean_currency('₹0') == 0.0

def test_clean_currency_plain_number():
    assert clean_currency('2000') == 2000.0

def test_clean_currency_empty():
    assert clean_currency('') == 0.0

def test_parse_date_day_mon_year():
    assert parse_date('13-May-25') == date(2025, 5, 13)

def test_parse_date_slash_format():
    assert parse_date('13/05/2025') == date(2025, 5, 13)

def test_parse_date_iso():
    assert parse_date('2025-05-13') == date(2025, 5, 13)

def test_parse_date_invalid():
    assert parse_date('not a date') is None
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_fetch.py -v
```

Expected: `ModuleNotFoundError: No module named 'fetch_data'`

- [ ] **Step 3: Create fetch_data.py with cleaning functions**

Create `fetch_data.py`:

```python
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
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
pytest tests/test_fetch.py -v
```

Expected: 9 tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add fetch_data.py tests/test_fetch.py
git commit -m "feat: data cleaning functions with tests"
```

---

## Task 3: Sheet Reading + DataFrame Cleaning

**Files:**
- Modify: `fetch_data.py` (add `clean_df`, `read_sheet`)
- Modify: `tests/test_fetch.py` (add DataFrame cleaning tests)

- [ ] **Step 1: Write failing tests for `clean_df`**

Add to `tests/test_fetch.py`:

```python
import pandas as pd
from fetch_data import clean_df

def _make_overall_df():
    return pd.DataFrame([
        {
            'Date': '13-May-25',
            'Total Payments': '2', 'New Payments': '2', 'Repeat Payments': '0',
            'New %': '100.00%', 'Repeat %': '0.00%',
            'Total Revenue': '₹4,200', 'New Revenue': '₹4,200', 'Repeat Revenue': '₹0',
            'ARPU': '₹2,100', 'New ARPU': '₹2,100', 'Repeat ARPU': '₹0',
        },
        {
            'Date': 'bad date',
            'Total Payments': '1', 'New Payments': '0', 'Repeat Payments': '1',
            'New %': '0.00%', 'Repeat %': '100.00%',
            'Total Revenue': '₹3,999', 'New Revenue': '₹0', 'Repeat Revenue': '₹3,999',
            'ARPU': '₹3,999', 'New ARPU': '₹0', 'Repeat ARPU': '₹3,999',
        },
    ])

def test_clean_df_drops_bad_dates():
    df = clean_df(_make_overall_df(), 'overall')
    assert len(df) == 1

def test_clean_df_parses_date():
    df = clean_df(_make_overall_df(), 'overall')
    from datetime import date
    assert df.iloc[0]['date'] == date(2025, 5, 13)

def test_clean_df_numeric_revenue():
    df = clean_df(_make_overall_df(), 'overall')
    assert df.iloc[0]['total_revenue'] == 4200.0

def test_clean_df_numeric_payments():
    df = clean_df(_make_overall_df(), 'overall')
    assert df.iloc[0]['total_payments'] == 2.0
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_fetch.py::test_clean_df_drops_bad_dates -v
```

Expected: `AttributeError: module 'fetch_data' has no attribute 'clean_df'`

- [ ] **Step 3: Add `clean_df` to fetch_data.py**

Add after `safe_div`:

```python
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
```

- [ ] **Step 4: Run all tests**

```bash
pytest tests/test_fetch.py -v
```

Expected: 13 tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add fetch_data.py tests/test_fetch.py
git commit -m "feat: sheet reading and DataFrame cleaning"
```

---

## Task 4: Aggregation Logic + Tests

**Files:**
- Modify: `fetch_data.py` (add `daily_records`, `aggregate`, `build_tab_data`)
- Modify: `tests/test_fetch.py` (add aggregation tests)

- [ ] **Step 1: Write failing aggregation tests**

Add to `tests/test_fetch.py`:

```python
from fetch_data import daily_records, aggregate, clean_df
from datetime import date

def _overall_df_two_rows():
    df = pd.DataFrame([
        {
            'Date': '01/01/2025',
            'Total Payments': '4', 'New Payments': '3', 'Repeat Payments': '1',
            'Total Revenue': '₹8,000', 'New Revenue': '₹6,000', 'Repeat Revenue': '₹2,000',
            'ARPU': '', 'New ARPU': '', 'Repeat ARPU': '',
            'New %': '', 'Repeat %': '',
        },
        {
            'Date': '08/01/2025',
            'Total Payments': '2', 'New Payments': '1', 'Repeat Payments': '1',
            'Total Revenue': '₹4,000', 'New Revenue': '₹2,000', 'Repeat Revenue': '₹2,000',
            'ARPU': '', 'New ARPU': '', 'Repeat ARPU': '',
            'New %': '', 'Repeat %': '',
        },
    ])
    return clean_df(df, 'overall')

def test_daily_records_count():
    df = _overall_df_two_rows()
    records = daily_records(df, 'overall')
    assert len(records) == 2

def test_daily_records_arpu_calculated():
    df = _overall_df_two_rows()
    records = daily_records(df, 'overall')
    # 8000 / 4 = 2000
    assert records[0]['arpu'] == 2000.0

def test_daily_records_new_pct():
    df = _overall_df_two_rows()
    records = daily_records(df, 'overall')
    # 3/4 * 100 = 75
    assert records[0]['new_pct'] == 75.0

def test_aggregate_monthly_sums_payments():
    df = _overall_df_two_rows()
    # Both rows are in Jan 2025
    rows = aggregate(df, 'monthly', 'overall')
    assert len(rows) == 1
    assert rows[0]['total_payments'] == 6

def test_aggregate_monthly_recalculates_arpu():
    df = _overall_df_two_rows()
    rows = aggregate(df, 'monthly', 'overall')
    # total_revenue=12000, total_payments=6 → arpu=2000
    assert rows[0]['arpu'] == 2000.0

def test_aggregate_monthly_new_pct():
    df = _overall_df_two_rows()
    rows = aggregate(df, 'monthly', 'overall')
    # new_payments=4, total=6 → 66.67%
    assert rows[0]['new_pct'] == 66.67
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
pytest tests/test_fetch.py -k "test_daily_records or test_aggregate" -v
```

Expected: `AttributeError: module 'fetch_data' has no attribute 'daily_records'`

- [ ] **Step 3: Add aggregation functions to fetch_data.py**

Add after `read_sheet`:

```python
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
    freq = 'W-MON' if period == 'weekly' else 'MS'
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
```

- [ ] **Step 4: Run all tests**

```bash
pytest tests/test_fetch.py -v
```

Expected: 19 tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add fetch_data.py tests/test_fetch.py
git commit -m "feat: aggregation logic with tests"
```

---

## Task 5: data.json Writing + Git Push

**Files:**
- Modify: `fetch_data.py` (add `main`, `git_push`)

- [ ] **Step 1: Add `git_push` and `main` to fetch_data.py**

Add at the bottom of `fetch_data.py`:

```python
def git_push(repo_dir):
    today = date.today().isoformat()
    subprocess.run(['git', 'add', 'data.json'], cwd=repo_dir, check=True)
    subprocess.run(
        ['git', 'commit', '-m', f'Update dashboard data {today}'],
        cwd=repo_dir, check=True
    )
    subprocess.run(['git', 'push'], cwd=repo_dir, check=True)


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

    git_push(REPO_DIR)
    print("Pushed to GitHub")


if __name__ == '__main__':
    main()
```

- [ ] **Step 2: Run the script manually to verify it works**

```bash
python3 fetch_data.py
```

Expected output:
```
Written /Users/anant/Documents/1 on 1 dashboard/data.json
Pushed to GitHub
```

Check that `data.json` has this shape:
```bash
python3 -c "import json; d=json.load(open('data.json')); print(list(d.keys())); print(len(d['overall']['daily']), 'overall daily rows')"
```

Expected: `['last_updated', 'overall', 'web', 'ios', 'android', 'platform']` and a count > 0.

- [ ] **Step 3: Commit**

```bash
git add fetch_data.py
git commit -m "feat: main pipeline - write data.json and git push"
```

---

## Task 6: index.html — Sidebar + Layout Skeleton

**Files:**
- Create: `index.html`

- [ ] **Step 1: Create index.html with sidebar + section shells**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>1on1 Dashboard</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"></script>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body { background: #0f172a; color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; display: flex; height: 100vh; overflow: hidden; }

    /* ── Sidebar ── */
    #sidebar { width: 210px; min-width: 210px; background: #1e293b; display: flex; flex-direction: column; border-right: 1px solid #334155; }
    .sidebar-logo { padding: 24px 20px 20px; font-size: 17px; font-weight: 700; color: #3b82f6; border-bottom: 1px solid #334155; letter-spacing: 0.02em; }
    .nav-section { padding: 12px 0 8px; border-bottom: 1px solid #334155; }
    .nav-label { padding: 0 20px 6px; font-size: 10px; text-transform: uppercase; letter-spacing: 0.1em; color: #475569; }
    .nav-item { display: block; padding: 9px 20px; cursor: pointer; font-size: 13.5px; color: #94a3b8; border-left: 3px solid transparent; user-select: none; }
    .nav-item:hover { color: #f1f5f9; background: #273549; }
    .nav-item.active { color: #f1f5f9; border-left-color: #3b82f6; background: #273549; }

    /* ── Granularity ── */
    .gran-wrap { padding: 16px 20px; border-bottom: 1px solid #334155; }
    .gran-label { font-size: 10px; text-transform: uppercase; letter-spacing: 0.1em; color: #475569; margin-bottom: 8px; }
    .gran-btns { display: flex; gap: 6px; }
    .gran-btn { flex: 1; padding: 5px 0; font-size: 11px; font-weight: 600; background: #334155; border: none; color: #94a3b8; cursor: pointer; border-radius: 5px; }
    .gran-btn:hover { background: #3d4f68; color: #f1f5f9; }
    .gran-btn.active { background: #3b82f6; color: #fff; }

    .last-updated { margin-top: auto; padding: 14px 20px; font-size: 11px; color: #475569; }

    /* ── Main ── */
    #main { flex: 1; overflow-y: auto; padding: 28px 32px; }
    .section { display: none; }
    .section.active { display: block; }
    .section-title { font-size: 21px; font-weight: 700; margin-bottom: 22px; color: #f1f5f9; }

    /* ── KPI cards ── */
    .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 24px; }
    .kpi-grid-5 { grid-template-columns: repeat(5, 1fr); }
    .kpi-card { background: #1e293b; border-radius: 10px; padding: 18px 20px; }
    .kpi-label { font-size: 10.5px; text-transform: uppercase; letter-spacing: 0.08em; color: #64748b; margin-bottom: 6px; }
    .kpi-value { font-size: 24px; font-weight: 700; color: #f1f5f9; }

    /* ── Chart layout ── */
    .charts-row { display: grid; grid-template-columns: 2fr 1fr; gap: 14px; margin-bottom: 14px; }
    .chart-card { background: #1e293b; border-radius: 10px; padding: 20px; }
    .chart-card.full { grid-column: 1 / -1; }
    .chart-title { font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 14px; }
  </style>
</head>
<body>
  <div id="sidebar">
    <div class="sidebar-logo">1on1</div>
    <div class="nav-section">
      <div class="nav-label">Views</div>
      <div class="nav-item active" data-section="overall">Overview</div>
      <div class="nav-item" data-section="web">Web</div>
      <div class="nav-item" data-section="ios">iOS</div>
      <div class="nav-item" data-section="android">Android</div>
      <div class="nav-item" data-section="platform">Platform</div>
    </div>
    <div class="gran-wrap">
      <div class="gran-label">Granularity</div>
      <div class="gran-btns">
        <button class="gran-btn active" data-gran="daily">Day</button>
        <button class="gran-btn" data-gran="weekly">Week</button>
        <button class="gran-btn" data-gran="monthly">Month</button>
      </div>
    </div>
    <div class="last-updated" id="last-updated">—</div>
  </div>

  <div id="main">
    <!-- Overview -->
    <div class="section active" id="section-overall">
      <div class="section-title">Overview</div>
      <div class="kpi-grid" id="kpi-overall"></div>
      <div class="charts-row">
        <div class="chart-card"><div class="chart-title">Revenue Over Time</div><canvas id="chart-overall-revenue"></canvas></div>
        <div class="chart-card"><div class="chart-title">New vs Repeat</div><canvas id="chart-overall-donut"></canvas></div>
      </div>
      <div class="chart-card"><div class="chart-title">Payments Over Time</div><canvas id="chart-overall-payments"></canvas></div>
    </div>

    <!-- Web -->
    <div class="section" id="section-web">
      <div class="section-title">Web</div>
      <div class="kpi-grid" id="kpi-web"></div>
      <div class="charts-row">
        <div class="chart-card"><div class="chart-title">Revenue Over Time</div><canvas id="chart-web-revenue"></canvas></div>
        <div class="chart-card"><div class="chart-title">New vs Repeat</div><canvas id="chart-web-donut"></canvas></div>
      </div>
      <div class="chart-card"><div class="chart-title">Payments Over Time</div><canvas id="chart-web-payments"></canvas></div>
    </div>

    <!-- iOS -->
    <div class="section" id="section-ios">
      <div class="section-title">iOS</div>
      <div class="kpi-grid" id="kpi-ios"></div>
      <div class="charts-row">
        <div class="chart-card"><div class="chart-title">Revenue Over Time</div><canvas id="chart-ios-revenue"></canvas></div>
        <div class="chart-card"><div class="chart-title">New vs Repeat</div><canvas id="chart-ios-donut"></canvas></div>
      </div>
      <div class="chart-card"><div class="chart-title">Payments Over Time</div><canvas id="chart-ios-payments"></canvas></div>
    </div>

    <!-- Android -->
    <div class="section" id="section-android">
      <div class="section-title">Android</div>
      <div class="kpi-grid" id="kpi-android"></div>
      <div class="charts-row">
        <div class="chart-card"><div class="chart-title">Revenue Over Time</div><canvas id="chart-android-revenue"></canvas></div>
        <div class="chart-card"><div class="chart-title">New vs Repeat</div><canvas id="chart-android-donut"></canvas></div>
      </div>
      <div class="chart-card"><div class="chart-title">Payments Over Time</div><canvas id="chart-android-payments"></canvas></div>
    </div>

    <!-- Platform -->
    <div class="section" id="section-platform">
      <div class="section-title">Platform Breakdown</div>
      <div class="kpi-grid kpi-grid-5" id="kpi-platform"></div>
      <div class="charts-row">
        <div class="chart-card"><div class="chart-title">Payments by Platform</div><canvas id="chart-platform-payments"></canvas></div>
        <div class="chart-card"><div class="chart-title">Platform Share</div><canvas id="chart-platform-donut"></canvas></div>
      </div>
      <div class="chart-card"><div class="chart-title">Revenue by Platform</div><canvas id="chart-platform-revenue"></canvas></div>
    </div>
  </div>

  <script>
    // Populated in Task 7
  </script>
</body>
</html>
```

- [ ] **Step 2: Open index.html in browser and verify layout**

Open `index.html` directly in Chrome/Safari (double-click). You should see:
- Dark sidebar on the left with nav links and granularity buttons
- Empty main area with section titles
- No charts yet (that's expected)

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "feat: dashboard HTML skeleton with sidebar and section layout"
```

---

## Task 7: Dashboard JavaScript — Data Loading, KPI Cards, Nav

**Files:**
- Modify: `index.html` (replace `<script>` block)

- [ ] **Step 1: Replace the empty `<script>` block in index.html with this JS**

Replace `<script>\n    // Populated in Task 7\n  </script>` with:

```html
<script>
  // ── State ──
  let DATA = null;
  let currentGran = 'daily';

  const CHARTS = {};

  // ── Colour palette ──
  const C = {
    new:     '#3b82f6',
    repeat:  '#8b5cf6',
    web:     '#3b82f6',
    ios:     '#10b981',
    android: '#f59e0b',
  };

  // ── Formatters ──
  function fmtRev(v) {
    if (v >= 100000) return '₹' + (v / 100000).toFixed(1) + 'L';
    if (v >= 1000)   return '₹' + (v / 1000).toFixed(1) + 'K';
    return '₹' + Math.round(v);
  }
  function fmtPct(v) { return (v || 0).toFixed(1) + '%'; }
  function fmtNum(v) { return Math.round(v || 0).toLocaleString('en-IN'); }

  // ── KPI cards ──
  function renderKpi(tab, gran) {
    const rows = DATA[tab][gran];
    if (!rows || !rows.length) return;
    const last = rows[rows.length - 1];
    const el = document.getElementById('kpi-' + tab);

    if (tab === 'platform') {
      el.innerHTML = `
        <div class="kpi-card"><div class="kpi-label">Total Payments</div><div class="kpi-value">${fmtNum(last.total_payments)}</div></div>
        <div class="kpi-card"><div class="kpi-label">Total Revenue</div><div class="kpi-value">${fmtRev(last.total_revenue)}</div></div>
        <div class="kpi-card"><div class="kpi-label">Web ARPU</div><div class="kpi-value">${fmtRev(last.web_arpu)}</div></div>
        <div class="kpi-card"><div class="kpi-label">iOS ARPU</div><div class="kpi-value">${fmtRev(last.ios_arpu)}</div></div>
        <div class="kpi-card"><div class="kpi-label">Android ARPU</div><div class="kpi-value">${fmtRev(last.android_arpu)}</div></div>
      `;
    } else {
      el.innerHTML = `
        <div class="kpi-card"><div class="kpi-label">Total Payments</div><div class="kpi-value">${fmtNum(last.total_payments)}</div></div>
        <div class="kpi-card"><div class="kpi-label">Total Revenue</div><div class="kpi-value">${fmtRev(last.total_revenue)}</div></div>
        <div class="kpi-card"><div class="kpi-label">ARPU</div><div class="kpi-value">${fmtRev(last.arpu)}</div></div>
        <div class="kpi-card"><div class="kpi-label">Repeat %</div><div class="kpi-value">${fmtPct(last.repeat_pct)}</div></div>
      `;
    }
  }

  // ── Chart helpers ──
  const SCALE_OPTS = {
    x: { ticks: { color: '#475569', maxTicksLimit: 10, font: { size: 11 } }, grid: { color: '#273549' } },
    y: { ticks: { color: '#475569', font: { size: 11 } }, grid: { color: '#334155' } },
  };
  const LEGEND_OPTS = { labels: { color: '#94a3b8', font: { size: 11 }, boxWidth: 12 } };

  function destroyChart(id) {
    if (CHARTS[id]) { CHARTS[id].destroy(); delete CHARTS[id]; }
  }

  function makeChart(id, config) {
    destroyChart(id);
    CHARTS[id] = new Chart(document.getElementById(id).getContext('2d'), config);
  }

  // ── Chart renderers ──
  function renderRevenueChart(tab, rows) {
    makeChart(`chart-${tab}-revenue`, {
      type: 'line',
      data: {
        labels: rows.map(r => r.date),
        datasets: [
          { label: 'New Revenue', data: rows.map(r => r.new_revenue), borderColor: C.new, backgroundColor: C.new + '26', fill: true, tension: 0.35, pointRadius: 1, pointHoverRadius: 4 },
          { label: 'Repeat Revenue', data: rows.map(r => r.repeat_revenue), borderColor: C.repeat, backgroundColor: C.repeat + '26', fill: true, tension: 0.35, pointRadius: 1, pointHoverRadius: 4 },
        ]
      },
      options: { responsive: true, animation: false, plugins: { legend: LEGEND_OPTS }, scales: { ...SCALE_OPTS, y: { ...SCALE_OPTS.y, stacked: true } } }
    });
  }

  function renderPaymentsChart(tab, rows) {
    makeChart(`chart-${tab}-payments`, {
      type: 'bar',
      data: {
        labels: rows.map(r => r.date),
        datasets: [
          { label: 'New', data: rows.map(r => r.new_payments), backgroundColor: C.new, stack: 'p' },
          { label: 'Repeat', data: rows.map(r => r.repeat_payments), backgroundColor: C.repeat, stack: 'p' },
        ]
      },
      options: { responsive: true, animation: false, plugins: { legend: LEGEND_OPTS }, scales: { ...SCALE_OPTS, x: { ...SCALE_OPTS.x, stacked: true }, y: { ...SCALE_OPTS.y, stacked: true } } }
    });
  }

  function renderDonut(tab, rows) {
    const totalNew    = rows.reduce((s, r) => s + r.new_payments, 0);
    const totalRepeat = rows.reduce((s, r) => s + r.repeat_payments, 0);
    makeChart(`chart-${tab}-donut`, {
      type: 'doughnut',
      data: {
        labels: ['New', 'Repeat'],
        datasets: [{ data: [totalNew, totalRepeat], backgroundColor: [C.new, C.repeat], borderWidth: 0 }]
      },
      options: { responsive: true, animation: false, plugins: { legend: LEGEND_OPTS } }
    });
  }

  function renderPlatformCharts(rows) {
    makeChart('chart-platform-payments', {
      type: 'bar',
      data: {
        labels: rows.map(r => r.date),
        datasets: [
          { label: 'Web', data: rows.map(r => r.web), backgroundColor: C.web, stack: 'p' },
          { label: 'iOS', data: rows.map(r => r.ios), backgroundColor: C.ios, stack: 'p' },
          { label: 'Android', data: rows.map(r => r.android), backgroundColor: C.android, stack: 'p' },
        ]
      },
      options: { responsive: true, animation: false, plugins: { legend: LEGEND_OPTS }, scales: { ...SCALE_OPTS, x: { ...SCALE_OPTS.x, stacked: true }, y: { ...SCALE_OPTS.y, stacked: true } } }
    });

    makeChart('chart-platform-revenue', {
      type: 'bar',
      data: {
        labels: rows.map(r => r.date),
        datasets: [
          { label: 'Web', data: rows.map(r => r.web_revenue), backgroundColor: C.web, stack: 'r' },
          { label: 'iOS', data: rows.map(r => r.ios_revenue), backgroundColor: C.ios, stack: 'r' },
          { label: 'Android', data: rows.map(r => r.android_revenue), backgroundColor: C.android, stack: 'r' },
        ]
      },
      options: { responsive: true, animation: false, plugins: { legend: LEGEND_OPTS }, scales: { ...SCALE_OPTS, x: { ...SCALE_OPTS.x, stacked: true }, y: { ...SCALE_OPTS.y, stacked: true } } }
    });

    const web     = rows.reduce((s, r) => s + r.web, 0);
    const ios     = rows.reduce((s, r) => s + r.ios, 0);
    const android = rows.reduce((s, r) => s + r.android, 0);
    makeChart('chart-platform-donut', {
      type: 'doughnut',
      data: {
        labels: ['Web', 'iOS', 'Android'],
        datasets: [{ data: [web, ios, android], backgroundColor: [C.web, C.ios, C.android], borderWidth: 0 }]
      },
      options: { responsive: true, animation: false, plugins: { legend: LEGEND_OPTS } }
    });
  }

  // ── Section render ──
  function renderSection(tab, gran) {
    const rows = DATA[tab][gran];
    renderKpi(tab, gran);
    if (tab === 'platform') {
      renderPlatformCharts(rows);
    } else {
      renderRevenueChart(tab, rows);
      renderPaymentsChart(tab, rows);
      renderDonut(tab, rows);
    }
  }

  // ── Nav wiring ──
  document.querySelectorAll('.nav-item').forEach(el => {
    el.addEventListener('click', () => {
      document.querySelectorAll('.nav-item').forEach(e => e.classList.remove('active'));
      document.querySelectorAll('.section').forEach(e => e.classList.remove('active'));
      el.classList.add('active');
      const tab = el.dataset.section;
      document.getElementById('section-' + tab).classList.add('active');
      if (DATA) renderSection(tab, currentGran);
    });
  });

  // ── Granularity wiring ──
  document.querySelectorAll('.gran-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.gran-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentGran = btn.dataset.gran;
      const activeTab = document.querySelector('.nav-item.active').dataset.section;
      if (DATA) renderSection(activeTab, currentGran);
    });
  });

  // ── Load data ──
  fetch('data.json')
    .then(r => {
      if (!r.ok) throw new Error('data.json not found — run fetch_data.py first');
      return r.json();
    })
    .then(data => {
      DATA = data;
      document.getElementById('last-updated').textContent = 'Updated: ' + data.last_updated;
      renderSection('overall', currentGran);
    })
    .catch(err => {
      document.getElementById('main').innerHTML =
        `<div style="padding:40px;color:#ef4444">${err.message}</div>`;
    });
</script>
```

- [ ] **Step 2: Serve index.html locally and verify**

Since `fetch('data.json')` requires HTTP (not `file://`), serve it locally:

```bash
cd "/Users/anant/Documents/1 on 1 dashboard" && python3 -m http.server 8080
```

Open **http://localhost:8080** in the browser.

Verify:
- KPI cards show values for the most recent daily row
- Revenue stacked area chart renders with blue (New) and purple (Repeat) areas
- Payments stacked bar chart renders
- Donut shows New vs Repeat split
- Clicking Web / iOS / Android / Platform in sidebar switches sections
- Clicking Week / Month in granularity toggle re-renders charts with aggregated data

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "feat: complete dashboard JS with charts and nav"
```

---

## Task 8: GitHub Pages Deployment

- [ ] **Step 1: Create a GitHub repo (if not already done)**

Go to github.com → New repository → name it `1on1-dashboard` → Public → no README.

- [ ] **Step 2: Set up remote and push**

```bash
cd "/Users/anant/Documents/1 on 1 dashboard"
git remote add origin https://github.com/YOUR_USERNAME/1on1-dashboard.git
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username.

- [ ] **Step 3: Enable GitHub Pages**

Go to repo Settings → Pages → Source: `Deploy from branch` → Branch: `main` → Folder: `/ (root)` → Save.

Wait ~1 minute, then open `https://YOUR_USERNAME.github.io/1on1-dashboard/`.

- [ ] **Step 4: Verify dashboard loads on GitHub Pages**

Open the Pages URL. Verify the same dashboard appears as on localhost.

---

## Task 9: Cron Setup

- [ ] **Step 1: Test the script runs clean from anywhere**

```bash
cd ~ && python3 "/Users/anant/Documents/1 on 1 dashboard/fetch_data.py"
```

Expected: writes data.json and pushes to GitHub without errors.

- [ ] **Step 2: Add cron job**

```bash
crontab -e
```

Add this line (runs at 9am daily):

```
0 9 * * * /usr/bin/python3 "/Users/anant/Documents/1 on 1 dashboard/fetch_data.py" >> "/Users/anant/Documents/1 on 1 dashboard/fetch.log" 2>&1
```

Save and exit. Verify with:

```bash
crontab -l
```

- [ ] **Step 3: Final commit**

```bash
cd "/Users/anant/Documents/1 on 1 dashboard"
git add .
git commit -m "docs: add cron setup instructions"
git push
```
