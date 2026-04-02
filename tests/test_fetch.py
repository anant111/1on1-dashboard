import pytest
import pandas as pd
from fetch_data import clean_currency, parse_date, clean_df, daily_records, aggregate
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
    assert df.iloc[0]['date'] == date(2025, 5, 13)

def test_clean_df_numeric_revenue():
    df = clean_df(_make_overall_df(), 'overall')
    assert df.iloc[0]['total_revenue'] == 4200.0

def test_clean_df_numeric_payments():
    df = clean_df(_make_overall_df(), 'overall')
    assert df.iloc[0]['total_payments'] == 2.0


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
