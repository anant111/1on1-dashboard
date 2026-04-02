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
