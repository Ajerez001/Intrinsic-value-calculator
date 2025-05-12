import streamlit as st
import yfinance as yf
import requests
import pandas as pd

# Display title of the app
st.title("Intrinsic Value Calculator (Graham Formula)")

ticker = st.text_input("Enter Stock Ticker (e.g., AAPL)", "")

if ticker:
    try:
        # Fetch stock data using yfinance
        stock = yf.Ticker(ticker)
        shares = stock.info['sharesOutstanding']
        eps_ttm = stock.info['trailingEps']

        # Fetch company logo
        company_logo_url = f"https://logo.clearbit.com/{stock.info['symbol']}.com"

        # Placeholder values for bond rate and growth
        from fredapi import Fred
        fred = Fred(api_key=st.secrets["FRED_API_KEY"])

        # Fetch AAA bond yield from FRED
        try:
            bond_yield = fred.get_series_latest_release('DAAA')[-1]
            bond_rate = round(float(bond_yield), 2)
        except Exception as e:
            st.warning("Could not fetch bond rate from FRED. Please enter it manually.")
            bond_rate = st.number_input("Enter Bond Rate (e.g., 4.4)", value=4.4)

        # Fetch earnings data from Yahoo Finance API (RapidAPI)
        url = "https://yahoo-finance-real-time1.p.rapidapi.com/calendar/get-events"
        params = {
            "entityIdType": "earnings",
            "sortType": "ASC",
            "sortField": "startdatetime",
            "region": "US",
            "size": "4",  # Limit to the last 4 earnings
            "lang": "en-US",
            "offset": "0",
            "includeFields": '["ticker", "companyshortname", "eventname", "startdatetime", "startdatetimetype", "epsestimate", "epsactual", "epssurprisepct", "timeZoneShortName", "gmtOffsetMilliSeconds"]'
        }
        
        headers = {
            "X-RapidAPI-Host": "yahoo-finance-real-time1.p.rapidapi.com",
            "X-RapidAPI-Key": st.secrets["YAHOO_FINANCE_API_KEY"]  # Make sure to add your API key here
        }

        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            earnings_data = response.json()
            eps_actuals = [event.get('epsactual') for event in earnings_data.get('calendar', []) if event.get('epsactual')]
            
            # Calculate the sum of the last 4 EPS actuals
            if len(eps_actuals) >= 4:
                total_eps = sum([float(eps) for eps in eps_actuals[:4]])
            else:
                total_eps = sum([float(eps) for eps in eps_actuals])

            # Fetch the growth estimate for next year (this can be tricky, so we will use a fallback if it's not available)
            growth_estimate = stock.info.get('growthEstimate', None)

            if growth_estimate is None:
                growth_estimate = st.number_input("Enter Growth Estimate (e.g., 10%)", value=10)

        else:
            st.error("Could not retrieve earnings data from Yahoo Finance API.")
            total_eps = 0
            growth_estimate = st.number_input("Enter Growth Estimate (e.g., 10%)", value=10)
            bond_rate = st.number_input("Enter Bond Rate (e.g., 4.4)", value=4.4)

        # Graham Formula Calculation
        intrinsic_value = (total_eps * (8.5 + 2 * growth_estimate) * 4.4) / bond_rate

        # Display Results
        st.image(company_logo_url, use_column_width=True)
        st.write(f"EPS (TTM): {eps_ttm}")
        st.write(f"Total EPS (from last 4 earnings): {total_eps}")
        st.write(f"Estimated Growth: {growth_estimate}%")
        st.write(f"AAA Bond Rate: {bond_rate}%")
        st.success(f"Intrinsic Value: ${intrinsic_value:.2f}")

    except Exception as e:
        st.error(f"Could not retrieve data. Error: {e}")
