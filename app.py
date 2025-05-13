import streamlit as st
import yfinance as yf
from fredapi import Fred
from datetime import datetime

# Load FRED API Key from secrets
fred_api_key = st.secrets["FRED_API_KEY"]
fred = Fred(api_key=fred_api_key)

# App title
st.title("Intrinsic Value Calculator with Options Snapshot")

# Input box for ticker
ticker_input = st.text_input("Enter Stock Ticker", "AAPL").upper()

# Function to fetch stock price and earnings date
def get_stock_info(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        price = info.get("currentPrice", "N/A")
        earnings_date = stock.calendar.loc["Earnings Date"][0] if "Earnings Date" in stock.calendar.index else "N/A"
        return price, earnings_date
    except Exception as e:
        st.error(f"Could not load data for {ticker}. Error: {e}")
        return "N/A", "N/A"

# Get stock info
if ticker_input:
    current_price, earnings_date = get_stock_info(ticker_input)
    st.subheader(f"{ticker_input} — ${current_price} {'(Earnings: ' + str(earnings_date.date()) + ')' if earnings_date != 'N/A' else ''}")

# FRED AAA corporate bond yield
def get_aaa_yield():
    try:
        yield_data = fred.get_series('AAA')
        return round(float(yield_data.dropna().iloc[-1]), 2)
    except Exception as e:
        st.warning("Could not fetch AAA bond yield. Please check your FRED API key or internet connection.")
        return None

bond_rate = get_aaa_yield()
if bond_rate:
    st.markdown(f"**AAA Corporate Bond Yield:** {bond_rate}%")
else:
    bond_rate = st.number_input("Manually enter AAA bond yield (%)", min_value=0.0, step=0.01)

# Manual input for EPS and growth rate
eps_ttm = st.number_input("Enter Total EPS (last 4 quarters)", min_value=0.0, step=0.01)
growth_rate = st.number_input("Enter Estimated Growth Rate (%)", min_value=0.0, step=0.1)

# Valuation calculation
def calculate_intrinsic_value(eps, growth, bond):
    try:
        g = growth / 100
        r = bond / 100
        intrinsic_value = eps * (8.5 + 2 * g) * (4.4 / r)
        return round(intrinsic_value, 2)
    except Exception:
        return None

if eps_ttm and growth_rate and bond_rate:
    intrinsic_value = calculate_intrinsic_value(eps_ttm, growth_rate, bond_rate)

    if current_price != "N/A":
        diff = float(current_price) - intrinsic_value
        pct = round((diff / intrinsic_value) * 100, 2)

        if pct < -15:
            color = "green"
            valuation_status = "Undervalued"
        elif -15 <= pct <= 15:
            color = "gray"
            valuation_status = "Fairly Valued"
        else:
            color = "red"
            valuation_status = "Overvalued"

        st.markdown(f"### Intrinsic Value: ${intrinsic_value}")
        st.markdown(f"**Valuation Status:** <span style='color:{color}'>{valuation_status}</span>", unsafe_allow_html=True)
    else:
        st.markdown(f"### Intrinsic Value: ${intrinsic_value}")
