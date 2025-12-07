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

# -------- Registration and Authentication Logic -----------

def register_page():
    st.header("Register as New Client")
    with st.form("register_form", clear_on_submit=True):
        name = st.text_input("Name")
        address = st.text_area("Address")
        phone = st.text_input("Phone Number")
        email = st.text_input("Email ID")
        income_bracket = st.selectbox("Income Bracket", ["<5 Lakh", "5-10 Lakh", "10-25 Lakh", "25+ Lakh"])
        age_bracket = st.selectbox("Age Bracket", ["<25", "25-35", "35-50", "50+"])
        submit = st.form_submit_button("Submit")
    if submit:
        if name and address and phone and email:
            st.session_state.new_reg = {
                "name": name,
                "address": address,
                "phone": phone,
                "email": email,
                "income_bracket": income_bracket,
                "age_bracket": age_bracket
            }
            st.success("Basic details submitted. Proceed to create User ID and Password below.")
        else:
            st.error("Please complete all fields in the form.")

    if st.session_state.get("new_reg"):
        with st.form("create_userid"):
            user_id = st.text_input("Choose User ID")
            password = st.text_input("Choose Password", type="password")
            create_btn = st.form_submit_button("Create Account")
        if create_btn:
            clients = load_clients()
            # Use phone number as the unique key
            phone = st.session_state.new_reg["phone"]
            if phone in clients:
                st.error("Mobile number already registered.")
            elif any(u.get("user_id") == user_id for u in clients.values()):
                st.error("User ID already in use.")
            else:
                clients[phone] = {
                    **st.session_state.new_reg,
                    "user_id": user_id,
                    "password": password,
                    "registered": True
                }
                save_clients(clients)
                st.success("Registration complete! Now use your registered phone number to log in via OTP.")
                del st.session_state["new_reg"]

# ----------- OTP Login and Existing User Flow -----------

if "otpdata" not in st.session_state:
    st.session_state.otpdata = {}
if "loggedin" not in st.session_state:
    st.session_state.loggedin = False

def generate_otp():
    return random.randint(100000, 999999)

def send_dummy_otp(mobile):
    otp = generate_otp()
    st.session_state.otpdata[mobile] = {"otp": otp, "expires": datetime.now() + timedelta(minutes=5)}
    st.sidebar.success(f"Dummy OTP for mobile is {otp}")
    return otp

def verify_otp(mobile, entered_otp):
    otpinfo = st.session_state.otpdata.get(mobile, None)
    if not otpinfo:
        return False, "No OTP sent for this number."
    if datetime.now() > otpinfo["expires"]:
        return False, "OTP has expired."
    if otpinfo["otp"] != entered_otp:
        return False, "Incorrect OTP."
    return True, "OTP Verified successfully!"

def loginsidebar():
    st.sidebar.title("Login - OTP Authentication")
    clients = load_clients()
    mobile = st.sidebar.text_input("Enter your registered Mobile Number")
    if st.sidebar.button("Send OTP"):
        if mobile in clients and clients[mobile].get("registered"):
            send_dummy_otp(mobile)
        else:
            st.sidebar.error("Mobile number not registered.")
    otpinput = st.sidebar.text_input("Enter OTP")
    if st.sidebar.button("Verify OTP"):
        if mobile and otpinput:
            try:
                entered_otp = int(otpinput)
            except ValueError:
                st.sidebar.error("OTP must be a number.")
                return False
            isvalid, message = verify_otp(mobile, entered_otp)
            if isvalid:
                st.sidebar.success(message)
                st.session_state.loggedin = True
                st.session_state.usermobile = mobile
                load_userspecific_data(mobile)
                return True
            else:
                st.sidebar.error(message)
                return False
        else:
            st.sidebar.error("Please enter both Mobile Number and OTP.")
            return False
    return st.session_state.get("loggedin", False)

def logoutsidebar():
    if st.sidebar.button("Logout"):
        user = st.session_state.get("usermobile")
        if user:
            clear_userdata(user)
        st.session_state.clear()
        st.rerun()

def load_userspecific_data(mobile):
    portfolio = load_userdata(mobile, "portfolio")
    if portfolio:
        st.session_state.portfoliodata = portfolio
    financialgoals = load_userdata(mobile, "financialgoals")
    if financialgoals:
        st.session_state.financialgoals = financialgoals
    insurance = load_userdata(mobile, "insurance")
    if insurance:
        st.session_state.insurancedata = insurance

# --------- App Pages: Portfolio, Insurance, Goals ---------

