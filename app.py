import streamlit as st
import yfinance as yf
import pandas as pd
from fredapi import Fred
import plotly.graph_objs as go
import numpy as np

# --- Helper to get logo URL via Clearbit ---
logo_domains = {
    "Apple Inc.": "apple.com",
    "Microsoft Corporation": "microsoft.com",
    "Amazon.com, Inc.": "amazon.com",
    "Alphabet Inc.": "abc.xyz",
    # add more overrides here as needed
}

def get_logo_url(company_name):
    domain = logo_domains.get(company_name)
    if not domain:
        domain = company_name.lower().replace(" ", "") + ".com"
    return f"https://logo.clearbit.com/{domain}"

# --- Function to fetch AAA bond yield from FRED ---
def get_bond_rate():
    try:
        fred = Fred(api_key=st.secrets["FRED_API_KEY"])
        bond_yield = fred.get_series_latest_release('DAAA')[-1]
        return round(float(bond_yield), 2)
    except:
        st.warning("Could not fetch AAA bond rate. Using fallback 4.4%")
        return 4.4

# --- Expected Move Calculator ---
def calculate_expected_move(price, iv_percent, days):
    try:
        return round(price * (iv_percent/100) * np.sqrt(days/365), 2)
    except:
        return None

# --- Streamlit App ---
st.set_page_config(page_title="Intrinsic Value & Options Snapshot", layout="wide")
st.title("Intrinsic Value Calculator + Options Snapshot")

ticker = st.text_input("Enter Stock Ticker (e.g., AAPL)", "").upper()

if ticker:
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Company logo
        company_name = info.get("longName", ticker)
        logo_url = get_logo_url(company_name)
        st.image(logo_url, width=120, caption=company_name)

        # Key financials
        eps = info.get("trailingEps", None)
        current_price = info.get("currentPrice", None)

        # Growth input
        growth_rate = st.number_input("Enter Estimated Growth Rate (%)", min_value=0.0, max_value=100.0, value=10.0, step=0.1)

        # Bond rate & intrinsic value
        bond_rate = get_bond_rate()
        if eps and current_price:
            intrinsic_value = (eps * (8.5 + 2 * growth_rate) * 4.4) / bond_rate
        else:
            intrinsic_value = None

        # Valuation Summary
        st.subheader("Valuation Summary")
        if intrinsic_value:
            st.write(f"**EPS (TTM):** {eps}")
            st.write(f"**Growth Estimate:** {growth_rate}%")
            st.write(f"**AAA Bond Rate:** {bond_rate}%")
            st.write(f"**Current Price:** ${current_price:.2f}")
            st.write(f"**Intrinsic Value:** ${intrinsic_value:.2f}")

            # Color-coded status
            if intrinsic_value > current_price * 1.2:
                color, status = "green", "Undervalued"
            elif intrinsic_value < current_price * 0.8:
                color, status = "red", "Overvalued"
            else:
                color, status = "orange", "Fairly Valued"

            st.markdown(
                f"<h3 style='color:{color};'>Intrinsic Value: ${intrinsic_value:.2f} — {status}</h3>",
                unsafe_allow_html=True
            )
        else:
            st.warning("Missing EPS or current price data.")

        # Live Price Chart
        st.subheader("Live Market Chart (1 Year)")
        hist = stock.history(period="1y")
        fig = go.Figure([go.Scatter(x=hist.index, y=hist["Close"], mode="lines", name="Close")])
        fig.update_layout(
            title=f"{ticker} Price History (1Y)",
            xaxis_title="Date",
            yaxis_title="Price",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

        # Options Snapshot
        st.subheader("Options Trading Snapshot")
        col1, col2, col3, col4 = st.columns(4)

        # Beta
        beta = info.get("beta", None)
        col1.metric("Beta", f"{beta:.2f}" if beta else "N/A")

        # Implied Volatility (average of front-month calls)
        try:
            calls = stock.option_chain().calls
            iv = round(calls["impliedVolatility"].mean() * 100, 2)
        except:
            iv = None
        col2.metric("Implied Volatility (IV)", f"{iv:.2f}%" if iv else "N/A")

        # Expected Move (30-day)
        if iv and current_price:
            move_30d = calculate_expected_move(current_price, iv, 30)
            col3.metric("30d Expected Move", f"±${move_30d}" if move_30d else "N/A")
        else:
            col3.metric("30d Expected Move", "N/A")

        # Next Earnings Date
        try:
            earnings = stock.calendar.loc["Earnings Date"][0].strftime("%b %d, %Y")
        except:
            earnings = "N/A"
        col4.metric("Next Earnings", earnings)

    except Exception as e:
        st.error(f"Could not retrieve data. Error: {e}")
