import pytest
import pandas as pd
from fetch_data import clean_currency, parse_date, clean_df
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