def homepagecontent():
    st.markdown(
        '<div class="header-box">Welcome to Capital Cartel</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        """
        <div class="content-box"><h3>About Us</h3>
        <p>Capital Cartel is a leading provider of Mutual Fund and Insurance solutions, helping clients achieve their financial goals with expert personalized guidance.</p>
        <h3>Services</h3>
        <ul>
        <li style="color:#FF6F00"><b>Mutual Fund Advisory</b></li>
        <li style="color:#FF6F00"><b>Insurance: Health, Life, Vehicle</b></li>
        <li style="color:#FF6F00"><b>Financial Planning & Tracking</b></li>
        </ul></div>
        <div class="content-box">
        <h3>Contact Information</h3>
        <b>Capital Cartel Pvt Ltd</b><br>
        123, Financial Estate, Sector 44, Gurgaon, Haryana, India<br>
        <b>Email:</b> info@capitalcartel.com<br>
        <b>Phone:</b> +91 99999 88888<br>
        <b>Website:</b> www.capitalcartel.com
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown("---")

def portfoliotracker():
    st.markdown('<div class="header-box">Portfolio Tracker</div>', unsafe_allow_html=True)
    st.write("Upload your investment details CSV file below.")
    uploadedfile = st.file_uploader("Upload Portfolio CSV", type="csv", key="portfolio_uploader")
    if uploadedfile is not None:
        df = pd.read_csv(uploadedfile)
        st.session_state.portfoliodata = df.to_dict()
    if "portfoliodata" in st.session_state:
        df = pd.DataFrame(st.session_state.portfoliodata)
        df = df.rename(columns={"Scheme Name": "Investment Category", "Investment Amount": "Amount"})
        df['Amount'] = df['Amount'].apply(lambda x: f"{x:,.0f}")
        st.markdown('<div class="content-box"><h4>Investment Details</h4></div>', unsafe_allow_html=True)
        st.dataframe(df)
        summary = df.groupby("Investment Category")["Amount"].apply(lambda x: sum(int(i.replace(",", "")) for i in x))
        if not summary.empty:
            st.markdown('<div class="content-box"><h4>Portfolio Distribution</h4></div>', unsafe_allow_html=True)
            fig, ax = plt.subplots()
            ax.pie(summary, labels=summary.index, autopct='%1.1f%%', startangle=90, colors=[
                "#FF6F00", "#757575", "#FFD180", "#B0BEC5", "#FFB74D", "#E0E0E0", "#F57C00"
            ])
            ax.axis('equal')
            st.pyplot(fig)
            totalamount = summary.sum()
            st.markdown(f'<div class="content-box"><b>Total Portfolio Amount</b>: {totalamount:,.0f}</div>', unsafe_allow_html=True)
        mobile = st.session_state.get("usermobile")
        if mobile and "portfoliodata" in st.session_state:
            save_userdata(mobile, "portfolio", st.session_state.portfoliodata)

def insurancepolicies():
    st.markdown('<div class="header-box">Insurance Policies</div>', unsafe_allow_html=True)
    st.write("Upload your insurance policies CSV below.")
    uploadedfile = st.file_uploader("Upload Insurance Policies CSV", type="csv", key="insurance_uploader")
    if uploadedfile is not None:
        df = pd.read_csv(uploadedfile)
        st.session_state.insurancedata = df.to_dict()
    if "insurancedata" in st.session_state:
        df = pd.DataFrame(st.session_state.insurancedata)
        df["Premium Amount"] = df["Premium Amount"].apply(lambda x: f"{x:,.0f}")
        df["Due Date"] = pd.to_datetime(df["Due Date"], errors="coerce")
        df["Due Date"] = df["Due Date"].dt.strftime('%d-%b-%Y')
        st.markdown('<div class="content-box"><h4>All Policies</h4></div>', unsafe_allow_html=True)
        st.dataframe(df)
        now = datetime.now()
        dfdue = pd.to_datetime(df["Due Date"], format='%d-%b-%Y', errors="coerce")
        mask = (dfdue - now).dt.days < 30
        mask &= (dfdue - now).dt.days >= 0
        upcoming = df[mask]
        if not upcoming.empty:
            st.markdown('<div class="content-box"><h4>Policy Due Soon</h4></div>', unsafe_allow_html=True)
            for idx, row in upcoming.iterrows():
                st.warning(f"{row['Policy Type']} policy {row['Policy Number']} premium of {row['Premium Amount']} is due on {row['Due Date']}.")
        else:
            st.markdown('<div class="content-box">No policies due in the next 30 days.</div>', unsafe_allow_html=True)
        mobile = st.session_state.get("usermobile")
        if mobile and "insurancedata" in st.session_state:
            save_userdata(mobile, "insurance", st.session_state.insurancedata)

def financialgoals():
    st.markdown('<div class="header-box">Financial Goals Planner</div>', unsafe_allow_html=True)
    st.write("Define and track your financial goals below.")
    if "financialgoals" not in st.session_state:
        st.session_state.financialgoals = []
    with st.form("Add New Goal"):
        goaltype = st.text_input("Goal Type (e.g., Retirement, Education, Car, House)")
        goalamount = st.number_input("Goal Amount (₹)", min_value=0, step=1000, format="%i")
        currentamount = st.number_input("Current Amount Saved (₹)", min_value=0, step=1000, format="%i")
        yearstogoal = st.number_input("Years to Goal", min_value=1, step=1, format="%i")
        submitgoal = st.form_submit_button("Add Goal")
    if submitgoal and goaltype and goalamount > 0:
        st.session_state.financialgoals.append({
            "Goal Type": goaltype,
            "Goal Amount": goalamount,
            "Current Amount": currentamount,
            "Years": yearstogoal
        })
        st.success(f"Added goal: {goaltype}")
    if st.session_state.financialgoals:
        df = pd.DataFrame(st.session_state.financialgoals)
        df["Remaining Amount"] = df["Goal Amount"] - df["Current Amount"]
        df["Progress"] = (df["Current Amount"] / df["Goal Amount"] * 100).clip(0, 100).round(1)
        st.markdown('<div class="content-box"><h4>Your Goals</h4></div>', unsafe_allow_html=True)
        st.dataframe(df)
        st.markdown('<div class="content-box"><h4>Goal Progress</h4></div>', unsafe_allow_html=True)
        fig, ax = plt.subplots()
        ax.bar(df["Goal Type"], df["Progress"], color="#FF6F00", edgecolor="#757575")
        ax.set_ylabel("Progress towards goal")
        ax.set_ylim(0, 100)
        ax.set_title("Progress on Financial Goals", color="#757575")
        for idx, v in enumerate(df["Progress"]):
            ax.text(idx, v + 2, f"{v}%", ha="center", color="#FF6F00")
        st.pyplot(fig)
        # Investment suggestion
        st.markdown('<div class="content-box"><h4>Investment Suggestion</h4></div>', unsafe_allow_html=True)
        st.write("Assuming an annual average return of 10% in mutual funds, here is an estimate of yearly investment needed for each goal:")
        roi = 0.10
        suggestion = []
        for i, row in df.iterrows():
            fv = row["Goal Amount"] - row["Current Amount"]
            n = row["Years"]
            if fv > 0 and n > 0:
                p = fv * roi / ((1 + roi) ** n - 1)
                suggestion.append({"Goal": row["Goal Type"], "Invest per Year": f"{p:,.0f}"})
        st.table(pd.DataFrame(suggestion))
    else:
        st.markdown('<div class="content-box">No financial goals yet. Use the form above to add goals.</div>', unsafe_allow_html=True)
    mobile = st.session_state.get("usermobile")
    if mobile and "financialgoals" in st.session_state:
        save_userdata(mobile, "financialgoals", st.session_state.financialgoals)

# -------------------- Main App Controller ------------------------

def main():
    st.markdown("""
        <style>
        .header-box {
            background: linear-gradient(90deg, #FF6F00 70%, #F3F3F3 100%);
            color: #fff; border-radius: 12px;
            box-shadow: 0 2px 8px rgba(120,120,120,0.08);
            padding: 20px 32px 16px 32px; margin-bottom: 28px;
            font-size: 34px; font-weight: 700; letter-spacing: .03em;
            font-family: Segoe UI, Tahoma, Geneva, Verdana, sans-serif;
        }
        .content-box {
            background-color: #F3F3F3;
            border-radius: 8px; padding: 18px 28px; margin-bottom: 24px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.sidebar.title("Menu")
    menu = st.sidebar.radio("Choose Action", ["Login", "Register"], key="action_radio")
    if menu == "Register":
        register_page()
        return

    loggedin = loginsidebar()
    if loggedin:
        logoutsidebar()
        option = st.sidebar.selectbox(
            "Choose an option",
            ["Welcome Page", "Portfolio Tracker", "Insurance Policies", "Financial Goals"]
        )
        if option == "Welcome Page":
            homepagecontent()
        elif option == "Portfolio Tracker":
            portfoliotracker()
        elif option == "Insurance Policies":
            insurancepolicies()
        elif option == "Financial Goals":
            financialgoals()
        else:
            homepagecontent()
    else:
        st.write("Login using the sidebar to access your personalized dashboard.")

if __name__ == "__main__":
    main()
