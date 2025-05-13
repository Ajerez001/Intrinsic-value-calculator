import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from fredapi import Fred

# Set page config
st.set_page_config(page_title="Intrinsic Value Calculator", layout="centered")

# FRED setup
FRED_API_KEY = "ef227271f5aef3df5c1a8970d24aabc2"
fred = Fred(api_key=FRED_API_KEY)

# Helper functions
def get_aaa_bond_rate():
    try:
        rate = fred.get_series_latest_release('AAA')
        latest_value = rate.iloc[-1]
        return latest_value / 100  # convert to decimal
    except Exception as e:
        st.warning("Could not fetch AAA corporate bond rate from FRED.")
        return 0.08  # default fallback

def search_ticker(query):
    url = f"https://query1.finance.yahoo.com/v1/finance/search?q={query}"
    try:
        response = requests.get(url)
        data = response.json()
        for item in data.get("quotes", []):
            if item.get("quoteType") == "EQUITY":
                return item.get("symbol")
    except:
        return None

def calculate_intrinsic_value(eps, growth_rate_percent, discount_rate, years=10):
    try:
        growth_rate = growth_rate_percent / 100  # Convert 8% → 0.08
        intrinsic_value = 0
        for year in range(1, years + 1):
            future_eps = eps * ((1 + growth_rate) ** year)
            intrinsic_value += future_eps / ((1 + discount_rate) ** year)
        return round(intrinsic_value, 2)
    except:
        return 0.0

# UI
st.title("Intrinsic Value Calculator")

user_input = st.text_input("Enter Company Name or Ticker Symbol")

if user_input:
    ticker = search_ticker(user_input)
    
    if ticker:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            company_name = info.get("shortName", ticker)
            current_price = info.get("currentPrice", None)

            st.subheader(f"{company_name} ({ticker})")
            if current_price:
                st.write(f"**Current Price:** ${current_price}")

            # Manual EPS input
            eps_total = st.number_input("Enter Total EPS for Last 4 Quarters", min_value=0.0, step=0.01)

            # Manual Growth Rate input
            growth_rate_percent = st.number_input("Expected Growth Rate (%)", min_value=0.0, step=0.01)

            # Fetch Discount Rate
            discount_rate = get_aaa_bond_rate()
            st.write(f"**Discount Rate (AAA Corp Bond):** {discount_rate * 100:.2f}%")

            # Calculate intrinsic value
            if eps_total > 0 and growth_rate_percent > 0:
                intrinsic = calculate_intrinsic_value(eps_total, growth_rate_percent, discount_rate)

                margin_price = round(intrinsic * 0.8, 2)  # 20% margin of safety
                st.success(f"**Intrinsic Value:** ${intrinsic}")
                st.info(f"**Buy Below (20% Margin of Safety):** ${margin_price}")

        except Exception as e:
            st.error(f"Error fetching stock info: {e}")
    else:
        st.error("Error searching for ticker. Please check the name or symbol.")
