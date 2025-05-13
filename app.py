import streamlit as st
import yfinance as yf
from fredapi import Fred
import pandas as pd
import os
import json

# Set your FRED API Key
FRED_API_KEY = "ef227271f5aef3df5c1a8970d24aabc2"
fred = Fred(api_key=FRED_API_KEY)

# Function to get AAA Corporate Bond Rate
def get_aaa_corp_bond_rate():
    try:
        data = fred.get_series('AAA')
        return round(data.dropna().iloc[-1], 2)
    except Exception as e:
        st.error(f"Error fetching bond rate: {e}")
        return 5.0  # fallback value

# Function to fetch stock data
def get_stock_info(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "longName": info.get("longName", ticker.upper()),
            "currentPrice": info.get("currentPrice", 0.0),
            "earningsDate": info.get("earningsDate", "N/A")
        }
    except:
        return None

# Intrinsic value formula
def calculate_intrinsic_value(eps, growth_rate, discount_rate, years=10):
    intrinsic_value = 0
    for year in range(1, years + 1):
        future_eps = eps * ((1 + growth_rate) ** year)
        intrinsic_value += future_eps / ((1 + discount_rate) ** year)
    return round(intrinsic_value, 2)

# Save evaluation
def save_evaluation(data):
    path = "evaluations.json"
    if os.path.exists(path):
        with open(path, "r") as f:
            evaluations = json.load(f)
    else:
        evaluations = []
    evaluations.append(data)
    with open(path, "w") as f:
        json.dump(evaluations, f, indent=2)

# Load evaluations
def load_evaluations():
    if os.path.exists("evaluations.json"):
        with open("evaluations.json", "r") as f:
            return json.load(f)
    return []

# --- STREAMLIT UI ---
st.title("Intrinsic Value Calculator")

ticker_input = st.text_input("Enter Stock Ticker Symbol (e.g., AAPL):")

if ticker_input:
    stock_info = get_stock_info(ticker_input.strip().upper())

    if stock_info:
        st.subheader(stock_info["longName"])
        st.write(f"Current Price: **${stock_info['currentPrice']}**")
        st.write(f"Next Earnings Date: {stock_info['earningsDate']}")

        eps_input = st.number_input("Enter total EPS from last 4 quarters (e.g., 2.99):", min_value=0.0, step=0.01)
        growth_input = st.number_input("Expected Growth Rate (e.g., 0.08 for 8%):", min_value=0.0, step=0.01)

        bond_rate = get_aaa_corp_bond_rate()
        st.write(f"Discount Rate (AAA Corp Bond): **{bond_rate}%**")
        discount_rate = bond_rate / 100

        if eps_input and growth_input:
            intrinsic = calculate_intrinsic_value(eps_input, growth_input, discount_rate)
            buy_price = round(intrinsic * 0.8, 2)

            st.success(f"Intrinsic Value: ${intrinsic}")
            st.info(f"Buy only if stock is below: ${buy_price} (20% margin of safety)")

            if st.button("Save Evaluation"):
                save_evaluation({
                    "Ticker": ticker_input.upper(),
                    "Company": stock_info["longName"],
                    "EPS": eps_input,
                    "Growth Rate": growth_input,
                    "Discount Rate": bond_rate,
                    "Intrinsic Value": intrinsic,
                    "Buy Below": buy_price
                })
                st.success("Evaluation saved!")

# View Saved Evaluations
st.markdown("---")
if st.checkbox("View Saved Evaluations"):
    data = load_evaluations()
    if data:
        st.dataframe(pd.DataFrame(data))
    else:
        st.info("No evaluations saved yet.")
