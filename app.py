import streamlit as st
import yfinance as yf
from fredapi import Fred
import requests
import datetime

# FRED API Key
FRED_API_KEY = "ef227271f5aef3df5c1a8970d24aabc2"
fred = Fred(api_key=FRED_API_KEY)

# Function to get AAA corporate bond rate
def get_aaa_corp_bond_rate():
    try:
        data = fred.get_series_latest_release('AAA')
        return round(data[-1], 4)
    except Exception as e:
        st.error(f"Error loading AAA corporate bond rate: {e}")
        return None

# Intrinsic value calculation
def calculate_intrinsic_value(eps, growth_rate, discount_rate, years=10):
    intrinsic_value = 0
    for year in range(1, years + 1):
        future_eps = eps * (1 + growth_rate) ** year
        discounted_eps = future_eps / (1 + discount_rate) ** year
        intrinsic_value += discounted_eps
    return round(intrinsic_value, 2)

# App title and input
st.title("Intrinsic Value Calculator")

ticker = st.text_input("Enter stock ticker (e.g., AAPL)").upper()

if ticker:
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        st.image(info.get("logo_url", ""), width=100)
        st.subheader(f"{info.get('shortName', '')} ({ticker})")
        st.write(f"**Current Price:** ${info.get('currentPrice', 'N/A')}")
        st.write(f"**Next Earnings Date:** {info.get('earningsDate', ['N/A'])[0]}")

        # Input for EPS (last 4 quarters total)
        eps_input = st.number_input("Enter EPS total from last 4 quarters", min_value=0.0, value=2.0)

        # Input for growth rate
        growth_input = st.number_input("Expected annual EPS growth rate (e.g., 0.08 for 8%)", min_value=0.0, max_value=1.0, value=0.08)

        # Get AAA bond rate as discount rate
        discount_rate = get_aaa_corp_bond_rate()
        if discount_rate:
            st.write(f"**Discount Rate (AAA Corporate Bond):** {discount_rate * 100:.2f}%")

            # Calculate intrinsic value
            intrinsic_value = calculate_intrinsic_value(eps_input, growth_input, discount_rate)

            st.success(f"**Intrinsic Value (per share):** ${intrinsic_value}")

            # Fair value range
            margin_threshold = intrinsic_value * 0.8
            st.info(f"**Buy Price (20% Margin of Safety):** ${margin_threshold:.2f}")
            if info.get("currentPrice") and info["currentPrice"] < margin_threshold:
                st.success("This stock is trading at or below its fair value range.")
            else:
                st.warning("This stock is not currently trading at a discount.")
        else:
            st.error("Could not retrieve AAA bond rate.")
    except Exception as e:
        st.error(f"Error fetching stock info: {e}")
