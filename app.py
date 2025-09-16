import streamlit as st
import pandas as pd

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

# --- Kit Info ---
kit_link = st.text_input("Kit Link (for reference):")
kit_price = st.number_input("Kit Price ($):", min_value=0.0, step=0.01)

# --- Component Input ---
st.subheader("Paste Component Info (Name | Part Number | Quantity)")

comp_text = st.text_area(
    "Example format:\nFront Rotor | 12345 | 2\nRear Rotor | 67890 | 2",
    height=150
)

if comp_text:
    # Parse pasted text into DataFrame
    rows = [line.strip().split("|") for line in comp_text.strip().split("\n") if line.strip()]
    df = pd.DataFrame(rows, columns=["Component", "Part Number", "Quantity"])
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors='coerce').fillna(1)
    df["Component Price ($)"] = 0.0  # placeholder for user input

    st.subheader("Enter Component Prices")
    for idx in df.index:
        df.at[idx, "Component Price ($)"] = st.number_input(
            f"{df.at[idx,'Component']} (${df.at[idx,'Part Number']})",
            min_value=0.0,
            step=0.01,
            key=f"price_{idx}"
        )

    # Calculate kit-adjusted prices
    total_individual = sum(df["Component Price ($)"]) if sum(df["Component Price ($)"]) > 0 else 1
    df["Kit-Adjusted Price ($)"] = df["Component Price ($)"] / total_individual * kit_price

    st.subheader("Select Components for Refund")
    refund_total = 0
    refund_flags = []
    for idx in df.index:
        flag = st.checkbox(
            f"{df.at[idx,'Component']} - Kit Price: ${df.at[idx,'Kit-Adjusted Price ($)']:.2f}",
            key=f"refund_{idx}"
        )
        refund_flags.append(flag)
        if flag:
            refund_total += df.at[idx, "Kit-Adjusted Price ($)"]

    st.markdown(f"<h2 style='color:green'>💰 Total Refund: ${refund_total:.2f}</h2>", unsafe_allow_html=True)
    st.subheader("Components Table")
    st.dataframe(df)
