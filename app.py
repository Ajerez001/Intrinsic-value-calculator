import streamlit as st
import yfinance as yf
from fredapi import Fred

FRED_API_KEY = "ef227271f5aef3df5c1a8970d24aabc2"

st.set_page_config(page_title="Intrinsic Value Calculator", layout="centered")
st.title("Intrinsic Value Calculator")

# --------- FUNCTIONS ---------

def fetch_stock_info(ticker):
    stock = yf.Ticker(ticker)
    try:
        info = stock.info
        logo_url = info.get("logo_url", "")
        name = info.get("longName", ticker.upper())
        current_price = info.get("currentPrice", 0.0)
        previous_close = info.get("previousClose", current_price)
        change = current_price - previous_close
        percent_change = (change / previous_close) * 100 if previous_close else 0

        # Safely fetch earnings date
        earnings_date = "N/A"
        try:
            cal = info.get("earningsDate")
            if isinstance(cal, (str, float, int)):
                earnings_date = str(cal)
            elif isinstance(cal, list) and len(cal) > 0:
                earnings_date = str(cal[0])
        except:
            earnings_date = "N/A"

        return {
            "name": name,
            "ticker": ticker.upper(),
            "price": current_price,
            "change": change,
            "percent_change": percent_change,
            "earnings_date": earnings_date,
            "logo": logo_url
        }
    except Exception as e:
        st.error(f"Error fetching stock info: {e}")
        return None

def get_discount_rate():
    try:
        fred = Fred(api_key=FRED_API_KEY)
        # Use Moody's Seasoned Aaa Corporate Bond Yield [AAA]
        rate = fred.get_series_latest_release('AAA').iloc[-1] / 100
        return round(rate, 4)
    except:
        return 0.045

def calculate_intrinsic_value(avg_eps, growth_rate, discount_rate, years=5):
    intrinsic_value = 0
    for i in range(1, years + 1):
        future_eps = avg_eps * ((1 + growth_rate) ** i)
        intrinsic_value += future_eps / ((1 + discount_rate) ** i)
    return round(intrinsic_value, 2)

# --------- APP LAYOUT ---------

ticker_input = st.text_input("Enter Stock Ticker", value="AAPL")

if ticker_input:
    stock = fetch_stock_info(ticker_input)

    if stock:
        col1, col2 = st.columns([1, 3])
        with col1:
            if stock["logo"]:
                st.image(stock["logo"], width=60)
        with col2:
            st.subheader(f"{stock['name']} ({stock['ticker']})")
            st.markdown(f"**Price:** ${stock['price']:.2f} ({stock['percent_change']:+.2f}%)")
            st.markdown(f"**Next Earnings Date:** {stock['earnings_date']}")

        st.divider()

        st.markdown("### Earnings Per Share Input")
        total_eps = st.number_input("Total EPS (last 4 quarters)", value=0.0)
        avg_eps = total_eps / 4

        growth_input = st.number_input("1-Year Growth Estimate (%)", value=10.0) / 100
        discount_rate = get_discount_rate()
        st.markdown(f"**Discount Rate (AAA Bond):** {discount_rate*100:.2f}%")

        if st.button("Calculate Intrinsic Value"):
            iv = calculate_intrinsic_value(avg_eps, growth_input, discount_rate)
            st.success(f"Intrinsic Value per Share: **${iv:.2f}**")

        with st.expander("Options Selling Decision Panel"):
            iv_input = st.number_input("Implied Volatility (IV %)", value=30.0)
            beta = st.number_input("Beta", value=1.0)
            expected_move = st.number_input("Expected Move ($)", value=5.0)
            premium = st.number_input("Put Option Premium ($)", value=1.50)

            st.markdown("Use this to assess if selling a put makes sense.")
            if premium >= 1.5 and iv_input >= 30:
                st.success("Conditions are favorable for selling puts.")
            else:
                st.warning("Consider waiting for higher IV or premium.")

st.markdown("---")
st.caption("Built with Streamlit | Data from Yahoo Finance and FRED")
