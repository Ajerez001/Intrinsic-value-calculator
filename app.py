import streamlit as st
import yfinance as yf
from fredapi import Fred
import numpy as np
import plotly.graph_objs as go

# App title
st.title("Intrinsic Value Calculator + Options Snapshot")

# User input
ticker = st.text_input("Enter Stock Ticker (e.g., AAPL)", "")

if ticker:
    try:
        stock = yf.Ticker(ticker)

        # EPS and Financials
        eps_ttm = stock.info.get("trailingEps", None)
        if eps_ttm is None:
            raise ValueError("EPS data not available.")

        # Get growth rate manually from user for now
        growth_rate = st.number_input("Enter Estimated Growth Rate (%)", min_value=0.0, max_value=100.0, value=10.0)

        # Get AAA bond yield using FRED
        try:
            fred = Fred(api_key=st.secrets["FRED_API_KEY"])
            bond_yield = fred.get_series_latest_release('DAAA')[-1]
            bond_rate = round(float(bond_yield), 2)
        except:
            st.warning("Using fallback AAA bond rate of 4.4%")
            bond_rate = 4.4

        # Graham intrinsic value calculation
        intrinsic_value = (eps_ttm * (8.5 + 2 * growth_rate) * 4.4) / bond_rate

        # Display results
        st.subheader("Valuation Summary")
        st.write(f"EPS (TTM): {eps_ttm}")
        st.write(f"Growth Estimate: {growth_rate}%")
        st.write(f"AAA Bond Rate: {bond_rate}%")
        st.success(f"Intrinsic Value: ${intrinsic_value:.2f}")

        # Color-coded valuation indicator
        current_price = stock.info.get("currentPrice", None)
        if current_price:
            if intrinsic_value > current_price * 1.2:
                st.markdown("**Valuation: Undervalued**", unsafe_allow_html=True)
            elif intrinsic_value < current_price * 0.8:
                st.markdown("**Valuation: Overvalued**", unsafe_allow_html=True)
            else:
                st.markdown("**Valuation: Fairly Valued**", unsafe_allow_html=True)

        # Options Trader Snapshot
        st.subheader("Options Trader Snapshot")

        # Beta
        beta = stock.info.get("beta", "Not available")
        st.write(f"Beta: {beta}")

        # Implied Volatility (IV)
        try:
            option_chain = stock.option_chain()
            calls = option_chain.calls
            if not calls.empty and "impliedVolatility" in calls.columns:
                iv = round(calls["impliedVolatility"].mean() * 100, 2)
            else:
                iv = "Not available"
        except:
            iv = "Not available"
        st.write(f"Implied Volatility (Avg): {iv}%")

        # Expected Move (1 week)
        if iv != "Not available" and isinstance(iv, (int, float)):
            days_to_expiration = 7
            if current_price:
                expected_move = round(current_price * (iv / 100) * np.sqrt(days_to_expiration / 365), 2)
            else:
                expected_move = "Not available"
        else:
            expected_move = "Not available"
        st.write(f"Expected Move (1 Week): ${expected_move}")

        # Earnings Date
        try:
            earnings_date = stock.calendar.loc["Earnings Date"].iloc[0]
        except:
            earnings_date = "Not available"
        st.write(f"Next Earnings Date: {earnings_date}")

        # Live market chart
        st.subheader("Live Stock Chart")
        hist = stock.history(period="5d", interval="5m")
        fig = go.Figure(data=[go.Scatter(x=hist.index, y=hist["Close"], mode='lines', name=ticker)])
        fig.update_layout(title=f"{ticker} 5-Day Intraday Chart", xaxis_title="Time", yaxis_title="Price")
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Could not retrieve data. Error: {e}")
