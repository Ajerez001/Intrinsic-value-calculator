import streamlit as st
import yfinance as yf
import requests
import pandas as pd

# --- API Keys ---
FRED_API_KEY = "ef227271f5aef3df5c1a8970d24aabc2"
FMP_API_KEY = "ZYWFtyBgxO0qoNNAMMiCDDc2TIdoIQWt"

# --- Function to Get AAA Corporate Bond Rate ---
def get_aaa_bond_rate():
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id=DAAA&api_key={FRED_API_KEY}&file_type=json"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            observations = data.get("observations", [])
            for obs in reversed(observations):
                value = obs.get("value")
                if value and value != ".":
                    return float(value) / 100  # Convert percentage to decimal
    except Exception as e:
        st.error(f"Error fetching AAA bond rate: {e}")
    return None

# --- Function to Calculate Intrinsic Value ---
def calculate_intrinsic_value(eps, growth_rate, bond_rate):
    try:
        intrinsic_value = eps * (8.5 + 2 * growth_rate) * 4.4 / (bond_rate * 100)
        return round(intrinsic_value, 2)
    except Exception as e:
        st.error(f"Error in intrinsic value calculation: {e}")
        return 0

# --- Function to Fetch Stock Information ---
def get_stock_info(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "name": info.get("shortName", "N/A"),
            "price": info.get("regularMarketPrice", 0),
            "logo_url": info.get("logo_url", ""),
            "previous_close": info.get("regularMarketPreviousClose", 0),
            "earnings_date": info.get("earningsDate", "N/A")
        }
    except Exception as e:
        st.error(f"Error fetching stock info: {e}")
        return None

# --- Function to Fetch Earnings History from FMP ---
def get_earnings_history_fmp(ticker, api_key):
    url = f"https://financialmodelingprep.com/api/v3/historical/earning_calendar/{ticker}?limit=6&apikey={api_key}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Error loading earnings history: {e}")
    return None

# --- Streamlit App Configuration ---
st.set_page_config(page_title="Intrinsic Value Calculator", layout="wide")
st.title("📈 Intrinsic Value Calculator")

# --- User Input for Stock Ticker ---
ticker_input = st.text_input("Enter Stock Ticker (e.g., AAPL)", value="AAPL").upper()

if ticker_input:
    stock_info = get_stock_info(ticker_input)

    if stock_info:
        # --- Display Stock Information ---
        col1, col2 = st.columns([1, 5])
        with col1:
            if stock_info["logo_url"]:
                st.image(stock_info["logo_url"], width=80)
        with col2:
            st.subheader(f"{stock_info['name']} ({ticker_input})")
            st.markdown(f"**Current Price:** ${stock_info['price']}")
            st.markdown(f"**Previous Close:** ${stock_info['previous_close']}")
            st.markdown(f"**Earnings Date:** {stock_info['earnings_date']}")

        st.divider()

        # --- Manual Inputs for EPS and Growth Rate ---
        eps_input = st.number_input("Enter Total EPS for Last 4 Quarters", min_value=0.0, step=0.01)
        growth_input = st.number_input("Enter Expected Annual Growth Rate (%)", min_value=0.0, step=0.5)

        if eps_input and growth_input:
            bond_rate = get_aaa_bond_rate()
            if bond_rate:
                st.markdown(f"**AAA Corporate Bond Rate:** {bond_rate:.2%}")
                intrinsic_value = calculate_intrinsic_value(eps_input, growth_input, bond_rate)
                st.markdown(f"### 💰 Intrinsic Value: ${intrinsic_value}")

                # --- Fair Value Range with 20% Margin of Safety ---
                buy_below = round(intrinsic_value * 0.8, 2)
                if stock_info["price"] < buy_below:
                    st.success(f"**Buy Zone:** Current price is more than 20% below intrinsic value (${buy_below})")
                else:
                    st.warning(f"**Overvalued:** Price is not yet 20% below intrinsic value (${buy_below})")
            else:
                st.error("Unable to fetch AAA corporate bond rate.")

        # --- Display Earnings History ---
        st.markdown("### 🗓️ Earnings History")
        earnings_data = get_earnings_history_fmp(ticker_input, FMP_API_KEY)

        if earnings_data:
            df = pd.DataFrame([{
                "Date": e.get("date", ""),
                "EPS Actual": e.get("eps", "N/A"),
                "EPS Estimate": e.get("epsEstimated", "N/A")
            } for e in earnings_data])
            st.dataframe(df)
        else:
            st.info("No earnings history available.")
