import streamlit as st
import yfinance as yf
import requests
from datetime import datetime
from fredapi import Fred

FRED_API_KEY = "ef227271f5aef3df5c1a8970d24aabc2"

st.set_page_config(page_title="Intrinsic Value Calculator", layout="centered")
st.title("Intrinsic Value Calculator")

# ------------------ Function Definitions ------------------

def fetch_stock_info(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info

    try:
        logo_url = info.get("logo_url", "")
        name = info.get("longName", ticker)
        current_price = info.get("currentPrice", 0)
        previous_close = info.get("previousClose", current_price)
        daily_change = current_price - previous_close
        percent_change = (daily_change / previous_close) * 100 if previous_close else 0

        # Pull next earnings date from earnings_dates instead of calendar
        try:
            earnings_dates = stock.earnings_dates
            if not earnings_dates.empty:
                next_earnings = earnings_dates.index[0].strftime('%Y-%m-%d')
            else:
                next_earnings = "N/A"
        except:
            next_earnings = "N/A"

        return {
            "name": name,
            "ticker": ticker.upper(),
            "price": current_price,
            "change": daily_change,
            "percent_change": percent_change,
            "earnings_date": next_earnings,
            "logo": logo_url
        }
    except Exception as e:
        st.error(f"Error fetching stock info: {e}")
        return None

def get_fed_rate():
    fred = Fred(api_key=FRED_API_KEY)
    try:
        rate = fred.get_series_latest_release('GS10').iloc[-1] / 100
        return round(rate, 4)
    except:
        return 0.045

def calculate_intrinsic_value(eps_list, growth_rate, discount_rate, years=5):
    avg_eps = sum(eps_list) / len(eps_list)
    intrinsic_value = 0
    for i in range(1, years + 1):
        future_eps = avg_eps * ((1 + growth_rate) ** i)
        intrinsic_value += future_eps / ((1 + discount_rate) ** i)
    return round(intrinsic_value, 2)

# ------------------ UI Layout ------------------

ticker_input = st.text_input("Enter Stock Ticker", value="AAPL")

if ticker_input:
    stock_data = fetch_stock_info(ticker_input)

    if stock_data:
        col1, col2 = st.columns([1, 3])
        with col1:
            if stock_data['logo']:
                st.image(stock_data['logo'], width=60)
        with col2:
            st.subheader(f"{stock_data['name']} ({stock_data['ticker']})")
            st.markdown(
                f"**Price:** ${stock_data['price']:.2f} ({stock_data['percent_change']:+.2f}%)")
            st.markdown(f"**Next Earnings Date:** {stock_data['earnings_date']}")

        st.divider()

        st.markdown("### EPS Actuals (last 4 quarters)")
        eps_1 = st.number_input("EPS Q1", value=0.0)
        eps_2 = st.number_input("EPS Q2", value=0.0)
        eps_3 = st.number_input("EPS Q3", value=0.0)
        eps_4 = st.number_input("EPS Q4", value=0.0)

        eps_list = [eps_1, eps_2, eps_3, eps_4]

        growth_input = st.number_input("1-Year Growth Estimate (%)", value=10.0) / 100

        discount_rate = get_fed_rate()
        st.markdown(f"**Discount Rate (10Y Treasury):** {discount_rate*100:.2f}%")

        if st.button("Calculate Intrinsic Value"):
            iv = calculate_intrinsic_value(eps_list, growth_input, discount_rate)
            st.success(f"Intrinsic Value per Share: **${iv:.2f}**")

        with st.expander("Options Selling Decision Panel"):
            iv_input = st.number_input("Implied Volatility (IV %)", value=30.0)
            beta = st.number_input("Beta", value=1.0)
            expected_move = st.number_input("Expected Move ($)", value=5.0)
            premium = st.number_input("Put Option Premium ($)", value=1.50)

            st.markdown("This section can help guide your decision to sell a cash-secured put.")
            if premium >= 1.5 and iv_input >= 30:
                st.success("Conditions look favorable for selling puts.")
            else:
                st.warning("You may want to wait for higher premiums or IV.")

st.markdown("---")
st.caption("Built with Streamlit | Data from Yahoo Finance and FRED")
