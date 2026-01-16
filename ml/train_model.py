import pandas as pd
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
from sklearn.metrics import r2_score
import joblib


def train_model():
    # 1. Connect to SQL
    engine = create_engine("mysql+pymysql://root@localhost/big_market_sales")

    # 2. Load data
    df = pd.read_sql("SELECT * FROM sales_data", engine)

    # 3. Data cleaning
    df["Item_Weight"].fillna(df["Item_Weight"].mean(), inplace=True)
    df.drop(columns=["id"], inplace=True)

    df["Item_Fat_Content"] = df["Item_Fat_Content"].replace({
        "low fat": "Low Fat",
        "LF": "Low Fat",
        "reg": "Regular"
    })

    # 4. Encoding
    df = pd.get_dummies(df, drop_first=True)

    # 5. Split
    X = df.drop("Item_Outlet_Sales", axis=1)
    y = df["Item_Outlet_Sales"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # 6. Train model
    model = XGBRegressor(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=6,
        random_state=42
    )

    model.fit(X_train, y_train)

    # 7. Evaluate
    preds = model.predict(X_test)
    r2 = r2_score(y_test, preds)

    # 8. Save model
    joblib.dump(model, "ml/sales_model.pkl")

    print("✅ Model trained successfully")
    print("R2 Score:", r2)


if __name__ == "__main__":
    train_model()
