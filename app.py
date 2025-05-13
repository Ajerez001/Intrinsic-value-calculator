import streamlit as st
import yfinance as yf
import requests
from fredapi import Fred
import os

# Set your FRED API Key
FRED_API_KEY = "ef227271f5aef3df5c1a8970d24aabc2"
fred = Fred(api_key=FRED_API_KEY)

st.set_page_config(page_title="Intrinsic Value Calculator", layout="wide")
st.title("Intrinsic Value Calculator")

# Convert company name to ticker symbol using Yahoo Finance search API
def get_ticker_from_name(name):
    url = f"https://query1.finance.yahoo.com/v1/finance/search?q={name}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            results = response.json().get("quotes", [])
            if results:
                return results[0]["symbol"]
    except Exception as e:
        st.error(f"Error searching for ticker: {e}")
    return None

# Get AAA corporate bond yield from FRED
@st.cache_data(ttl=86400)
def get_aaa_corp_bond_rate():
    try:
        rate = fred.get_series_latest_release("AAA")
        return round(rate.iloc[-1], 2)
    except Exception as e:
        st.error("Failed to fetch AAA corporate bond rate from FRED.")
        return None

# Discounted Cash Flow (DCF) formula
def calculate_intrinsic_value(eps, growth_rate, discount_rate):
    try:
        value = eps * (8.5 + 2 * (growth_rate * 100)) * (4.4 / discount_rate)
        return round(value, 2)
    except:
        return None

# Input section
user_input = st.text_input("Enter Ticker or Company Name")

if user_input:
    ticker = user_input.upper()

    # Try using ticker directly
    stock = yf.Ticker(ticker)
    try:
        info = stock.info
        if "shortName" not in info:
            # Try to convert name to ticker if direct fetch fails
            ticker = get_ticker_from_name(user_input)
            if ticker:
                stock = yf.Ticker(ticker)
                info = stock.info
            else:
                st.error("Ticker not found.")
                st.stop()
    except:
        ticker = get_ticker_from_name(user_input)
        if ticker:
            stock = yf.Ticker(ticker)
            info = stock.info
        else:
            st.error("Ticker not found.")
            st.stop()

    # Show company info
    st.subheader(f"{info.get('shortName', '')} ({ticker})")
    st.write(f"Current Price: ${info.get('currentPrice', 'N/A')}")
    st.write(f"Earnings Date: {info.get('earningsDate', 'N/A')}")

    # EPS and growth input
    eps_input = st.number_input("Enter total EPS from last 4 quarters", min_value=0.0, step=0.01)
    growth_rate = st.number_input("Enter expected annual growth rate (e.g., 0.08 for 8%)", min_value=0.0, step=0.01)

    # AAA Bond Rate from FRED
    aaa_rate = get_aaa_corp_bond_rate()
    if aaa_rate:
        st.write(f"AAA Corporate Bond Rate (FRED): {aaa_rate}%")

    # Calculate intrinsic value
    if st.button("Calculate Intrinsic Value"):
        if eps_input > 0 and growth_rate > 0 and aaa_rate:
            intrinsic_value = calculate_intrinsic_value(eps_input, growth_rate, aaa_rate)
            st.success(f"Intrinsic Value: ${intrinsic_value}")

            # Fair value range with 20% margin of safety
            margin_price = round(intrinsic_value * 0.8, 2)
            st.write(f"**Buy only if stock is trading below: ${margin_price} (20% margin of safety)**")
        else:
            st.error("Please fill all required fields.")
