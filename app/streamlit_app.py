import streamlit as st
import pandas as pd
import numpy as np
import joblib
from sqlalchemy import create_engine
import matplotlib.pyplot as plt

# ----------------------------
# Page Config
# ----------------------------
st.set_page_config(
    page_title="Big Market Sales Predictor",
    page_icon="🛒",
    layout="wide"
)

# ----------------------------
# Load Model + SQL
# ----------------------------
engine = create_engine("mysql+pymysql://root@localhost/big_market_sales")
model = joblib.load("ml/sales_model.pkl")

# ----------------------------
# Title
# ----------------------------
st.title("🛒 Big Market Sales Prediction Dashboard")
st.caption("SQL → ML Model (.pkl) → Predictions + Insights | Streamlit App")

# ----------------------------
# Load SQL Data (for dropdowns + sampling)
# ----------------------------
df_sql = pd.read_sql("SELECT * FROM sales_data", engine)

# ----------------------------
# Sidebar Controls
# ----------------------------
st.sidebar.header("⚙️ Controls")

mode = st.sidebar.radio(
    "Choose Input Mode",
    ["Manual Input", "Pick Random Sample from SQL"],
    index=1
)

save_to_sql = st.sidebar.checkbox("✅ Save Prediction to SQL", value=True)

st.sidebar.markdown("---")
st.sidebar.info("Tip: Random sample mode is easiest for demo & resume screenshots ✅")

# ----------------------------
# Pick sample row
# ----------------------------
sample_row = None
if mode == "Pick Random Sample from SQL":
    if st.sidebar.button("🎲 Pick Random Row"):
        sample_row = df_sql.sample(1, random_state=None).iloc[0]

# If no sample picked, use first row as default
if sample_row is None:
    sample_row = df_sql.iloc[0]

# ----------------------------
# Main Input Section (only important features)
# ----------------------------
st.subheader("📌 Enter Important Details (Minimal Inputs)")

col1, col2, col3 = st.columns(3)

with col1:
    Item_MRP = st.number_input(
        "Item_MRP (Price)",
        min_value=0.0,
        value=float(sample_row["Item_MRP"]),
        step=1.0
    )
    Item_Visibility = st.number_input(
        "Item_Visibility",
        min_value=0.0,
        value=float(sample_row["Item_Visibility"]),
        step=0.001
    )

with col2:
    Item_Fat_Content = st.selectbox(
        "Item_Fat_Content",
        ["Low Fat", "Regular"],
        index=0 if str(sample_row["Item_Fat_Content"]) == "Low Fat" else 1
    )
    Outlet_Location_Type = st.selectbox(
        "Outlet_Location_Type",
        ["Tier 1", "Tier 2", "Tier 3"],
        index=["Tier 1", "Tier 2", "Tier 3"].index(str(sample_row["Outlet_Location_Type"]))
        if str(sample_row["Outlet_Location_Type"]) in ["Tier 1", "Tier 2", "Tier 3"] else 0
    )

with col3:
    Outlet_Type = st.selectbox(
        "Outlet_Type",
        ["Supermarket Type1", "Supermarket Type2", "Supermarket Type3", "Grocery Store"],
        index=["Supermarket Type1", "Supermarket Type2", "Supermarket Type3", "Grocery Store"].index(str(sample_row["Outlet_Type"]))
        if str(sample_row["Outlet_Type"]) in ["Supermarket Type1", "Supermarket Type2", "Supermarket Type3", "Grocery Store"] else 0
    )
    Outlet_Establishment_Year = st.slider(
        "Outlet_Establishment_Year",
        1985, 2010,
        int(sample_row["Outlet_Establishment_Year"])
    )

# Extra (hidden but required for model)
Item_Identifier = str(sample_row["Item_Identifier"])
Outlet_Identifier = str(sample_row["Outlet_Identifier"])
Item_Type = str(sample_row["Item_Type"])
Item_Weight = float(sample_row["Item_Weight"]) if not pd.isna(sample_row["Item_Weight"]) else df_sql["Item_Weight"].mean()
Outlet_Size = str(sample_row["Outlet_Size"]) if not pd.isna(sample_row["Outlet_Size"]) else "Medium"

