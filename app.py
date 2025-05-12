import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
from fredapi import Fred
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title("Intrinsic Value Calculator with Options Snapshot")

ticker = st.text_input("Enter Stock Ticker (e.g., AAPL)").upper()

if ticker:
    try:
        # Load ticker info
        stock = yf.Ticker(ticker)
        info = stock.info
        logo_url = info.get("logo_url", None)

        # Display logo if available
        if logo_url:
            st.image(logo_url, width=100)

        # EPS actuals: extract from Yahoo Finance earnings page
        earnings_url = f"https://finance.yahoo.com/quote/{ticker}/earnings"
        response = requests.get(earnings_url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")

        eps_tags = soup.find_all("td", string=lambda text: text and "EPS actual" in text)
        eps_values = []
        for tag in eps_tags[:4]:  # Get latest 4
            next_td = tag.find_next("td")
            try:
                eps_values.append(float(next_td.text.strip()))
            except:
                continue

        eps_ttm = round(sum(eps_values), 2) if eps_values else None

        # Growth estimate from summary page
        summary_url = f"https://finance.yahoo.com/quote/{ticker}"
        response = requests.get(summary_url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")
        growth_estimate = None

        for row in soup.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) == 2 and "Next Year" in cells[0].text and "%" in cells[1].text:
                try:
                    growth_estimate = float(cells[1].text.replace("%", "").strip())
                    break
                except:
                    continue

        # Use fallback if either value is missing
        if eps_ttm is None:
            st.warning("Could not extract EPS Actuals. Using fallback EPS = 5.")
            eps_ttm = 5
        if growth_estimate is None:
            st.warning("Could not extract growth estimate. Using fallback 10%.")
            growth_estimate = 10

        # FRED AAA bond rate
        fred = Fred(api_key=st.secrets["FRED_API_KEY"])
        try:
            bond_yield = fred.get_series_latest_release('DAAA')[-1]
            bond_rate = round(float(bond_yield), 2)
        except:
            st.warning("Could not retrieve AAA bond rate. Using fallback of 4.4%.")
            bond_rate = 4.4

        # Graham formula
        intrinsic_value = (eps_ttm * (8.5 + 2 * growth_estimate) * 4.4) / bond_rate

        # Valuation color label
        current_price = info.get("regularMarketPrice", None)
        if current_price:
            if intrinsic_value > current_price * 1.1:
                valuation_status = "Undervalued"
                color = "green"
            elif intrinsic_value < current_price * 0.9:
                valuation_status = "Overvalued"
                color = "red"
            else:
                valuation_status = "Fairly Valued"
                color = "orange"
        else:
            valuation_status = "N/A"
            color = "gray"

        # Display metrics
        st.subheader("Valuation Metrics")
        st.markdown(f"**EPS (TTM from last 4 actuals):** {eps_ttm}")
        st.markdown(f"**Growth Estimate (Next Year):** {growth_estimate}%")
        st.markdown(f"**AAA Bond Rate:** {bond_rate}%")
        st.markdown(f"**Current Price:** ${current_price}")
        st.markdown(f"**Intrinsic Value:** ${intrinsic_value:.2f}")
        st.markdown(f"**Valuation:** <span style='color:{color}'>{valuation_status}</span>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Could not retrieve data: {e}")
