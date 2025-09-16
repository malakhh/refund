import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

st.set_page_config(page_title="Detroit Axle Refund Calculator", layout="wide")
st.title("🚗 Detroit Axle Refund Calculator (Hosted)")

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

# --- Kit URL Input ---
kit_url = st.text_input("Paste Detroit Axle Kit URL:")

kit_price = None
components_df = None

if kit_url:
    try:
        r = requests.get(kit_url, timeout=10)
        r.raise_for_status()
        html = r.text
        soup = BeautifulSoup(html, "html.parser")

        # --- Extract kit price (red discounted price) ---
        price_tag = soup.find("span", class_="price-red")  # most pages have price in this class
        if price_tag:
            kit_price = float(price_tag.text.strip().replace('$','').replace(',',''))
            st.success(f"Kit price automatically detected: ${kit_price:.2f}")
        else:
            st.warning("Could not detect kit price automatically. Please enter manually.")
            kit_price = st.number_input("Enter Kit Price ($):", min_value=0.0, step=0.01)

        # --- Extract kit components ---
        components_section = soup.find("div", class_="kit-components")  # adjust based on actual HTML
        rows = []
        if components_section:
            for li in components_section.find_all("li"):
                text = li.get_text(strip=True)
                # Example format: "Front Rotor | FR1234 | Qty: 2"
                parts = text.split("|")
                if len(parts) >= 2:
                    name = parts[0].strip()
                    part_number = parts[1].strip()
                    # Quantity parsing
                    quantity = 1
                    if len(parts) >= 3:
                        qty_match = re.search(r'\d+', parts[2])
                        if qty_match:
                            quantity = int(qty_match.group())
                    rows.append([name, part_number, quantity])
        if rows:
            components_df = pd.DataFrame(rows, columns=["Component", "Part Number", "Quantity"])
            st.success("Kit components automatically detected.")

        if components_df is None:
            st.info("Could not detect components automatically. Please paste manually.")
            comp_text = st.text_area(
                "Paste Component Info (Name | Part Number | Quantity):",
                height=150
            )
            if comp_text:
                rows = [line.strip().split("|") for line in comp_text.strip().split("\n") if line.strip()]
                components_df = pd.DataFrame(rows, columns=["Component", "Part Number", "Quantity"])
                components_df["Quantity"] = pd.to_numeric(components_df["Quantity"], errors='coerce').fillna(1)

        if components_df is not None:
            # Add columns for manual price and refund checkbox
            components_df["Component Price ($)"] = 0.0
            components_df["Refund?"] = False

            st.subheader("Components Table with Inline Refund Selection")
            for idx in components_df.index:
                cols = st.columns([3, 1, 2, 2, 1])  # name, quantity, part#, price input, refund checkbox
                components_df.at[idx, "Component"] = cols[0].text_input(
                    "Component Name", value=components_df.at[idx, "Component"], key=f"name_{idx}"
                )
                components_df.at[idx, "Quantity"] = cols[1].number_input(
                    "Quantity", min_value=1, value=int(components_df.at[idx, "Quantity"]), key=f"qty_{idx}"
                )
                components_df.at[idx, "Part Number"] = cols[2].text_input(
                    "Part Number", value=components_df.at[idx, "Part Number"], key=f"pn_{idx}"
                )
                components_df.at[idx, "Component Price ($)"] = cols[3].number_input(
                    "Price ($)", min_value=0.0, step=0.01, key=f"price_{idx}"
                )
                components_df.at[idx, "Refund?"] = cols[4].checkbox(
                    "Refund", key=f"refund_{idx}"
                )

            # Calculate kit-adjusted prices
            total_individual = sum(components_df["Component Price ($)"]) if sum(components_df["Component Price ($)"]) > 0 else 1
            components_df["Kit-Adjusted Price ($)"] = [p / total_individual * kit_price for p in components_df["Component Price ($)"]]

            # Calculate total refund
            refund_total = components_df.loc[components_df["Refund?"], "Kit-Adjusted Price ($)"].sum()
            st.markdown(f"<h2 style='color:green'>💰 Total Refund: ${refund_total:.2f}</h2>", unsafe_allow_html=True)

            st.subheader("Components Table Overview")
            st.dataframe(components_df)

    except Exception as e:
        st.error(f"Error fetching kit data: {e}")
        kit_price = st.number_input("Enter Kit Price ($):", min_value=0.0, step=0.01)
