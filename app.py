import streamlit as st
import yfinance as yf
from fredapi import Fred
import datetime

st.set_page_config(layout="wide")
st.title("Intrinsic Value & Options Insights")

# User input
ticker = st.text_input("Enter Stock Ticker (e.g., AAPL)", "").upper()

if ticker:
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        eps_ttm = info.get('trailingEps', None)
        shares = info.get('sharesOutstanding', None)
        beta = info.get('beta', 'N/A')
        iv = info.get('impliedVolatility', 'N/A')
        earnings = info.get('earningsDate', 'N/A')
        current_price = info.get('currentPrice', 0)

        # Get AAA bond rate from FRED
        try:
            fred = Fred(api_key=st.secrets["FRED_API_KEY"])
            bond_yield = fred.get_series_latest_release('DAAA')[-1]
            bond_rate = round(float(bond_yield), 2)
        except:
            bond_rate = 4.4
            st.warning("Using fallback bond rate: 4.4%")

        # User input for growth
        growth_rate = st.number_input("Enter estimated growth rate (%)", min_value=0.0, max_value=100.0, value=10.0)

        if eps_ttm:
            intrinsic_value = (eps_ttm * (8.5 + 2 * growth_rate) * 4.4) / bond_rate
            st.write(f"**EPS (TTM):** {eps_ttm}")
            st.write(f"**Growth Rate Used:** {growth_rate}%")
            st.write(f"**AAA Bond Rate:** {bond_rate}%")
            st.write(f"**Intrinsic Value:** ${intrinsic_value:.2f}")

            if intrinsic_value > current_price * 1.2:
                st.success("This stock appears **Undervalued**.")
            elif intrinsic_value < current_price * 0.8:
                st.error("This stock appears **Overvalued**.")
            else:
                st.info("This stock appears **Fairly Valued**.")

        # Options trading data
        st.subheader("Options Trading Snapshot")
        st.write(f"**Current Price:** ${current_price}")
        st.write(f"**Beta:** {beta}")
        st.write(f"**Implied Volatility:** {iv}")
        st.write(f"**Next Earnings Date:** {earnings}")

        # Expected move formula
        if iv and iv != 'N/A':
            try:
                expected_move = current_price * float(iv) * (1 / (252 ** 0.5))
                st.write(f"**1-week Expected Move:** ±${expected_move:.2f}")
            except:
                st.write("Could not compute expected move.")
        else:
            st.write("IV unavailable to estimate expected move.")

        # Live market chart
        st.subheader("Live Market Chart")
        st.line_chart(stock.history(period="5d")['Close'])

    except Exception as e:
        st.error(f"Could not retrieve data. Error: {e}")
