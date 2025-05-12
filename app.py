import streamlit as st
import yfinance as yf
import pandas as pd
from fredapi import Fred
import plotly.graph_objs as go
import datetime
import requests

# Setup
st.set_page_config(page_title="Stock Valuation & Options Snapshot", layout="wide")
st.title("Stock Valuation & Options Trading Snapshot")

def get_company_logo(ticker, company_name):
    domain = company_name.lower().split(" ")[0] + ".com"
    clearbit_url = f"https://logo.clearbit.com/{domain}"
    try:
        r = requests.get(clearbit_url)
        if r.status_code == 200:
            return clearbit_url
    except:
        pass
    return "https://upload.wikimedia.org/wikipedia/commons/a/ac/No_image_available.svg"

ticker = st.text_input("Enter Stock Ticker (e.g., AAPL)", "").upper()

if ticker:
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        company_name = info.get("longName", ticker)
        eps_ttm = info.get("trailingEps", None)
        current_price = info.get("currentPrice", 0)

        # Logo
        logo_url = get_company_logo(ticker, company_name)
        st.image(logo_url, width=100, caption=company_name)

        # Growth input
        if eps_ttm is None or eps_ttm <= 0:
            raise ValueError("EPS is unavailable or invalid.")
        growth_rate = st.number_input("Enter Estimated Growth Rate (%)", min_value=0.0, max_value=100.0, value=10.0)

        # AAA bond yield from FRED
        fred = Fred(api_key=st.secrets["FRED_API_KEY"])
        try:
            bond_yield = fred.get_series_latest_release('DAAA')[-1]
            bond_rate = round(float(bond_yield), 2)
        except:
            st.warning("Could not fetch bond rate. Using fallback value of 4.4%.")
            bond_rate = 4.4

        # Intrinsic value
        intrinsic_value = (eps_ttm * (8.5 + 2 * growth_rate) * 4.4) / bond_rate
        if intrinsic_value > current_price * 1.1:
            color = "green"
            valuation_msg = "Undervalued"
        elif intrinsic_value < current_price * 0.9:
            color = "red"
            valuation_msg = "Overvalued"
        else:
            color = "orange"
            valuation_msg = "Fairly Valued"

        st.subheader("Intrinsic Valuation")
        st.markdown(f"**EPS (TTM):** {eps_ttm}")
        st.markdown(f"**Growth Rate:** {growth_rate}%")
        st.markdown(f"**AAA Bond Yield:** {bond_rate}%")
        st.markdown(f"**Intrinsic Value:** ${intrinsic_value:.2f}")
        st.markdown(f"<span style='color:{color}; font-size: 20px'><strong>{valuation_msg}</strong></span>", unsafe_allow_html=True)

        # Live Chart (Robinhood Style)
        st.subheader("Live Market Chart")
        hist = stock.history(period="5d", interval="5m")
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=hist.index,
            y=hist["Close"],
            mode='lines',
            line=dict(color="#00C805", width=2),
            hoverinfo='x+y',
            name=ticker
        ))

        fig.update_layout(
            template="plotly_dark",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(title="", showgrid=False),
            yaxis=dict(title="Price", showgrid=False),
            margin=dict(l=0, r=0, t=30, b=20),
            height=400,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

        # Options Snapshot
        st.subheader("Options Trading Snapshot")
        iv = info.get("impliedVolatility", None)
        beta = info.get("beta", None)
        earnings_date = info.get("earningsDate", None)
        expected_move = (current_price * iv * (2.71828 ** 0.5)) if iv else None

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Implied Volatility", f"{iv:.2%}" if iv else "N/A")
        col2.metric("Beta", f"{beta:.2f}" if beta else "N/A")
        col3.metric("Expected Move (±)", f"${expected_move:.2f}" if expected_move else "N/A")
        if earnings_date:
            earnings_display = pd.to_datetime(earnings_date[0]).strftime("%Y-%m-%d") if isinstance(earnings_date, list) else pd.to_datetime(earnings_date).strftime("%Y-%m-%d")
            col4.metric("Next Earnings", earnings_display)
        else:
            col4.metric("Next Earnings", "N/A")

    except Exception as e:
        st.error(f"Could not retrieve data. Error: {e}")
