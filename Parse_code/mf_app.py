import streamlit as st
import pandas as pd
import json
from mftool import Mftool

# --- CONFIGURATION ---
st.set_page_config(page_title="Live Portfolio Dashboard", layout="wide")

# --- HELPER FUNCTIONS ---
@st.cache_resource
def get_mftool():
    """Initialize the MF Tool library (Cached to prevent reloading)"""
    return Mftool()

def fetch_latest_nav(amfi_code, obj_mftool):
    """Fetch latest NAV for a given AMFI code"""
    if not amfi_code:
        return None, None
    
    try:
        # Fetch quote using mftool
        quote = obj_mftool.get_scheme_quote(str(amfi_code))
        return float(quote['nav']), quote['last_updated']
    except Exception:
        return None, None

# --- MAIN UI ---
st.title("📈 Live Mutual Fund Portfolio Tracker")
st.markdown("Upload your **`my_portfolio_db.json`** file to see values updated with **Live NAVs**.")

# 1. SIDEBAR: File Upload
with st.sidebar:
    st.header("📁 Load Data")
    uploaded_file = st.file_uploader("Upload JSON Database", type=["json"])
    
    refresh = st.button("🔄 Refresh NAVs")

# 2. MAIN LOGIC
if uploaded_file:
    # Load JSON data
    data = json.load(uploaded_file)
    mf = get_mftool()
    
    investor_name = data.get('investor_info', {}).get('name', 'Investor')
    st.subheader(f"Welcome, {investor_name}")

    # Container for the rows
    portfolio_data = []
    
    # Progress bar for fetching NAVs (can be slow for many funds)
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Flatten the JSON structure
    all_schemes = []
    for folio in data.get('folios', []):
        for scheme in folio.get('schemes', []):
            all_schemes.append({
                "folio": folio['folio'],
                "scheme_data": scheme
            })

    total_schemes = len(all_schemes)

    # 3. ITERATE AND UPDATE
    for i, item in enumerate(all_schemes):
        scheme = item['scheme_data']
        folio_num = item['folio']
        
        name = scheme['scheme']
        amfi_code = scheme.get('amfi', None) # casparser usually finds this
        units = float(scheme['valuation']['units'])
        old_val = float(scheme['valuation']['value'])
        
        # Update Status
        status_text.text(f"Fetching NAV for: {name}...")
        progress_bar.progress((i + 1) / total_schemes)

        # FETCH LIVE DATA
        latest_nav, nav_date = fetch_latest_nav(amfi_code, mf)
        
        # Calculate New Value
        if latest_nav:
            current_val = units * latest_nav
            nav_display = latest_nav
            val_display = current_val
            gain_loss = current_val - scheme['valuation'].get('cost', 0)
            nav_status = f"✅ Live ({nav_date})"
        else:
            # Fallback to PDF data if live fetch fails
            current_val = old_val
            nav_display = float(scheme['valuation'].get('nav', 0))
            val_display = old_val
            gain_loss = 0
            nav_status = "⚠️ Old (PDF Data)"

        portfolio_data.append({
            "Scheme Name": name,
            "AMFI Code": amfi_code,
            "Units": units,
            "Latest NAV (₹)": nav_display,
            "Current Value (₹)": val_display,
            "Status": nav_status,
        })

    status_text.empty()
    progress_bar.empty()

    # 4. DISPLAY DASHBOARD
    if portfolio_data:
        df = pd.DataFrame(portfolio_data)
        
        # Top level metrics
        total_value = df["Current Value (₹)"].sum()
        st.metric(label="💰 Total Portfolio Value (Live)", value=f"₹{total_value:,.2f}")
        
        # Formatting for display
        st.dataframe(
            df.style.format({
                "Units": "{:.4f}",
                "Latest NAV (₹)": "{:.4f}",
                "Current Value (₹)": "{:,.2f}",
            }),
            use_container_width=True,
            height=500
        )
    else:
        st.warning("No schemes found in the JSON file.")

else:
    st.info("👈 Please upload your JSON file from the sidebar to begin.")