import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import json
import os
from fredapi import Fred

# FRED API Key
FRED_API_KEY = "ef227271f5aef3df5c1a8970d24aabc2"
fred = Fred(api_key=FRED_API_KEY)

SAVE_FILE = "saved_valuations.json"

st.set_page_config(page_title="Intrinsic Value Calculator", layout="centered")
st.title("Intrinsic Value Calculator")

# Function to search for ticker from company name using Yahoo autocomplete
def search_ticker(query):
    url = f"https://query1.finance.yahoo.com/v1/finance/search?q={query}"
    try:
        response = requests.get(url)
        data = response.json()
        if "quotes" in data and len(data["quotes"]) > 0:
            return data["quotes"][0]["symbol"]
    except Exception as e:
        st.error(f"Error searching for ticker: {e}")
    return ""

# Input box for ticker or company name
user_input = st.text_input("Enter stock ticker or company name", "").strip()

ticker = ""
company_name = ""

if user_input:
    # Try fetching as ticker, else search
    try:
        ticker = search_ticker(user_input) if not user_input.isupper() else user_input
        if not ticker:
            raise ValueError("Ticker not found.")
        data = yf.Ticker(ticker)
        info = data.info
        ticker = info.get("symbol", ticker.upper())
        company_name = info.get("shortName", "")
        current_price = info["currentPrice"]
        logo_url = info.get("logo_url", "")
        st.subheader(f"{company_name} ({ticker})")
        st.image(logo_url, width=60)
        st.write(f"Current Price: ${current_price:.2f}")
    except Exception as e:
        st.error(f"Error fetching stock info: {e}")
        ticker = ""

# Manual EPS total input
eps_total = st.number_input("Enter total EPS for the last 4 quarters (e.g., 2.99)", min_value=0.0, format="%.2f")
growth_rate = st.number_input("Enter estimated annual growth rate (e.g., 8% = 0.08)", min_value=0.0, format="%.4f")

# Fetch current AAA bond yield
try:
    aaa_series = fred.get_series("AAA")
    latest_aaa_rate = aaa_series.dropna().iloc[-1] / 100  # convert to decimal
    st.write(f"AAA Corporate Bond Rate: **{latest_aaa_rate:.2%}**")
except Exception as e:
    st.error(f"Error loading AAA bond rate: {e}")
    latest_aaa_rate = 0.0545  # fallback

# Intrinsic Value formula
def calculate_intrinsic_value(eps, growth, bond_rate):
    return eps * (8.5 + 2 * (growth * 100)) * 4.4 / (bond_rate * 100)

# Calculate intrinsic value
if st.button("Calculate Intrinsic Value") and ticker:
    intrinsic_value = calculate_intrinsic_value(eps_total, growth_rate, latest_aaa_rate)
    margin_price = intrinsic_value * 0.8

    st.success(f"Intrinsic Value: ${intrinsic_value:,.2f}")
    st.write(f"Buy Price With 20% Margin of Safety: **${margin_price:,.2f}**")

    if st.button("Save This Evaluation"):
        entry = {
            "ticker": ticker,
            "company": company_name,
            "eps_total": eps_total,
            "growth_rate": growth_rate,
            "intrinsic_value": intrinsic_value,
            "margin_price": margin_price
        }
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, "r") as f:
                saved_data = json.load(f)
        else:
            saved_data = []
        saved_data.append(entry)
        with open(SAVE_FILE, "w") as f:
            json.dump(saved_data, f, indent=4)
        st.success("Evaluation saved!")

# View saved evaluations
if st.checkbox("View Saved Evaluations"):
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            saved_data = json.load(f)
        for entry in saved_data[::-1]:
            st.write(f"**{entry['company']} ({entry['ticker']})**")
            st.write(f"- EPS: {entry['eps_total']}")
            st.write(f"- Growth Rate: {entry['growth_rate'] * 100:.2f}%")
            st.write(f"- Intrinsic Value: ${entry['intrinsic_value']:,.2f}")
            st.write(f"- Buy Price w/ Margin: ${entry['margin_price']:,.2f}")
            st.markdown("---")
    else:
        st.info("No saved evaluations yet.")
