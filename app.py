import streamlit as st
import yfinance as yf
import pandas as pd
from fredapi import Fred
import json
import os

# Set up API keys
FRED_API_KEY = "ef227271f5aef3df5c1a8970d24aabc2"
fred = Fred(api_key=FRED_API_KEY)

# File to save evaluations
SAVE_FILE = "saved_valuations.json"

st.set_page_config(page_title="Intrinsic Value Calculator", layout="centered")
st.title("Intrinsic Value Calculator")

# Ticker/company input
user_input = st.text_input("Enter stock ticker or company name (e.g., AAPL or Apple)", "").strip()

ticker = ""
company_name = ""

if user_input:
    try:
        data = yf.Ticker(user_input)
        info = data.info
        ticker = info.get("symbol", user_input.upper())
        company_name = info.get("shortName", "")
        current_price = info["currentPrice"]
        logo_url = info.get("logo_url", "")
        st.subheader(f"{company_name} ({ticker})")
        st.image(logo_url, width=60)
        st.write(f"Current Price: ${current_price:.2f}")
    except Exception as e:
        st.error(f"Error fetching stock info: {e}")
        ticker = ""

# EPS and growth input
eps_total = st.number_input("Enter total EPS for the last 4 quarters (e.g., 2.99)", min_value=0.0, format="%.2f")
growth_rate = st.number_input("Enter estimated annual growth rate (e.g., 8% = 0.08)", min_value=0.0, format="%.4f")

# AAA corporate bond rate
try:
    aaa_yield = fred.get_series_latest_release('AAA')[-1] / 100  # Convert to decimal
except Exception as e:
    st.error(f"Error fetching AAA bond rate: {e}")
    aaa_yield = 0.0545  # Fallback value
st.write(f"AAA Corporate Bond Rate: **{aaa_yield:.2%}**")

# Intrinsic value calculation
def calculate_intrinsic_value(eps, growth, bond_rate):
    return eps * (8.5 + 2 * (growth * 100)) * 4.4 / (bond_rate * 100)

if st.button("Calculate Intrinsic Value") and ticker:
    intrinsic_value = calculate_intrinsic_value(eps_total, growth_rate, aaa_yield)
    margin_price = intrinsic_value * 0.8  # 20% margin of safety

    st.success(f"Intrinsic Value: ${intrinsic_value:,.2f}")
    st.write(f"Buy Price With 20% Margin of Safety: **${margin_price:,.2f}**")

    # Save option
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

# Load saved evaluations
if st.checkbox("View Saved Evaluations"):
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            saved_data = json.load(f)
        for entry in saved_data[::-1]:
            st.write(f"**{entry['company']} ({entry['ticker']})**")
            st.write(f"- EPS (last 4 quarters): {entry['eps_total']}")
            st.write(f"- Growth Rate: {entry['growth_rate'] * 100:.2f}%")
            st.write(f"- Intrinsic Value: ${entry['intrinsic_value']:,.2f}")
            st.write(f"- Buy Price with 20% Margin: ${entry['margin_price']:,.2f}")
            st.markdown("---")
    else:
        st.info("No saved evaluations yet.")
