import streamlit as st
import yfinance as yf
from fredapi import Fred

# Set Streamlit page configuration
st.set_page_config(page_title="Intrinsic Value Calculator", layout="wide")

st.title("Intrinsic Value Calculator (Graham Formula)")

# Input: Stock Ticker
ticker = st.text_input("Enter Stock Ticker (e.g., AAPL)", "")

if ticker:
    try:
        # Get stock data
        stock = yf.Ticker(ticker)
        eps_ttm = stock.info.get('trailingEps', None)
        shares = stock.info.get('sharesOutstanding', None)

        if eps_ttm is None:
            st.warning("Could not retrieve EPS (TTM).")
            st.stop()

        # Get AAA bond rate from FRED
        try:
            fred = Fred(api_key=st.secrets["FRED_API_KEY"])
            bond_yield = fred.get_series_latest_release('DAAA')[-1]
            bond_rate = round(float(bond_yield), 2)
        except Exception:
            st.warning("Could not fetch bond rate from FRED. Using fallback value of 4.4%.")
            bond_rate = 4.4

        # Manual growth rate input
        growth_estimate = st.number_input("Enter estimated growth rate (%)", value=10.0, step=0.5)

        # Graham formula
        intrinsic_value = (eps_ttm * (8.5 + 2 * growth_estimate) * 4.4) / bond_rate

        # Display values
        st.subheader("Results")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("EPS (TTM)", f"${eps_ttm:.2f}")
        col2.metric("Growth Estimate", f"{growth_estimate:.2f}%")
        col3.metric("AAA Bond Rate", f"{bond_rate:.2f}%")
        col4.metric("Intrinsic Value", f"${intrinsic_value:.2f}")

        # Live TradingView chart
        st.subheader("Live Market Chart")
        tradingview_html = f"""
        <iframe src="https://s.tradingview.com/widgetembed/?frameElementId=tradingview_{ticker}&symbol={ticker}&interval=D&hidesidetoolbar=1&symboledit=1&saveimage=1&toolbarbg=f1f3f6&studies=[]&theme=light&style=1&timezone=Etc/UTC&withdateranges=1&hideideas=1&allow_symbol_change=1&details=1&hotlist=1&calendar=1" 
        width="100%" height="500" frameborder="0" allowtransparency="true" scrolling="no" allowfullscreen></iframe>
        """
        st.components.v1.html(tradingview_html, height=500)

    except Exception as e:
        st.error(f"Could not retrieve data. Error: {e}")
t
