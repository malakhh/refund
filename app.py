import streamlit as st
import pandas as pd
from playwright.sync_api import sync_playwright

st.set_page_config(page_title="Detroit Axle Refund Calculator", layout="wide")
st.title("🚗 Detroit Axle Refund Calculator")

# --- Dark/Light mode ---
theme = st.sidebar.radio("Theme:", ["Light", "Dark"])
if theme == "Dark":
    st.markdown("""
        <style>
        .stApp {background-color: #0e1117; color: #f0f0f0;}
        .stTextInput>div>div>input {background-color: #1f1f1f; color: #f0f0f0;}
        .stCheckbox>div>label {color: #f0f0f0;}
        .stNumberInput>div>div>input {background-color: #1f1f1f; color: #f0f0f0;}
        </style>
        """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
        .stApp {background-color: #ffffff; color: #000000;}
        </style>
        """, unsafe_allow_html=True)

# --- Kit URL input ---
kit_url = st.text_input("Paste Detroit Axle Kit URL:")

if kit_url:
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(kit_url, timeout=15000)
            
            # Wait for kit price to appear
            page.wait_for_selector("span.price-red", timeout=10000)
            price_text = page.query_selector("span.price-red").inner_text()
            kit_price = float(price_text.replace('$','').replace(',',''))
            st.success(f"Kit price detected: ${kit_price:.2f}")

            # Click Kit Components toggle
            toggle_text = "Kit Component Parts Toggle"
            page.wait_for_selector(f"text={toggle_text}", timeout=10000)
            page.click(f"text={toggle_text}")

            # Wait for table to load
            page.wait_for_selector("table", timeout=10000)
            table = page.query_selector("table")
            
            # Extract rows
            rows = []
            for tr in table.query_selector_all("tr")[1:]:  # skip header
                tds = tr.query_selector_all("td")
                if len(tds) >= 3:
                    qty = int(tds[0].inner_text().strip())
                    name = tds[1].inner_text().strip()
                    part_number = tds[2].inner_text().strip()
                    rows.append([qty, name, part_number])
            
            browser.close()

        if not rows:
            st.warning("Could not detect kit components automatically. Try manually copy-pasting the table.")
        else:
            # --- Create DataFrame ---
            df = pd.DataFrame(rows, columns=["Quantity","Component","Part Number"])
            df["Component Price ($)"] = 0.0
            df["Refund?"] = False

            st.subheader("Components Table (Editable Prices & Refund Selection)")

            # Editable table with inline price input and refund checkbox
            for idx in df.index:
                cols = st.columns([1.5,3,2,2,1])
                df.at[idx,"Quantity"] = cols[0].number_input("Qty", min_value=1, value=int(df.at[idx,"Quantity"]), key=f"qty_{idx}")
                df.at[idx,"Component"] = cols[1].text_input("Name", value=df.at[idx,"Component"], key=f"name_{idx}")
                df.at[idx,"Part Number"] = cols[2].text_input("Part #", value=df.at[idx,"Part Number"], key=f"pn_{idx}")
                df.at[idx,"Component Price ($)"] = cols[3].number_input("Price ($)", min_value=0.0, step=0.01, key=f"price_{idx}")
                df.at[idx,"Refund?"] = cols[4].checkbox("Refund", key=f"refund_{idx}")

            # Kit-adjusted price calculation
            total_component_price = df["Component Price ($)"].sum()
            if total_component_price > 0:
                df["Kit-Adjusted Price ($)"] = df["Component Price ($)"] / total_component_price * kit_price
            else:
                df["Kit-Adjusted Price ($)"] = 0.0

            # Total refund
            refund_total = df.loc[df["Refund?"], "Kit-Adjusted Price ($)"].sum()
            st.markdown(f"<h2 style='color:green'>💰 Total Refund: ${refund_total:.2f}</h2>", unsafe_allow_html=True)

            st.subheader("Components Overview")
            st.dataframe(df)

    except Exception as e:
        st.error(f"Error fetching kit data: {e}")
