import streamlit as st
import yfinance as yf
import pandas as pd
from fredapi import Fred
import plotly.graph_objs as go

# Title
st.set_page_config(layout="wide")
st.title("Intrinsic Value Calculator + Option Trader Snapshot")

# Input
ticker = st.text_input("Enter Stock Ticker (e.g., AAPL)", "")

# Get AAA bond rate from FRED
def get_bond_rate():
    try:
        fred = Fred(api_key=st.secrets["FRED_API_KEY"])
        bond_yield = fred.get_series_latest_release('DAAA')[-1]
        return round(float(bond_yield), 2)
    except:
        st.warning("Could not fetch AAA bond rate. Using fallback value of 4.4%")
        return 4.4

# Calculate expected move
def calculate_expected_move(current_price, iv, days):
    try:
        move = current_price * (iv / 100) * (days / 365) ** 0.5
        return round(move, 2)
    except:
        return None

if ticker:
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        eps_ttm = info.get("trailingEps", None)
        current_price = info.get("currentPrice", None)
        growth_rate = st.number_input("Enter Estimated Growth Rate (%)", min_value=0.0, value=10.0)
        bond_rate = get_bond_rate()

        if eps_ttm and current_price:
            intrinsic_value = (eps_ttm * (8.5 + 2 * growth_rate) * 4.4) / bond_rate

            # Display results
            st.subheader("Valuation Summary")
            st.write(f"EPS (TTM): {eps_ttm}")
            st.write(f"Growth Estimate: {growth_rate}%")
            st.write(f"AAA Bond Rate: {bond_rate}%")
            st.success(f"Intrinsic Value: ${intrinsic_value:.2f}")

            # Valuation color coding
            if intrinsic_value > current_price * 1.2:
                st.markdown("<span style='color:green; font-weight:bold;'>Valuation: Undervalued</span>", unsafe_allow_html=True)
            elif intrinsic_value < current_price * 0.8:
                st.markdown("<span style='color:red; font-weight:bold;'>Valuation: Overvalued</span>", unsafe_allow_html=True)
            else:
                st.markdown("<span style='color:orange; font-weight:bold;'>Valuation: Fairly Valued</span>", unsafe_allow_html=True)
        else:
            st.warning("Missing EPS or current price data.")

        # Option Trader Snapshot
        st.subheader("Options Trading Snapshot")
        col1, col2, col3, col4 = st.columns(4)

        # Implied Volatility
        iv = info.get("impliedVolatility", None)
        col1.metric("Implied Volatility", f"{iv*100:.2f}%" if iv else "Not Available")

        # Beta
        beta = info.get("beta", None)
        col2.metric("Beta", f"{beta:.2f}" if beta else "Not Available")

        # Expected Move (Next 30 Days)
        if iv and current_price:
            move = calculate_expected_move(current_price, iv * 100, 30)
            col3.metric("30d Expected Move", f"+/- ${move}" if move else "N/A")
        else:
            col3.metric("30d Expected Move", "Not Available")

        # Earnings Date
        try:
            earnings = stock.calendar.loc["Earnings Date"][0].strftime("%Y-%m-%d")
        except:
            earnings = "Not Available"
        col4.metric("Next Earnings", earnings)

        # Live Chart
        st.subheader("Live Price Chart")
        hist = stock.history(period="6mo")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], mode='lines', name='Close Price'))
        fig.update_layout(title=f"{ticker.upper()} Price History", xaxis_title="Date", yaxis_title="Price")
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error loading data: {e}")
