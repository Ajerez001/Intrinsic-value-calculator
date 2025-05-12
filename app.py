import streamlit as st
import yfinance as yf
from fredapi import Fred
import pandas as pd

st.set_page_config(layout="wide")
st.title("Intrinsic Value Calculator (Graham Formula)")

ticker = st.text_input("Enter Stock Ticker (e.g., AAPL)", "")

if ticker:
    try:
        stock = yf.Ticker(ticker)
        eps_ttm = stock.info['trailingEps']
        current_price = stock.info['regularMarketPrice']

        # Get FRED API key from secrets
        fred = Fred(api_key=st.secrets["FRED_API_KEY"])

        # Fetch AAA bond rate
        try:
            bond_yield = fred.get_series_latest_release('DAAA')[-1]
            bond_rate = round(float(bond_yield), 2)
        except Exception:
            st.warning("Could not fetch bond rate from FRED. Using fallback value of 4.4%.")
            bond_rate = 4.4

        # User input: growth rate
        growth_estimate = st.number_input("Enter Estimated Growth Rate (%)", min_value=0.0, max_value=100.0, value=10.0, step=0.1)

        # Graham formula
        intrinsic_value = (eps_ttm * (8.5 + 2 * growth_estimate) * 4.4) / bond_rate

        # Display key stats
        st.subheader("Summary")
        st.metric("EPS (TTM)", f"${eps_ttm}")
        st.metric("Growth Estimate", f"{growth_estimate}%")
        st.metric("AAA Bond Rate", f"{bond_rate}%")
        st.metric("Current Price", f"${current_price}")
        st.metric("Intrinsic Value", f"${intrinsic_value:.2f}")

        # Fair Value Status
        if intrinsic_value > current_price * 1.2:
            value_status = "Undervalued"
            color = "green"
        elif intrinsic_value < current_price * 0.8:
            value_status = "Overvalued"
            color = "red"
        else:
            value_status = "Fairly Valued"
            color = "orange"

        st.markdown(f"<h3 style='color:{color}'>{value_status}</h3>", unsafe_allow_html=True)

        # Line chart comparing Intrinsic Value and Current Price
        st.subheader("Intrinsic vs. Market Price")
        chart_df = pd.DataFrame({
            'Metric': ['Intrinsic Value', 'Current Price'],
            'Value': [intrinsic_value, current_price]
        })
        st.line_chart(chart_df.set_index('Metric'))

    except Exception as e:
        st.error(f"Could not retrieve data. Error: {e}")
