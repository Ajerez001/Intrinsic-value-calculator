import streamlit as st
import yfinance as yf
import requests
from fredapi import Fred

st.title("Intrinsic Value Calculator (Graham Formula)")

ticker = st.text_input("Enter Stock Ticker (e.g., AAPL)", "")

if ticker:
    try:
        # Get stock data
        stock = yf.Ticker(ticker)
        eps_ttm = stock.info.get('trailingEps', None)
        if not eps_ttm:
            st.warning("Could not retrieve EPS. Exiting.")
            st.stop()

        # FRED: Get AAA corporate bond rate
        fred = Fred(api_key=st.secrets["FRED_API_KEY"])
        try:
            bond_yield = fred.get_series_latest_release('DAAA')[-1]
            bond_rate = round(float(bond_yield), 2)
        except Exception:
            st.warning("Could not fetch bond rate. Using fallback 4.4%")
            bond_rate = 4.4

        # Yahoo via RapidAPI: Get growth estimate
        url = "https://yahoo-finance15.p.rapidapi.com/api/yahoo/qu/quote/" + ticker
        headers = {
            "X-RapidAPI-Key": st.secrets["RAPIDAPI_KEY"],
            "X-RapidAPI-Host": "yahoo-finance15.p.rapidapi.com"
        }

        response = requests.get(url, headers=headers)
        data = response.json()
        yahoo_growth = data.get('financialData', {}).get('earningsGrowth')

        if yahoo_growth is not None:
            growth_estimate = round(float(yahoo_growth) * 100, 2)
        else:
            st.warning("Could not retrieve growth estimate. Using fallback 10%.")
            growth_estimate = 10

        # Graham formula
        intrinsic_value = (eps_ttm * (8.5 + 2 * growth_estimate) * 4.4) / bond_rate

        st.write(f"EPS (TTM): {eps_ttm}")
        st.write(f"Estimated Growth Rate: {growth_estimate}%")
        st.write(f"AAA Bond Rate: {bond_rate}%")
        st.success(f"Intrinsic Value: ${intrinsic_value:.2f}")

    except Exception as e:
        st.error(f"Could not retrieve data. Error: {e}")
