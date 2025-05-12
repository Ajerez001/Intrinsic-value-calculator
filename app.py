import streamlit as st
import yfinance as yf
import pandas as pd
from fredapi import Fred
import plotly.graph_objs as go

# Load FRED API key from secrets
fred = Fred(api_key=st.secrets["FRED_API_KEY"])

st.set_page_config(layout="wide")
st.title("Intrinsic Value & Options Analysis Dashboard")

ticker = st.text_input("Enter Stock Ticker (e.g., AAPL)", "").upper()

if ticker:
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Display company logo if available
        logo_url = info.get("logo_url")
        if logo_url:
            st.image(logo_url, width=100)

        # Get key financials
        eps_ttm = info.get("trailingEps", 0)
        shares_outstanding = info.get("sharesOutstanding", 1)

        # AAA bond rate from FRED
        try:
            bond_yield = fred.get_series_latest_release('DAAA')[-1]
            bond_rate = round(float(bond_yield), 2)
        except Exception:
            st.warning("Could not fetch bond rate from FRED. Using fallback 4.4%")
            bond_rate = 4.4

        # Growth input by user
        growth_input = st.number_input("Enter Estimated Growth Rate (%)", min_value=0.0, max_value=50.0, value=10.0)

        # Graham intrinsic value formula
        intrinsic_value = (eps_ttm * (8.5 + 2 * growth_input) * 4.4) / bond_rate
        current_price = info.get("currentPrice", 0)

        # Display valuation
        st.subheader("Valuation Analysis")
        col1, col2 = st.columns(2)
        col1.metric("EPS (TTM)", f"${eps_ttm:.2f}")
        col2.metric("AAA Bond Rate", f"{bond_rate:.2f}%")

        st.write(f"Estimated Growth Rate: {growth_input}%")

        # Color-coded intrinsic value status
        if intrinsic_value > current_price * 1.2:
            color = "green"
            status = "Undervalued"
        elif intrinsic_value < current_price * 0.8:
            color = "red"
            status = "Overvalued"
        else:
            color = "orange"
            status = "Fairly Valued"

        st.markdown(f"<h3 style='color:{color}'>Intrinsic Value: ${intrinsic_value:.2f} — {status}</h3>", unsafe_allow_html=True)

        # Historical chart
        st.subheader("Live Market Chart")
        hist = stock.history(period="1y")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist.index, y=hist["Close"], mode="lines", name="Close"))
        fig.update_layout(title=f"{ticker} Stock Price (1Y)", xaxis_title="Date", yaxis_title="Price")
        st.plotly_chart(fig, use_container_width=True)

        # Options Trading Snapshot
        st.subheader("Options Trading Snapshot")
        beta = info.get("beta")
        iv = info.get("impliedVolatility")
        next_earnings = info.get("earningsDate")

        if beta:
            st.write(f"**Beta:** {beta}")
        else:
            st.write("**Beta:** Not available")

        if iv:
            st.write(f"**Implied Volatility (IV):** {iv:.2%}")
        else:
            st.write("**Implied Volatility (IV):** Not available")

        if current_price and iv:
            expected_move = current_price * iv * (1 / 12)**0.5
            st.write(f"**Expected Monthly Move:** ${expected_move:.2f}")
        else:
            st.write("**Expected Monthly Move:** Not available")

        if next_earnings:
            st.write(f"**Next Earnings Date:** {next_earnings}")
        else:
            st.write("**Next Earnings Date:** Not available")

    except Exception as e:
        st.error(f"Could not retrieve data. Error: {e}")
