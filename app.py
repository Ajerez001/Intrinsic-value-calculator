import streamlit as st
import yfinance as yf

st.title("Intrinsic Value Calculator (Graham Formula)")

ticker = st.text_input("Enter Stock Ticker (e.g., AAPL)", "")

if ticker:
    try:
        stock = yf.Ticker(ticker)
        earnings = stock.financials.loc['Net Income'].dropna()
        shares = stock.info['sharesOutstanding']
        eps_ttm = stock.info['trailingEps']

        # Placeholder values for bond rate and growth
        bond_rate = 4.4  # AAA bond rate (adjust manually or scrape later)
        growth_estimate = 10  # Estimated growth (manual placeholder)

        intrinsic_value = (eps_ttm * (8.5 + 2 * growth_estimate) * 4.4) / bond_rate

        st.write(f"EPS (TTM): {eps_ttm}")
        st.write(f"Estimated Growth: {growth_estimate}%")
        st.write(f"AAA Bond Rate: {bond_rate}%")
        st.success(f"Intrinsic Value: ${intrinsic_value:.2f}")
    except Exception as e:
        st.error(f"Could not retrieve data. Error: {e}")
