import streamlit as st
import yfinance as yf
from fredapi import Fred
from datetime import datetime
import plotly.graph_objs as go

# --- Streamlit App Title ---
st.set_page_config(page_title="Intrinsic Value & Options Tool", layout="wide")
st.title("Intrinsic Value Calculator + Options Snapshot")

# --- User Inputs ---
ticker = st.text_input("Enter Stock Ticker (e.g., AAPL)", "")
manual_growth = st.number_input("Enter Expected Annual Growth Rate (%)", min_value=0.0, max_value=100.0, value=10.0, step=0.1)

if ticker:
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        eps = info.get("trailingEps", None)
        current_price = info.get("currentPrice", None)
        shares = info.get("sharesOutstanding", None)

        # --- FRED AAA Bond Rate ---
        try:
            fred = Fred(api_key=st.secrets["FRED_API_KEY"])
            bond_yield = fred.get_series_latest_release('DAAA')[-1]
            bond_rate = round(float(bond_yield), 2)
        except:
            st.warning("Could not fetch AAA bond rate. Using fallback value of 4.4%.")
            bond_rate = 4.4

        # --- Graham Formula Calculation ---
        if eps and current_price:
            intrinsic_value = (eps * (8.5 + 2 * manual_growth) * 4.4) / bond_rate

            # Display values
            st.subheader("Graham Valuation")
            st.write(f"**EPS (TTM):** ${eps}")
            st.write(f"**Growth Estimate:** {manual_growth}%")
            st.write(f"**AAA Bond Rate:** {bond_rate}%")
            st.write(f"**Intrinsic Value:** ${intrinsic_value:.2f}")
            st.write(f"**Current Price:** ${current_price:.2f}")

            # Valuation Label
            if intrinsic_value > current_price * 1.2:
                st.success("Undervalued")
            elif current_price >= intrinsic_value * 0.8 and current_price <= intrinsic_value * 1.2:
                st.info("Fairly Valued")
            else:
                st.error("Overvalued")
        else:
            st.warning("Missing EPS or current price.")

        # --- Live Market Chart ---
        st.subheader("Live Stock Chart")
        hist = stock.history(period="1mo", interval="1d")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist.index, y=hist["Close"], mode="lines", name=ticker))
        fig.update_layout(title=f"{ticker} - Last 30 Days", xaxis_title="Date", yaxis_title="Price", height=400)
        st.plotly_chart(fig, use_container_width=True)

        # --- Options Trading Snapshot ---
        st.subheader("Options Trading Snapshot")

        iv = info.get('impliedVolatility', None)
        beta = info.get('beta', None)
        earnings_date = info.get('earningsDate', None)

        st.write(f"**Beta:** {beta if beta is not None else 'Not Available'}")
        st.write(f"**Implied Volatility:** {round(iv*100, 2)}%" if iv else "Implied Volatility: Not Available")

        if earnings_date:
            if isinstance(earnings_date, list) and len(earnings_date) > 0:
                earnings_display = earnings_date[0].strftime('%B %d, %Y')
            elif isinstance(earnings_date, datetime):
                earnings_display = earnings_date.strftime('%B %d, %Y')
            else:
                earnings_display = "Not Available"
        else:
            earnings_display = "Not Available"

        st.write(f"**Next Earnings Date:** {earnings_display}")

        # Expected move calculation
        if iv and current_price:
            try:
                expected_move = current_price * float(iv) * (1 / (252 ** 0.5))
                st.write(f"**1-week Expected Move:** ±${expected_move:.2f}")
            except:
                st.write("Could not compute expected move.")
        else:
            st.write("Expected Move: Not Available")

    except Exception as e:
        st.error(f"Could not retrieve data. Error: {e}")
