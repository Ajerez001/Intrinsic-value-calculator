import streamlit as st
import yfinance as yf
from fredapi import Fred

st.title("Intrinsic Value Calculator (Graham Formula)")

ticker = st.text_input("Enter Stock Ticker (e.g., AAPL)", "")

if ticker:
    try:
        stock = yf.Ticker(ticker)
        eps_ttm = stock.info['trailingEps']

        # Get FRED API key from Streamlit secrets
        fred = Fred(api_key=st.secrets["FRED_API_KEY"])

        # Fetch the most recent AAA bond yield
        try:
            bond_yield = fred.get_series_latest_release('DAAA')[-1]
            bond_rate = round(float(bond_yield), 2)
        except Exception as e:
            st.warning("Could not fetch bond rate from FRED. Using fallback value of 4.4%.")
            bond_rate = 4.4

        # Manual input for growth estimate
        growth_estimate = st.number_input("Enter Estimated Growth Rate (%)", min_value=0.0, max_value=100.0, value=10.0, step=0.1)

        intrinsic_value = (eps_ttm * (8.5 + 2 * growth_estimate) * 4.4) / bond_rate

        st.write(f"EPS (TTM): {eps_ttm}")
        st.write(f"Estimated Growth: {growth_estimate}%")
        st.write(f"AAA Bond Rate: {bond_rate}%")
        st.success(f"Intrinsic Value: ${intrinsic_value:.2f}")

    except Exception as e:
        st.error(f"Could not retrieve data. Error: {e}")
