import streamlit as st
import yfinance as yf
from fredapi import Fred

# Set up the title
st.title("Intrinsic Value Calculator (Graham Formula)")

# Get user input for stock ticker
ticker = st.text_input("Enter Stock Ticker (e.g., AAPL)", "")

if ticker:
    try:
        # Fetch stock data from Yahoo Finance
        stock = yf.Ticker(ticker)
        earnings_history = stock.earnings_history

        # Get last 4 actual EPS values from earnings history
        last_4_eps = [e['epsactual'] for e in earnings_history[-4:] if 'epsactual' in e and e['epsactual'] is not None]
        eps_ttm = sum(last_4_eps)

        # Get company logo if available
        try:
            logo_url = stock.info.get("logo_url")
            if logo_url:
                st.image(logo_url, width=100)
        except Exception:
            st.warning("Logo not available.")

        # Get shares outstanding from Yahoo Finance
        shares = stock.info['sharesOutstanding']

        # Placeholder values for bond rate and growth rate
        try:
            # Fetch the most recent AAA bond yield from FRED API
            fred = Fred(api_key=st.secrets["FRED_API_KEY"])
            bond_yield = fred.get_series_latest_release('DAAA')[-1]
            bond_rate = round(float(bond_yield), 2)
        except Exception as e:
            st.warning("Could not fetch bond rate from FRED. Please enter it manually.")
            bond_rate = st.number_input("Enter bond rate", value=4.4)

        # Get growth estimate from user input
        growth_estimate = st.number_input("Enter growth rate estimate", value=10.0)

        # Calculate intrinsic value using Graham Formula
        intrinsic_value = (eps_ttm * (8.5 + 2 * growth_estimate) * 4.4) / bond_rate

        # Show calculated data
        st.write(f"EPS (TTM): {eps_ttm}")
        st.write(f"Estimated Growth: {growth_estimate}%")
        st.write(f"AAA Bond Rate: {bond_rate}%")
        st.success(f"Intrinsic Value: ${intrinsic_value:.2f}")

        # Display stock data (company name, price, etc.)
        st.write(f"Company Name: {stock.info.get('longName', 'N/A')}")
        st.write(f"Current Price: ${stock.info.get('currentPrice', 'N/A')}")
        
    except Exception as e:
        st.error(f"Could not retrieve data. Error: {e}")
