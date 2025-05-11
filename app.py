import streamlit as st
import yfinance as yf
import requests
from bs4 import BeautifulSoup

# --- Graham formula function ---
def graham_formula(eps, growth_rate, aaa_yield):
    return round(eps * (8.5 + 2 * growth_rate) * (4.4 / aaa_yield), 2)

# --- Get trailing 12-month EPS ---
def get_eps(ticker):
    stock = yf.Ticker(ticker)
    try:
        return stock.info['trailingEps']
    except KeyError:
        return None

# --- Get Yahoo analyst growth estimate ---
def get_yahoo_growth(ticker):
    url = f"https://finance.yahoo.com/quote/{ticker}/analysis"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    try:
        td = soup.find(text="Next 5 Years (per annum)").find_parent("td").find_next_sibling("td")
        return float(td.text.strip('%'))  # convert from % to number
    except:
        return None

# --- Placeholder for Simply Wall St estimate (manual for now) ---
def get_simply_wall_st_growth(ticker):
    # In a real version, we’d scrape this — placeholder for now
    return st.number_input("Enter Simply Wall St growth estimate (%)", min_value=0.0, max_value=100.0, value=10.0)

# --- Get AAA corporate bond yield (static or FRED later) ---
def get_aaa_yield():
    # Placeholder static value (you can replace with FRED API later)
    return 4.4  # typical base

# --- Streamlit UI ---
st.title("Intrinsic Value Calculator (Graham Formula)")

ticker = st.text_input("Enter Stock Ticker (e.g., AAPL)", value="AAPL")

if ticker:
    eps = get_eps(ticker)
    yahoo_growth = get_yahoo_growth(ticker)
    sws_growth = get_simply_wall_st_growth(ticker)
    aaa_yield = get_aaa_yield()

    if eps is not None and yahoo_growth is not None:
    growth_rate = (yahoo_growth + sws_growth) / 2
    intrinsic_value = graham_formula(eps, growth_rate, aaa_yield)

    st.subheader("Results")
    st.write(f"**EPS (TTM)**: {eps}")
    st.write(f"**Avg Growth Rate**: {growth_rate:.2f}%")
    st.write(f"**AAA Bond Yield**: {aaa_yield}%")
    st.write(f"**Intrinsic Value**: ${intrinsic_value}")
else:
    st.warning("Could not retrieve EPS or growth data. Please check the stock ticker and try again.")
the
    st.subheader("Results")
    st.write(f"**EPS (TTM)**: {eps}")
    st.write(f"**Avg Growth Rate**: {growth_rate:.2f}%")
    st.write(f"**AAA Bond Yield**: {aaa_yield}%")
    st.write(f"**Intrinsic Value**: ${intrinsic_value}")
else:
    st.warning("Could not retrieve EPS or growth data. Please check the stock ticker and try again.")


        st.subheader("Results")
        st.write(f"**EPS (TTM)**: {eps}")
        st.write(f"**Avg Growth Rate**: {growth_rate:.2f}%")
        st.write(f"**AAA Bond Yield**: {aaa_yield}%")
        st.write(f"**Intrinsic Value**: ${intrinsic_value}")
    else:
        st.warning("Could not retrieve all data. Check the ticker or try again.")
I
