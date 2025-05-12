import streamlit as st
import yfinance as yf
from fredapi import Fred

st.title("Intrinsic Value Calculator (Graham Formula)")

ticker = st.text_input("Enter Stock Ticker (e.g., AAPL)", "")

if ticker:
    try:
        # Load financial data from Yahoo Finance
        stock = yf.Ticker(ticker)
        earnings = stock.financials.loc['Net Income'].dropna()
        shares = stock.info['sharesOutstanding']
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

        # Placeholder growth estimate for now
        growth_estimate = 10  # You can replace this with a more dynamic source later

        # Calculate intrinsic value using Graham formula
        intrinsic_value = (eps_ttm * (8.5 + 2 * growth_estimate) * 4.4) / bond_rate

        st.write(f"EPS (TTM): {eps_ttm}")
        st.write(f"Estimated Growth: {growth_estimate}%")
        st.write(f"AAA Bond Rate: {bond_rate}%")
        st.success(f"Intrinsic Value: ${intrinsic_value:.2f}")

    except Exception as e:
        st.error(f"Could not retrieve data. Error: {e}")
