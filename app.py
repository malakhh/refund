import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="Detroit Axle Refund Calculator", layout="wide")
st.title("🚗 Detroit Axle Refund Calculator")

# --- Theme ---
theme = st.sidebar.radio("Theme:", ["Light", "Dark"])
if theme == "Dark":
    st.markdown("""
        <style>
        .stApp {background-color: #0e1117; color: #f0f0f0;}
        .stTextInput>div>div>input {background-color: #1f1f1f; color: #f0f0f0;}
        .stCheckbox>div>label {color: #f0f0f0;}
        </style>
        """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
        .stApp {background-color: #ffffff; color: #000000;}
        .stTextInput>div>div>input {background-color: #f9f9f9; color: #000000;}
        .stCheckbox>div>label {color: #000000;}
        </style>
        """, unsafe_allow_html=True)

# --- Kit URL input ---
kit_url = st.text_input("Paste Detroit Axle Kit URL:")

if kit_url:
    try:
        r = requests.get(kit_url, timeout=10)
        r.raise_for_status()
        html = r.text
        soup = BeautifulSoup(html, "html.parser")

        # --- Extract kit price from red discounted price ---
        price_tag = soup.find("span", class_="price-red")
        if price_tag:
            kit_price = float(price_tag.text.strip().replace('$','').replace(',',''))
            st.success(f"Kit price automatically detected: ${kit_price:.2f}")
        else:
            st.warning("Could not detect kit price automatically. Enter manually:")
            kit_price = st.number_input("Kit Price ($):", min_value=0.0, step=0.01)

        # --- Extract kit components table ---
        # Find the first <table> after "Kit Components" toggle
        components_table = None
        for h3 in soup.find_all(["h3","h2","h4"]):
            if "Kit Components" in h3.get_text():
                # Look for next table
                table = h3.find_next("table")
                if table:
                    components_table = table
                    break

        rows = []
        if components_table:
            for tr in components_table.find_all("tr")[1:]:  # skip header
                cols = tr.find_all("td")
                if len(cols) >= 3:
                    qty = int(cols[0].text.strip())
                    name = cols[1].text.strip()
                    part_number = cols[2].text.strip()
                    rows.append([qty, name, part_number])
            st.success("Kit components automatically detected.")
        else:
            st.warning("Could not detect components automatically. Paste manually:")
            comp_text = st.text_area(
                "Paste Component Info (Qty | Name | Part Number) separated by |, one per line",
                height=150
            )
            if comp_text:
                rows = [line.strip().split("|") for line in comp_text.strip().split("\n") if line.strip()]

        if rows:
            df = pd.DataFrame(rows, columns=["Quantity","Component","Part Number"])
            df["Quantity"] = pd.to_numeric(df["Quantity"], errors='coerce').fillna(1)
            df["Component Price ($)"] = 0.0
            df["Refund?"] = False

            st.subheader("Components Table with Inline Refund Selection")
            for idx in df.index:
                cols = st.columns([1.5,3,2,2,1])  # qty, name, part#, price, refund
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

            st.subheader("Components Table Overview")
            st.dataframe(df)

    except Exception as e:
        st.error(f"Error fetching kit data: {e}")
