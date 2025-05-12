import streamlit as st
import yfinance as yf
import requests
from bs4 import BeautifulSoup
from fredapi import Fred

# Set up app title
st.title("Intrinsic Value Calculator (Graham Formula + Options Snapshot)")

# Ticker input
ticker = st.text_input("Enter Stock Ticker (e.g., AAPL)", "").upper()

def get_eps_ttm(ticker):
    try:
        url = f"https://finance.yahoo.com/quote/{ticker}/earnings"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        tables = soup.find_all('table')

        for table in tables:
            if 'EPS Actual' in table.text:
                rows = table.find_all('tr')[1:]
                eps_values = []
                for row in rows[:4]:
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        eps = cols[1].text.strip()
                        try:
                            eps_values.append(float(eps))
                        except:
                            continue
                return round(sum(eps_values), 2)
    except:
        return None

def get_next_year_growth_estimate(ticker):
    try:
        url = f"https://finance.yahoo.com/quote/{ticker}/analysis"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        tables = soup.find_all('table')

        for table in tables:
            if 'Growth Estimates' in table.text:
                rows = table.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 2 and 'Next Year' in cols[0].text:
                        growth = cols[1].text.strip().replace('%', '')
                        return round(float(growth), 2)
    except:
        return None

if ticker:
    try:
        # EPS
        eps_ttm = get_eps_ttm(ticker)
        if eps_ttm is None:
            st.warning("Could not fetch EPS from Yahoo. Using fallback EPS of 5.0.")
            eps_ttm = 5.0

        # Growth estimate
        growth_estimate = get_next_year_growth_estimate(ticker)
        if growth_estimate is None:
            st.warning("Could not fetch growth estimate. Using fallback growth rate of 10%.")
            growth_estimate = 10.0

        # Get bond rate from FRED
        try:
            fred = Fred(api_key=st.secrets["FRED_API_KEY"])
            bond_yield = fred.get_series_latest_release('DAAA')[-1]
            bond_rate = round(float(bond_yield), 2)
        except:
            st.warning("Could not fetch bond rate. Using fallback value of 4.4%.")
            bond_rate = 4.4

        # Graham formula
        intrinsic_value = (eps_ttm * (8.5 + 2 * growth_estimate) * 4.4) / bond_rate

        # Display
        st.subheader("Valuation Summary")
        st.write(f"**EPS (TTM)**: {eps_ttm}")
        st.write(f"**Growth Estimate (Next Year)**: {growth_estimate}%")
        st.write(f"**AAA Bond Rate**: {bond_rate}%")
        
        if intrinsic_value > 1.25 * yf.Ticker(ticker).info['currentPrice']:
            st.success(f"**Undervalued** — Intrinsic Value: ${intrinsic_value:.2f}")
        elif intrinsic_value < 0.8 * yf.Ticker(ticker).info['currentPrice']:
            st.error(f"**Overvalued** — Intrinsic Value: ${intrinsic_value:.2f}")
        else:
            st.warning(f"**Fairly Valued** — Intrinsic Value: ${intrinsic_value:.2f}")

    except Exception as e:
        st.error(f"Error processing ticker {ticker}: {e}")
