import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import json
import os
import random

# Constants and directories
CLIENTS_FILE = "clients.json"
DATADIR = "userdata"
os.makedirs(DATADIR, exist_ok=True)

# Helper: Load all clients
def load_clients():
    if not os.path.exists(CLIENTS_FILE):
        return {}
    with open(CLIENTS_FILE) as f:
        return json.load(f)

# Helper: Save all clients
def save_clients(clients):
    with open(CLIENTS_FILE, "w") as f:
        json.dump(clients, f, indent=2)

# Helper: Save user data (portfolio, goals, insurance)
def save_userdata(mobile, key, data):
    filepath = os.path.join(DATADIR, f"{mobile}_{key}.json")
    with open(filepath, "w") as f:
        json.dump(data, f)

def load_userdata(mobile, key):
    filepath = os.path.join(DATADIR, f"{mobile}_{key}.json")
    if os.path.exists(filepath):
        with open(filepath) as f:
            return json.load(f)
    return None

def clear_userdata(mobile):
    for key in ["portfolio", "financialgoals", "insurance"]:
        filepath = os.path.join(DATADIR, f"{mobile}_{key}.json")
        if os.path.exists(filepath):
            os.remove(filepath)

# Parse CAMS JSON to extract portfolio data
def parse_cams_json(file):
    import json
    from collections import defaultdict

    data = json.load(file)
    records = data.get("TRXN_DETAILS", [])
    holdings = defaultdict(lambda: {"units": 0.0, "latest_nav": 0.0, "scheme_name": ""})

    for record in records:
        scheme_name = record.get("Scheme Name", "N/A")
        units = float(record.get("Units", 0))
        nav = float(record.get("Price", 0))
        desc = record.get("Desc", "").lower()

        # Purchase adds units, redemption/switch/subtract units
        if "purchase" in desc:
            holdings[scheme_name]["units"] += units
        elif "redemption" in desc or "switch" in desc:
            holdings[scheme_name]["units"] -= units
        else:
            holdings[scheme_name]["units"] += units  # treat other as addition

        holdings[scheme_name]["latest_nav"] = nav  # assumes sorted by date or always use latest

        holdings[scheme_name]["scheme_name"] = scheme_name

    portfolio = []
    total_value = 0.0
    for h in holdings.values():
        value = h["units"] * h["latest_nav"]
        portfolio.append({
            "Scheme Name": h["scheme_name"],
            "Total Units": h["units"],
            "Current NAV": h["latest_nav"],
            "Current Value": value
        })
        total_value += value
    return portfolio, total_value


# Show portfolio in Streamlit with CAMS JSON upload
def show_cams_portfolio():
    st.header("Upload CAMS JSON Portfolio File")
    uploaded_file = st.file_uploader("Choose your CAMS JSON file", type="json")
    if uploaded_file is not None:
        portfolio, total = parse_cams_json(uploaded_file)
        if len(portfolio) > 0:
            df = pd.DataFrame(portfolio)
            st.subheader("Your Portfolio Holdings")
            st.dataframe(df)
            st.write(f"**Total Portfolio Value:** ₹{total:,.2f}")
        else:
            st.write("No holdings data found in the file.")

def save_portfolio(mobile, portfolio):
    save_userdata(mobile, "portfolio", portfolio)

def load_portfolio(mobile):
    return load_userdata(mobile, "portfolio")

def display_portfolio(portfolio):
    if portfolio and len(portfolio) > 0:
        df = pd.DataFrame(portfolio)
        st.dataframe(df)
        total_val = sum(item.get("Current Value", 0) for item in portfolio)
        st.write(f"**Total Portfolio Value:** ₹{total_val:,.2f}")
    else:
        st.write("No portfolio data found.")

def main_app(user_mobile):
    st.sidebar.write(f"Logged in as: {user_mobile}")

    menu = ["Home", "View Portfolio", "Upload CAMS Portfolio", "Logout"]
    choice = st.sidebar.selectbox("Select Activity", menu)

    if choice == "Home":
        st.write("Welcome to your personalized Portfolio Tracker")

    elif choice == "View Portfolio":
        st.header("Your Portfolio")
        portfolio = load_portfolio(user_mobile)
        display_portfolio(portfolio)

    elif choice == "Upload CAMS Portfolio":
        show_cams_portfolio()

    elif choice == "Logout":
        st.success("You have been logged out.")
        st.experimental_rerun()

def authenticate_user(mobile, otp):
    valid_otp = "123456"
    return otp == valid_otp

def send_otp(mobile):
    st.write(f"OTP sent to {mobile} (simulated)")

def user_login():
    st.header("User Login")
    mobile = st.text_input("Enter Mobile Number", max_chars=10)
    if st.button("Send OTP"):
        send_otp(mobile)
        st.session_state['otp'] = "123456"
        st.success("OTP sent to your mobile.")

    otp = st.text_input("Enter OTP")
    if otp and 'otp' in st.session_state:
        if authenticate_user(mobile, otp):
            st.success("Login successful.")
            return mobile
        else:
            st.error("Incorrect OTP entered.")
    return None

if __name__ == "__main__":
    if "user_mobile" not in st.session_state:
        user_mobile = user_login()
        if user_mobile:
            st.session_state['user_mobile'] = user_mobile
            main_app(user_mobile)
    else:
        main_app(st.session_state['user_mobile'])
