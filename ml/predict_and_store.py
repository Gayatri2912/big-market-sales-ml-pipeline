import pandas as pd
from sqlalchemy import create_engine
import joblib

def predict_and_store():
    # 1. DB connection
    engine = create_engine("mysql+pymysql://root@localhost/big_market_sales")

    # 2. Load trained model
    model = joblib.load("ml/sales_model.pkl")

    # 3. Load latest data from SQL
    df = pd.read_sql("SELECT * FROM sales_data", engine)

    # 4. Same preprocessing as training
    df["Item_Weight"].fillna(df["Item_Weight"].mean(), inplace=True)

    df["Item_Fat_Content"] = df["Item_Fat_Content"].replace({
        "low fat": "Low Fat",
        "LF": "Low Fat",
        "reg": "Regular"
    })

    # Keep identifiers for saving later
    output_df = df[["Item_Identifier", "Outlet_Identifier"]].copy()

    # Drop unwanted columns
    df = df.drop(columns=["id", "Item_Outlet_Sales"])

    # One-hot encoding
    df = pd.get_dummies(df, drop_first=True)

    # 5. Predict
    predictions = model.predict(df)

    output_df["predicted_sales"] = predictions

    # 6. Store predictions into SQL
    output_df.to_sql(
        name="sales_predictions",
        con=engine,
        if_exists="replace",
        index=False
    )

    print("✅ Predictions generated and stored in SQL")

if __name__ == "__main__":
    predict_and_store()
