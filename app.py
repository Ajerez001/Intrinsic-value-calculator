import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
from fredapi import Fred

# Set your FRED API Key
FRED_API_KEY = "ef227271f5aef3df5c1a8970d24aabc2"
fred = Fred(api_key=FRED_API_KEY)

st.set_page_config(page_title="Intrinsic Value Calculator", layout="centered")
st.title("Intrinsic Value Calculator")

# Input for Ticker or Company Name
user_input = st.text_input("Enter Company Ticker or Name (e.g., AAPL or Apple)", "").strip()

# EPS & Growth Inputs
eps_input = st.number_input("Enter total EPS from last 4 quarters (e.g. 2.99)", min_value=0.0, format="%.2f")
growth_input = st.number_input("Enter estimated annual growth rate (e.g. 0.08 for 8%)", min_value=0.0, format="%.4f")

# Fetch AAA corporate bond rate
try:
    aaa_yield = fred.get_series_latest_release('AAA')[-1]
except Exception as e:
    st.error(f"Error fetching AAA bond rate: {e}")
    aaa_yield = 0.0545  # fallback value
st.write(f"AAA Corporate Bond Rate: **{aaa_yield:.2%}**")

# Calculate intrinsic value
def calculate_intrinsic_value(eps, growth, discount_rate):
    try:
        intrinsic_value = eps * (8.5 + 2 * (growth * 100)) * 4.4 / (discount_rate * 100)
        return intrinsic_value
    except ZeroDivisionError:
        return 0

# Process ticker input
if user_input:
    try:
        ticker_obj = yf.Ticker(user_input)
        info = ticker_obj.info
        company_name = info.get("longName") or user_input.upper()
        current_price = ticker_obj.history(period="1d")["Close"].iloc[-1]

        st.subheader(f"{company_name} ({user_input.upper()})")
        st.write(f"Current Price: **${current_price:.2f}**")

        if eps_input > 0 and growth_input > 0:
            intrinsic_value = calculate_intrinsic_value(eps_input, growth_input, aaa_yield * 100)
            st.success(f"Intrinsic Value: **${intrinsic_value:.2f}**")

            # Fair Value Range (20% Margin of Safety)
            margin_price = intrinsic_value * 0.8
            st.write(f"Buy if price is below: **${margin_price:.2f}**")

            # Save Evaluation
            if st.button("Save Evaluation"):
                row = {
                    "Date": datetime.date.today(),
                    "Ticker": user_input.upper(),
                    "Company": company_name,
                    "EPS (TTM)": eps_input,
                    "Growth Rate": growth_input,
                    "AAA Yield": aaa_yield,
                    "Intrinsic Value": intrinsic_value,
                    "Current Price": current_price,
                    "Buy Below (20% MoS)": margin_price
                }
                try:
                    df_existing = pd.read_csv("saved_evaluations.csv")
                    df_new = pd.DataFrame([row])
                    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
                except FileNotFoundError:
                    df_combined = pd.DataFrame([row])

                df_combined.to_csv("saved_evaluations.csv", index=False)
                st.success("Evaluation saved to `saved_evaluations.csv`")

        else:
            st.info("Please enter valid EPS and growth rate.")

    except Exception as e:
        st.error(f"Error fetching stock info: {e}")

# View Saved Evaluations
st.markdown("---")
st.subheader("Saved Evaluations")

try:
    df_saved = pd.read_csv("saved_evaluations.csv")
    st.dataframe(df_saved, use_container_width=True)
except FileNotFoundError:
    st.info("No saved evaluations found yet.")
