import streamlit as st
import yfinance as yf
from fredapi import Fred
import pandas as pd
import os
import json

# FRED API setup
FRED_API_KEY = "ef227271f5aef3df5c1a8970d24aabc2"
fred = Fred(api_key=FRED_API_KEY)

# --- FUNCTIONS ---
def get_aaa_corp_bond_rate():
    try:
        data = fred.get_series('AAA')
        return round(data.dropna().iloc[-1], 2)
    except Exception:
        return 5.0  # fallback

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

def calculate_intrinsic_value(eps, growth_rate_percent, discount_rate, years=10):
    growth_rate = growth_rate_percent / 100  # Convert percent to decimal
    intrinsic_value = 0
    for year in range(1, years + 1):
        future_eps = eps * ((1 + growth_rate) ** year)
        intrinsic_value += future_eps / ((1 + discount_rate) ** year)
    return round(intrinsic_value, 2)

def save_evaluation(data):
    path = "evaluations.json"
    evaluations = []
    if os.path.exists(path):
        with open(path, "r") as f:
            evaluations = json.load(f)
    evaluations.append(data)
    with open(path, "w") as f:
        json.dump(evaluations, f, indent=2)

def load_evaluations():
    if os.path.exists("evaluations.json"):
        with open("evaluations.json", "r") as f:
            return json.load(f)
    return []

# --- UI ---
st.title("Intrinsic Value Calculator")

ticker = st.text_input("Enter Stock Ticker Symbol (e.g., AAPL):")

if ticker:
    stock_info = get_stock_info(ticker.strip().upper())

    if stock_info:
        st.subheader(stock_info["longName"])
        st.write(f"Current Price: **${stock_info['currentPrice']}**")
        st.write(f"Earnings Date: {stock_info['earningsDate']}")

        eps = st.number_input("Total EPS (last 4 quarters)", min_value=0.0, step=0.01)
        growth_rate_input = st.number_input("Expected Growth Rate (%)", min_value=0.0, step=0.01)

        bond_rate = get_aaa_corp_bond_rate()
        st.write(f"Discount Rate (AAA Corporate Bond): **{bond_rate}%**")
        discount_rate = bond_rate / 100

        if eps and growth_rate_input:
            intrinsic_value = calculate_intrinsic_value(eps, growth_rate_input, discount_rate)
            margin_price = round(intrinsic_value * 0.8, 2)

            st.success(f"Intrinsic Value: ${intrinsic_value}")
            st.info(f"Buy Below: ${margin_price} (20% Margin of Safety)")

            if st.button("Save Evaluation"):
                save_evaluation({
                    "Ticker": ticker.upper(),
                    "Company": stock_info["longName"],
                    "EPS": eps,
                    "Growth Rate (%)": growth_rate_input,
                    "Discount Rate (%)": bond_rate,
                    "Intrinsic Value": intrinsic_value,
                    "Buy Below": margin_price
                })
                st.success("Saved!")

# View saved evaluations
if st.checkbox("View Saved Evaluations"):
    saved = load_evaluations()
    if saved:
        st.dataframe(pd.DataFrame(saved))
    else:
        st.info("No saved evaluations found.")
