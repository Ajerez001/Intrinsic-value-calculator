import streamlit as st
import yfinance as yf
from fredapi import Fred
import requests
from bs4 import BeautifulSoup

st.title("Intrinsic Value Calculator (Graham Formula)")

ticker = st.text_input("Enter Stock Ticker (e.g., AAPL)", "")

if ticker:
    try:
        stock = yf.Ticker(ticker)
        eps_ttm = stock.info['trailingEps']

        # Get bond rate from FRED
        fred = Fred(api_key=st.secrets["FRED_API_KEY"])
        try:
            bond_yield = fred.get_series_latest_release('DAAA')[-1]
            bond_rate = round(float(bond_yield), 2)
        except:
            st.warning("Could not fetch bond rate. Using fallback value of 4.4%.")
            bond_rate = 4.4

        # --- Get Yahoo growth estimate ---
        yahoo_url = f"https://finance.yahoo.com/quote/{ticker}/analysis"
        yahoo_response = requests.get(yahoo_url, headers={"User-Agent": "Mozilla/5.0"})
        yahoo_soup = BeautifulSoup(yahoo_response.text, 'html.parser')
        yahoo_growth = None
        try:
            td_tags = yahoo_soup.find_all("td")
            for i, tag in enumerate(td_tags):
                if "Next Year" in tag.text:
                    yahoo_growth = float(td_tags[i + 1].text.replace('%', '').strip())
                    break
        except:
            pass

        # --- Get Simply Wall St growth forecast ---
        sws_url = f"https://simplywall.st/stocks/us/{ticker.lower()}"
        sws_response = requests.get(sws_url, headers={"User-Agent": "Mozilla/5.0"})
        sws_soup = BeautifulSoup(sws_response.text, 'html.parser')
        sws_growth = None
        try:
            for tag in sws_soup.find_all("p"):
                if "Earnings are forecast" in tag.text:
                    percent_text = tag.text.split("grow")[1].split("%")[0]
                    sws_growth = float(percent_text.strip())
                    break
        except:
            pass

        # Combine both growth estimates
        if yahoo_growth and sws_growth:
            growth_rate = (yahoo_growth + sws_growth) / 2
        elif yahoo_growth:
            growth_rate = yahoo_growth
        elif sws_growth:
            growth_rate = sws_growth
        else:
            growth_rate = 10  # fallback

        intrinsic_value = (eps_ttm * (8.5 + 2 * growth_rate) * 4.4) / bond_rate

        st.write(f"EPS (TTM): {eps_ttm}")
        st.write(f"Estimated Growth Rate: {growth_rate:.2f}%")
        st.write(f"AAA Bond Rate: {bond_rate}%")
        st.success(f"Intrinsic Value: ${intrinsic_value:.2f}")

    except Exception as e:
        st.error(f"Could not retrieve data. Error: {e}")
