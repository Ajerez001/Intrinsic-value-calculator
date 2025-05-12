import streamlit as st
import yfinance as yf
from fredapi import Fred

# App title
st.title("Intrinsic Value Calculator (Graham Formula)")

# User input for stock ticker
ticker = st.text_input("Enter Stock Ticker (e.g., AAPL)", "")

# Manual EPS and growth rate input
st.subheader("Manual Inputs")

eps_ttm = st.number_input("Enter Total EPS (TTM) from last 4 quarters", format="%.2f")
manual_growth = st.number_input("Enter Estimated Growth Rate (%)", format="%.2f")

# Fetch AAA corporate bond rate from FRED
st.subheader("AAA Corporate Bond Rate (Auto-Fetched)")

try:
    fred = Fred(api_key=st.secrets["FRED_API_KEY"])
    bond_yield = fred.get_series_latest_release('DAAA')[-1]
    bond_rate = round(float(bond_yield), 2)
    st.success(f"AAA Bond Rate: {bond_rate}%")
except Exception as e:
    bond_rate = st.number_input("Enter Bond Rate (%)", format="%.2f")
    st.warning("Could not fetch bond rate from FRED. Please enter manually.")

# Calculate intrinsic value using Graham formula
if eps_ttm > 0 and manual_growth > 0 and bond_rate > 0:
    intrinsic_value = (eps_ttm * (8.5 + 2 * manual_growth) * 4.4) / bond_rate
    st.subheader("Intrinsic Value Result")
    st.success(f"Intrinsic Value: ${intrinsic_value:.2f}")

    # Valuation color indicator
    try:
        stock = yf.Ticker(ticker)
        current_price = stock.info['currentPrice']
        st.write(f"Current Price: ${current_price:.2f}")

        if intrinsic_value > current_price * 1.2:
            st.markdown("**Valuation: Undervalued**")
            st.markdown("<span style='color: green;'>Undervalued</span>", unsafe_allow_html=True)
        elif intrinsic_value < current_price * 0.8:
            st.markdown("**Valuation: Overvalued**")
            st.markdown("<span style='color: red;'>Overvalued</span>", unsafe_allow_html=True)
        else:
            st.markdown("**Valuation: Fairly Valued**")
            st.markdown("<span style='color: orange;'>Fairly Valued</span>", unsafe_allow_html=True)
    except Exception:
        st.warning("Could not fetch current stock price.")
