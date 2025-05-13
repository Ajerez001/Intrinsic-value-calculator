import streamlit as st
import yfinance as yf
import requests
from datetime import datetime
import plotly.graph_objs as go
from fredapi import Fred

st.set_page_config(page_title="Intrinsic Value Calculator", layout="wide")
st.title("Intrinsic Value Calculator")

# Ticker input
ticker = st.text_input("Enter stock ticker (e.g., AAPL)", value="AAPL").upper()

# FRED bond rate
fred_api_key = st.secrets["FRED_API_KEY"]
fred = Fred(api_key=fred_api_key)
try:
    bond_rate = fred.get_series("GS10")[-1] / 100
    st.success(f"10Y Bond Rate (FRED): {bond_rate:.2%}")
except:
    bond_rate = None
    st.warning("Failed to fetch bond rate from FRED. Please enter it manually below.")

if bond_rate is None:
    bond_rate = st.number_input("Enter bond rate manually (e.g., 0.04 for 4%)", min_value=0.0, max_value=1.0, step=0.01)

# Stock Data
try:
    stock = yf.Ticker(ticker)
    info = stock.info
    price = info["regularMarketPrice"]
    previous_close = info["previousClose"]
    price_change = price - previous_close
    change_percent = (price_change / previous_close) * 100

    earnings_date = "N/A"
    try:
        earnings_calendar = stock.calendar
        if not earnings_calendar.empty:
            earnings_raw = earnings_calendar.loc["Earnings Date"]
            earnings_date = earnings_raw[0].strftime("%b %d, %Y") if not earnings_raw.empty else "N/A"
    except:
        pass

    st.markdown(f"## {info['shortName']} ({ticker})")
    if "website" in info:
        st.image(f"https://logo.clearbit.com/{info['website']}", width=100)
    st.metric("Stock Price", f"${price:.2f}", f"{price_change:+.2f} ({change_percent:+.2f}%)")
    st.markdown(f"**Earnings Date:** {earnings_date}")

except Exception as e:
    st.error(f"Could not load data for {ticker}. Error: {str(e)}")

# Manual Inputs
st.header("Manual Inputs")
eps_input = st.number_input("Enter combined EPS for last 4 quarters", min_value=0.0, step=0.01)
growth_rate_input = st.number_input("Enter expected annual growth rate (e.g., 0.12 for 12%)", min_value=0.0, step=0.01)

# Intrinsic Value
if eps_input > 0 and growth_rate_input > 0 and bond_rate > 0:
    intrinsic_value = eps_input * (8.5 + 2 * growth_rate_input * 100) * (4.4 / (bond_rate * 100))
    st.subheader("Intrinsic Value Result")
    if price < intrinsic_value * 0.8:
        st.markdown(f"<h3 style='color:green;'>Undervalued: ${intrinsic_value:.2f}</h3>", unsafe_allow_html=True)
    elif price > intrinsic_value * 1.2:
        st.markdown(f"<h3 style='color:red;'>Overvalued: ${intrinsic_value:.2f}</h3>", unsafe_allow_html=True)
    else:
        st.markdown(f"<h3 style='color:gray;'>Fairly Valued: ${intrinsic_value:.2f}</h3>", unsafe_allow_html=True)
else:
    st.info("Please fill in all inputs to calculate intrinsic value.")

# Chart
try:
    hist = stock.history(period="6mo")
    fig = go.Figure(data=[go.Candlestick(
        x=hist.index,
        open=hist["Open"],
        high=hist["High"],
        low=hist["Low"],
        close=hist["Close"]
    )])
    fig.update_layout(title=f"{ticker} Price Chart (6M)", xaxis_title="Date", yaxis_title="Price", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
except:
    st.warning("Could not load chart.")
