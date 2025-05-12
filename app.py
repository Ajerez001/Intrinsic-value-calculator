import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from fredapi import Fred

st.set_page_config(page_title="Intrinsic Value Calculator", layout="wide")

st.title("Intrinsic Value Calculator (Graham Formula)")

ticker = st.text_input("Enter Stock Ticker (e.g., AAPL)", "").upper()

# Display logo and company name
if ticker:
    stock = yf.Ticker(ticker)
    try:
        info = stock.info
        st.subheader(info.get("shortName", ""))
        logo_url = info.get("logo_url")
        if logo_url:
            st.image(logo_url, width=100)
    except:
        st.warning("Company info/logo not available.")

    # Pull EPS actuals from RapidAPI
    headers = {
        "X-RapidAPI-Key": st.secrets["YAHOO_FINANCE_API_KEY"],
        "X-RapidAPI-Host": "yahoo-finance15.p.rapidapi.com"
    }
    earnings_url = f"https://yahoo-finance15.p.rapidapi.com/api/yahoo/qu/earnings/{ticker}"
    eps_ttm = 0.0
    try:
        response = requests.get(earnings_url, headers=headers)
        data = response.json()
        eps_list = [float(x["epsactual"]) for x in data["earnings"]["financialsChart"]["yearly"][-1:] +
                    data["earnings"]["financialsChart"]["quarterly"][-3:] if x["epsactual"] is not None]
        eps_ttm = round(sum(eps_list), 2)
    except:
        st.warning("Could not fetch EPS actuals. EPS (TTM) set to 0.")

    # Get bond rate from FRED
    try:
        fred = Fred(api_key=st.secrets["FRED_API_KEY"])
        bond_yield = fred.get_series_latest_release('DAAA')[-1]
        bond_rate = round(float(bond_yield), 2)
        st.write(f"AAA Bond Rate (Auto): {bond_rate}%")
    except:
        bond_rate = st.number_input("AAA Bond Rate (Manual)", min_value=1.0, max_value=15.0, value=4.4, step=0.1)

    # Get growth estimate from Yahoo (fallback: manual input)
    try:
        growth_estimate = float(info.get("earningsQuarterlyGrowth") or 0) * 100
        if growth_estimate == 0:
            raise ValueError
        st.write(f"Estimated Growth (Auto): {growth_estimate:.2f}%")
    except:
        growth_estimate = st.number_input("Growth Rate Estimate (Manual)", min_value=0.0, max_value=100.0, value=10.0)

    if eps_ttm:
        intrinsic_value = round((eps_ttm * (8.5 + 2 * growth_estimate) * 4.4) / bond_rate, 2)

        st.write(f"EPS (TTM): {eps_ttm}")
        st.write(f"Growth Estimate: {growth_estimate:.2f}%")

        current_price = info.get("currentPrice", 0)
        st.write(f"Current Price: ${current_price}")

        # Valuation color
        if intrinsic_value > current_price * 1.1:
            st.markdown(f"### Intrinsic Value: <span style='color:green;'>${intrinsic_value}</span>", unsafe_allow_html=True)
        elif intrinsic_value < current_price * 0.9:
            st.markdown(f"### Intrinsic Value: <span style='color:red;'>${intrinsic_value}</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"### Intrinsic Value: <span style='color:orange;'>${intrinsic_value}</span>", unsafe_allow_html=True)
    else:
        st.error("EPS (TTM) is not available for this stock.")
