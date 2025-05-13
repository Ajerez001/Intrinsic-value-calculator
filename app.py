import streamlit as st
import yfinance as yf
from fredapi import Fred

# FRED API Key
FRED_API_KEY = "ef227271f5aef3df5c1a8970d24aabc2"
fred = Fred(api_key=FRED_API_KEY)

# Function to get AAA corporate bond rate
def get_aaa_corp_bond_rate():
    try:
        data = fred.get_series_latest_release('AAA')
        return round(data[-1] / 100, 4)  # Convert to decimal
    except Exception as e:
        st.error(f"Error loading AAA corporate bond rate: {e}")
        return None

# Intrinsic value calculation using EPS (per share)
def calculate_intrinsic_value(eps, growth_rate, discount_rate, years=10):
    intrinsic_value_per_share = 0
    for year in range(1, years + 1):
        future_eps = eps * ((1 + growth_rate) ** year)
        discounted_eps = future_eps / ((1 + discount_rate) ** year)
        intrinsic_value_per_share += discounted_eps
    return round(intrinsic_value_per_share, 2)

# Streamlit App
st.title("Intrinsic Value Calculator")

ticker = st.text_input("Enter stock ticker (e.g., AAPL)").upper()

if ticker:
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Validate ticker
        if not info or "shortName" not in info:
            raise ValueError("Invalid or unknown ticker symbol.")

        # Display stock info
        st.image(info.get("logo_url", ""), width=100)
        st.subheader(f"{info.get('shortName', '')} ({ticker})")
        st.write(f"**Current Price:** ${info.get('currentPrice', 'N/A')}")
        earnings_date = info.get("earningsDate")
        if earnings_date:
            st.write(f"**Next Earnings Date:** {earnings_date[0]}")
        else:
            st.write("**Next Earnings Date:** N/A")

        # EPS input
        eps_input = st.number_input("Enter EPS total from last 4 quarters", min_value=0.0, value=2.99)

        # Growth rate input in %
        growth_input_pct = st.number_input("Expected annual EPS growth rate (%)", min_value=0.0, max_value=100.0, value=8.0)
        growth_input = growth_input_pct / 100  # Convert to decimal

        # Get discount rate from AAA bond
        discount_rate = get_aaa_corp_bond_rate()
        if discount_rate:
            st.write(f"**Discount Rate (AAA Corporate Bond):** {discount_rate * 100:.2f}%")

            # Calculate intrinsic value
            intrinsic_value = calculate_intrinsic_value(eps_input, growth_input, discount_rate)
            st.success(f"**Intrinsic Value (per share):** ${intrinsic_value}")

            # Margin of safety (20%)
            fair_value_threshold = intrinsic_value * 0.8
            st.info(f"**Buy Price (20% Margin of Safety):** ${fair_value_threshold:.2f}")

            current_price = info.get("currentPrice")
            if current_price:
                if current_price < fair_value_threshold:
                    st.success("This stock is trading at or below its fair value range.")
                else:
                    st.warning("This stock is not currently trading at a discount.")
        else:
            st.error("Failed to retrieve discount rate.")

    except Exception as e:
        st.error(f"Error fetching stock info: {e}")
