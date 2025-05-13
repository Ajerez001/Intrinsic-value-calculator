import streamlit as st
import yfinance as yf
import requests
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="Stock Snapshot", layout="wide")

st.title("Intrinsic Value & Option Snapshot")

# Input
ticker = st.text_input("Enter Ticker Symbol", value="AAPL").upper()

if ticker:
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Fetch current price and daily change
        todays_data = stock.history(period='1d')
        price = todays_data['Close'][0]
        prev_close = todays_data['Close'][0] - todays_data['Close'][0] * info['regularMarketChangePercent'] / 100
        change = price - prev_close
        change_percent = info['regularMarketChangePercent']
        price_color = "green" if change > 0 else "red"

        # Earnings date
        earnings = stock.calendar
        earnings_date = earnings.loc['Earnings Date'][0] if 'Earnings Date' in earnings.index else "N/A"

        # Fetch logo using Clearbit fallback
        company_name = info.get('shortName', ticker)
        domain_lookup = f"https://autocomplete.clearbit.com/v1/companies/suggest?query={company_name}"
        logo_url = None
        try:
            logo_response = requests.get(domain_lookup)
            if logo_response.status_code == 200:
                data = logo_response.json()
                if data:
                    logo_url = data[0].get("logo")
        except Exception:
            pass

        # Layout
        col1, col2 = st.columns([1, 6])
        with col1:
            if logo_url:
                st.image(logo_url, width=64)
        with col2:
            st.markdown(f"### **{company_name}** ({ticker})")
            st.markdown(
                f"<h3 style='margin: 0;'>${price:,.2f} "
                f"<span style='color:{price_color}; font-size: 0.8em;'>"
                f"{change:+.2f} ({change_percent:+.2f}%)</span></h3>",
                unsafe_allow_html=True
            )
            st.markdown(f"**Earnings Date:** {earnings_date.strftime('%b %d, %Y') if earnings_date != 'N/A' else 'N/A'}")

    except Exception as e:
        st.error(f"Could not load data for {ticker}. Error: {str(e)}")