# ----------------------------
# Make input dataframe (must match training columns)
# ----------------------------
input_data = pd.DataFrame([{
    "Item_Identifier": Item_Identifier,
    "Item_Weight": Item_Weight,
    "Item_Fat_Content": Item_Fat_Content,
    "Item_Visibility": Item_Visibility,
    "Item_Type": Item_Type,
    "Item_MRP": Item_MRP,
    "Outlet_Identifier": Outlet_Identifier,
    "Outlet_Establishment_Year": Outlet_Establishment_Year,
    "Outlet_Size": Outlet_Size,
    "Outlet_Location_Type": Outlet_Location_Type,
    "Outlet_Type": Outlet_Type
}])

# ----------------------------
# Preprocessing (same style as training)
# ----------------------------
input_data["Item_Weight"].fillna(df_sql["Item_Weight"].mean(), inplace=True)

input_data["Item_Fat_Content"] = input_data["Item_Fat_Content"].replace({
    "low fat": "Low Fat",
    "LF": "Low Fat",
    "reg": "Regular"
})

input_encoded = pd.get_dummies(input_data, drop_first=True)

# Training reference columns (use SQL data sample to create same columns)
df_ref = df_sql.drop(columns=["id"])
df_ref["Item_Weight"].fillna(df_ref["Item_Weight"].mean(), inplace=True)
df_ref["Item_Fat_Content"] = df_ref["Item_Fat_Content"].replace({
    "low fat": "Low Fat",
    "LF": "Low Fat",
    "reg": "Regular"
})

df_ref_X = df_ref.drop(columns=["Item_Outlet_Sales"])
df_ref_encoded = pd.get_dummies(df_ref_X, drop_first=True)

# Add missing columns
for col in df_ref_encoded.columns:
    if col not in input_encoded.columns:
        input_encoded[col] = 0

# Keep same order
input_encoded = input_encoded[df_ref_encoded.columns]

# ----------------------------
# Predict
# ----------------------------
st.markdown("---")
predict_btn = st.button("🔮 Predict Outlet Sales", use_container_width=True)

if predict_btn:
    prediction = float(model.predict(input_encoded)[0])

    st.success(f"✅ Predicted Item Outlet Sales: **{prediction:,.2f}**")

    # Actual if available (from sample row)
    actual_sales = float(sample_row["Item_Outlet_Sales"]) if "Item_Outlet_Sales" in df_sql.columns else None

    # ----------------------------
    # Comparison section
    # ----------------------------
    colA, colB = st.columns(2)

    with colA:
        st.subheader("📊 Actual vs Predicted")
        if actual_sales is not None:
            chart_df = pd.DataFrame({
                "Type": ["Actual", "Predicted"],
                "Sales": [actual_sales, prediction]
            })
            st.bar_chart(chart_df.set_index("Type"))
        else:
            st.info("Actual sales not available.")

    with colB:
        st.subheader("📌 Quick Summary")
        st.write(f"**Item Identifier:** {Item_Identifier}")
        st.write(f"**Outlet Identifier:** {Outlet_Identifier}")
        st.write(f"**Outlet Type:** {Outlet_Type}")
        st.write(f"**Location Type:** {Outlet_Location_Type}")
        st.write(f"**MRP:** {Item_MRP}")

        if actual_sales is not None:
            diff = prediction - actual_sales
            st.write(f"**Actual Sales:** {actual_sales:,.2f}")
            st.write(f"**Difference (Pred - Actual):** {diff:,.2f}")

    # ----------------------------
    # Save to SQL (optional)
    # ----------------------------
    if save_to_sql:
        save_df = pd.DataFrame([{
            "Item_Identifier": Item_Identifier,
            "Outlet_Identifier": Outlet_Identifier,
            "predicted_sales": prediction
        }])

        save_df.to_sql("sales_predictions", engine, if_exists="append", index=False)
        st.toast("✅ Prediction saved to SQL!", icon="✅")

    # ----------------------------
    # Show last 10 saved predictions
    # ----------------------------
    st.markdown("---")
    st.subheader("🕒 Latest Predictions History (SQL)")

    try:
        history = pd.read_sql("SELECT * FROM sales_predictions ORDER BY id DESC LIMIT 10", engine)
        st.dataframe(history, use_container_width=True)
    except Exception:
        st.warning("sales_predictions table not found or no data yet.")
