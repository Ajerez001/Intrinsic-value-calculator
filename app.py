import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta
from fredapi import Fred

st.set_page_config(page_title="Intrinsic Value Calculator", layout="wide")

st.title("Intrinsic Value Calculator (Graham Formula)")

ticker = st.text_input("Enter Stock Ticker (e.g., AAPL)", "")

# Function to get AAA bond yield from FRED
def get_aaa_bond_yield():
    fred_api_key = st.secrets["FRED_API_KEY"]
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id=DAAA&api_key={fred_api_key}&file_type=json"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        observations = data.get("observations", [])
        latest_valid = next((obs for obs in reversed(observations) if obs["value"] not in ("", ".")), None)
        if latest_valid:
            return float(latest_valid["value"])
        else:
            st.warning("No valid AAA bond yield found. Using fallback 4.0%.")
            return 4.0
    except Exception:
        st.warning("Could not fetch AAA bond yield. Using fallback 4.0%.")
        return 4.0

if ticker:
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        eps_ttm = info.get("trailingEps", None)
        shares = info.get("sharesOutstanding", None)

        if eps_ttm is None or shares is None:
            st.error("Missing financial data for EPS or shares outstanding.")
        else:
            # Get AAA bond rate
            bond_rate = get_aaa_bond_yield()

            # User inputs growth rate manually
            growth_estimate = st.number_input("Enter Estimated Growth Rate (%)", min_value=0.0, max_value=50.0, value=10.0)

            # Graham Formula
            intrinsic_value = (eps_ttm * (8.5 + 2 * growth_estimate) * 4.4) / bond_rate

            current_price = info.get("currentPrice", 0)

            st.subheader("Results")
            st.write(f"**EPS (TTM):** {eps_ttm}")
            st.write(f"**Estimated Growth:** {growth_estimate}%")
            st.write(f"**AAA Bond Rate:** {bond_rate}%")
            st.write(f"**Current Price:** ${current_price}")
            st.success(f"**Intrinsic Value:** ${intrinsic_value:.2f}")

            # Valuation assessment
            if intrinsic_value > current_price * 1.15:
                st.markdown("### :green[Undervalued]")
            elif intrinsic_value < current_price * 0.85:
                st.markdown("### :red[Overvalued]")
            else:
                st.markdown("### :orange[Fairly Valued]")

            # Live stock chart
            st.subheader("Live Stock Chart (Last 3 Months)")
            end = datetime.today()
            start = end - timedelta(days=90)
            hist = stock.history(start=start, end=end)

            st.line_chart(hist['Close'])

    except Exception as e:
        st.error(f"Could not retrieve data. Error: {e}")
