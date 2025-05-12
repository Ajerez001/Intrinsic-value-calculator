import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(layout="wide")
st.title("Intrinsic Value Calculator (Graham Formula)")

ticker = st.text_input("Enter Stock Ticker (e.g., AAPL)")

if ticker:
    try:
        stock = yf.Ticker(ticker)

        # Earnings per share
        eps_ttm = stock.info.get('trailingEps')
        shares_outstanding = stock.info.get('sharesOutstanding')

        # Input growth rate manually
        growth_input = st.number_input("Enter estimated growth rate (%)", value=10.0, step=0.1)

        # Get AAA corporate bond yield from secrets
        bond_rate = st.secrets["FRED_BOND_RATE"]

        # Calculate intrinsic value
        intrinsic_value = (eps_ttm * (8.5 + 2 * growth_input) * 4.4) / bond_rate

        # Current market price
        current_price = stock.history(period="1d")["Close"].iloc[-1]

        # Display outputs
        st.write(f"**EPS (TTM):** {eps_ttm}")
        st.write(f"**Growth Rate:** {growth_input}%")
        st.write(f"**AAA Bond Rate:** {bond_rate}%")
        st.write(f"**Intrinsic Value:** ${intrinsic_value:.2f}")
        st.write(f"**Current Price:** ${current_price:.2f}")

        # Color-coded valuation
        if current_price < intrinsic_value * 0.9:
            st.markdown(f"**Valuation:** :green[Undervalued]")
        elif current_price > intrinsic_value * 1.1:
            st.markdown(f"**Valuation:** :red[Overvalued]")
        else:
            st.markdown(f"**Valuation:** :orange[Fairly Valued]")

        # Live market chart
        st.subheader(f"{ticker.upper()} Stock Price (1Y)")
        hist = stock.history(period="1y")
        st.line_chart(hist["Close"])

    except Exception as e:
        st.error(f"Could not retrieve data. Error: {e}")
