import streamlit as st
import yfinance as yf
from fredapi import Fred
import pandas as pd
import os
import json

# Load FRED API key
FRED_API_KEY = "ef227271f5aef3df5c1a8970d24aabc2"
fred = Fred(api_key=FRED_API_KEY)

# Function to fetch AAA corporate bond rate
def get_aaa_corp_bond_rate():
    try:
        data = fred.get_series('AAA')
        return round(data.dropna().iloc[-1], 2)
    except Exception as e:
        st.error(f"Error fetching AAA Corporate Bond Rate: {e}")
        return None

# Function to fetch company info
def get_stock_info(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "longName": info.get("longName", "N/A"),
            "currentPrice": info.get("currentPrice", 0),
            "logo_url": info.get("logo_url", ""),
            "earningsDate": info.get("earningsDate", "N/A")
        }
    except Exception as e:
        st.error(f"Error fetching stock info: {e}")
        return None

# Function to calculate intrinsic value using simplified DCF
def calculate_intrinsic_value(eps, growth_rate, discount_rate, years=10):
    intrinsic_value = 0
    for year in range(1, years + 1):
        future_eps = eps * ((1 + growth_rate) ** year)
        discounted_eps = future_eps / ((1 + discount_rate) ** year)
        intrinsic_value += discounted_eps
    return round(intrinsic_value, 2)

# Save evaluations to local JSON
def save_evaluation(data):
    if not os.path.exists("evaluations.json"):
        with open("evaluations.json", "w") as f:
            json.dump([], f)
    with open("evaluations.json", "r") as f:
        evaluations = json.load(f)
    evaluations.append(data)
    with open("evaluations.json", "w") as f:
        json.dump(evaluations, f, indent=2)

# Load evaluations
def load_evaluations():
    if os.path.exists("evaluations.json"):
        with open("evaluations.json", "r") as f:
            return json.load(f)
    return []

# Streamlit UI
st.title("Intrinsic Value Calculator")

# Input for ticker or company name
user_input = st.text_input("Enter Company Ticker (e.g., AAPL):")

if user_input:
    stock_info = get_stock_info(user_input.upper())
    if stock_info:
        st.subheader(stock_info["longName"])
        st.markdown(f"**Current Price:** ${stock_info['currentPrice']}")
        st.markdown(f"**Next Earnings Date:** {stock_info['earningsDate']}")

        # Manual Inputs
        eps_input = st.number_input("Enter total EPS for last 4 quarters (e.g., 2.99):", min_value=0.0, step=0.01)
        growth_rate = st.number_input("Expected Annual Growth Rate (e.g., 0.08 for 8%):", min_value=0.0, step=0.01)

        # Fetch AAA bond rate
        discount_rate = get_aaa_corp_bond_rate()
        if discount_rate:
            st.markdown(f"**Discount Rate (AAA Corporate Bond):** {discount_rate}%")
            discount_rate_decimal = discount_rate / 100

            if eps_input > 0 and growth_rate > 0:
                intrinsic_value = calculate_intrinsic_value(eps_input, growth_rate, discount_rate_decimal)
                margin_price = round(intrinsic_value * 0.8, 2)
                st.success(f"Intrinsic Value: ${intrinsic_value}")
                st.info(f"Buy only if stock is under: ${margin_price} (20% margin of safety)")

                if st.button("Save Evaluation"):
                    eval_data = {
                        "Company": stock_info["longName"],
                        "Ticker": user_input.upper(),
                        "EPS": eps_input,
                        "Growth Rate": growth_rate,
                        "Discount Rate": discount_rate,
                        "Intrinsic Value": intrinsic_value
                    }
                    save_evaluation(eval_data)
                    st.success("Evaluation saved!")

# View saved evaluations
st.markdown("---")
if st.checkbox("View Saved Evaluations"):
    evaluations = load_evaluations()
    if evaluations:
        st.write(pd.DataFrame(evaluations))
    else:
        st.write("No saved evaluations found.")
