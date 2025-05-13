import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from fredapi import Fred
from datetime import datetime

# --- Set page config ---
st.set_page_config(page_title="Intrinsic Value Calculator", layout="wide")

# --- Function to fetch AAA bond rate from FRED ---
def get_aaa_bond_rate():
    try:
        fred = Fred(api_key=st.secrets["FRED_API_KEY"])
        data = fred.get_series("DAAA")
        latest_rate = data.dropna().iloc[-1] / 100
        return latest_rate
    except Exception as e:
        st.warning(f"Failed to fetch AAA bond rate: {e}")
        return 0.065  # fallback default rate

# --- Function to calculate intrinsic value using a DCF-like model ---
def calculate_intrinsic_value(eps, growth_rate, discount_rate, years=10):
    intrinsic_value = 0
    for year in range(1, years + 1):
        future_eps = eps * ((1 + growth_rate) ** year)
        discounted_eps = future_eps / ((1 + discount_rate) ** year)
        intrinsic_value += discounted_eps
    return round(intrinsic_value, 2)

# --- Function to fetch stock info and logo ---
def get_stock_info(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "longName": info.get("longName", ""),
            "logo_url": info.get("logo_url", ""),
            "currentPrice": info.get("currentPrice", None),
            "previousClose": info.get("previousClose", None),
            "earningsDate": info.get("earningsDate", None),
        }
    except Exception as e:
        st.error(f"Error fetching stock info: {e}")
        return {}

# --- Function to fetch earnings history using RapidAPI Yahoo Finance endpoint ---
def get_earnings_history(ticker):
    url = f"https://yh-finance.p.rapidapi.com/stock/v3/get-earnings?symbol={ticker}"
    headers = {
        "X-RapidAPI-Key": st.secrets["RAPIDAPI_KEY"],
        "X-RapidAPI-Host": "yh-finance.p.rapidapi.com"
    }

    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        earnings = data.get("earningsChart", {}).get("quarterly", [])
        if not earnings:
            return pd.DataFrame()
        df = pd.DataFrame(earnings)
        df["date"] = pd.to_datetime(df["date"])
        df.rename(columns={"actual": "EPS Actual", "estimate": "EPS Estimate"}, inplace=True)
        return df[["date", "EPS Actual", "EPS Estimate"]]
    except Exception as e:
        st.warning(f"Error loading earnings history: {e}")
        return pd.DataFrame()

# --- UI Layout ---
st.title("Intrinsic Value Calculator")
ticker = st.text_input("Enter Stock Ticker (e.g., AAPL):").upper()

if ticker:
    stock_info = get_stock_info(ticker)

    if stock_info.get("longName"):
        col1, col2 = st.columns([1, 4])
        with col1:
            if stock_info.get("logo_url"):
                st.image(stock_info["logo_url"], width=75)
        with col2:
            st.subheader(f"{stock_info['longName']} ({ticker})")

        # Display current price and earnings date
        price = stock_info.get("currentPrice")
        if price:
            st.metric("Current Price", f"${price:.2f}")
        if stock_info.get("earningsDate"):
            st.write("Next Earnings Date:", stock_info["earningsDate"])

        st.markdown("---")

        # --- Manual inputs ---
        total_eps = st.number_input("Enter total EPS for the last 4 quarters:", min_value=0.0, step=0.01)
        growth_rate = st.number_input("Expected annual EPS growth rate (e.g., 12% = 0.12):", min_value=0.0, step=0.01)

        # --- Fetch discount rate ---
        discount_rate = get_aaa_bond_rate()
        st.write(f"Using AAA Corporate Bond Rate as Discount Rate: **{discount_rate * 100:.2f}%**")

        # --- Calculate intrinsic value ---
        if total_eps and growth_rate:
            intrinsic_value = calculate_intrinsic_value(total_eps, growth_rate, discount_rate)
            st.success(f"Intrinsic Value: **${intrinsic_value:.2f}**")

            # Fair value range
            margin_of_safety = 0.20
            buy_below_price = intrinsic_value * (1 - margin_of_safety)
            st.info(f"Fair Value Range: Buy only if price is **below ${buy_below_price:.2f}** (20% margin of safety)")

        # --- Earnings History Section ---
        st.markdown("---")
        st.subheader("Earnings History")
        earnings_df = get_earnings_history(ticker)
        if not earnings_df.empty:
            st.dataframe(earnings_df.sort_values("date", ascending=False).reset_index(drop=True), use_container_width=True)
        else:
            st.write("No earnings history available.")
    else:
        st.error("Could not fetch valid stock data. Please check the ticker.")
