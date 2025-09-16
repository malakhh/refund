import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="Detroit Axle Refund Calculator", layout="wide")
st.title("🚗 Detroit Axle Refund Calculator")

# --- Kit URL input ---
kit_url = st.text_input("Paste Detroit Axle Kit URL:")

if kit_url:
    try:
        r = requests.get(kit_url, timeout=10)
        r.raise_for_status()
        html = r.text
        soup = BeautifulSoup(html, "html.parser")

        # --- Extract kit price ---
        price_tag = soup.find("span", class_="price-red")
        if price_tag:
            kit_price = float(price_tag.text.strip().replace('$','').replace(',',''))
            st.success(f"Kit price automatically detected: ${kit_price:.2f}")
        else:
            st.warning("Could not detect kit price automatically. Enter manually:")
            kit_price = st.number_input("Kit Price ($):", min_value=0.0, step=0.01)

        # --- Paste Kit Components ---
        st.info("Copy the Kit Components table from the page (Quantity | Name | Part Number) and paste below")
        comp_text = st.text_area("Paste Component Info here", height=200)
        rows = []
        if comp_text:
            for line in comp_text.strip().split("\n"):
                parts = [p.strip() for p in line.split("|")]
                if len(parts) == 3:
                    qty = int(parts[0])
                    name = parts[1]
                    part_number = parts[2]
                    rows.append([qty, name, part_number])

        if rows:
            df = pd.DataFrame(rows, columns=["Quantity","Component","Part Number"])
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
