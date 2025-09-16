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

        # --- Extract kit price (second $) ---
        dollar_matches = re.findall(r"\$(\d+[\.,]?\d*)", html)
        if len(dollar_matches) >= 2:
            kit_price = float(dollar_matches[1].replace(',', ''))
            st.success(f"Kit price automatically detected: ${kit_price:.2f}")
        else:
            st.warning("Could not detect kit price automatically. Please enter manually.")
            kit_price = st.number_input("Enter Kit Price ($):", min_value=0.0, step=0.01)

        # --- Extract kit components ---
        soup = BeautifulSoup(html, "html.parser")
        # Attempt to find static table, fallback to manual
        table = soup.find("table")
        if table:
            rows = []
            for tr in table.find_all("tr"):
                cols = [td.get_text(strip=True) for td in tr.find_all("td")]
                if len(cols) >= 2:
                    name = cols[0]
                    part_number = cols[1]
                    quantity = int(cols[2]) if len(cols) >= 3 and cols[2].isdigit() else 1
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
            # Add Component Price column for manual input
            components_df["Component Price ($)"] = 0.0

            st.subheader("Enter Component Prices")
            for idx in components_df.index:
                components_df.at[idx, "Component Price ($)"] = st.number_input(
                    f"{components_df.at[idx,'Component']} (${components_df.at[idx,'Part Number']})",
                    min_value=0.0,
                    step=0.01,
                    key=f"price_{idx}"
                )

            # Calculate kit-adjusted prices
            prices = components_df["Component Price ($)"].tolist()
            total_individual = sum(prices) if sum(prices) > 0 else 1
            components_df["Kit-Adjusted Price ($)"] = [p / total_individual * kit_price for p in prices]

            st.subheader("Select Components for Refund")
            refund_total = 0
            for idx in components_df.index:
                flag = st.checkbox(
                    f"{components_df.at[idx,'Component']} - Kit Price: ${components_df.at[idx,'Kit-Adjusted Price ($)']:.2f}",
                    key=f"refund_{idx}"
                )
                if flag:
                    refund_total += components_df.at[idx, "Kit-Adjusted Price ($)"]

            st.markdown(f"<h2 style='color:green'>💰 Total Refund: ${refund_total:.2f}</h2>", unsafe_allow_html=True)
            st.subheader("Components Table")
            st.dataframe(components_df)

    except Exception as e:
        st.error(f"Error fetching kit data: {e}")
        kit_price = st.number_input("Enter Kit Price ($):", min_value=0.0, step=0.01)
