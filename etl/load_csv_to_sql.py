import pandas as pd
from sqlalchemy import create_engine
import os

# MySQL connection
engine = create_engine(
    "mysql+pymysql://root@localhost/big_market_sales"
)
# Absolute path of CSV
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
csv_path = os.path.join(BASE_DIR, "data", "Train.csv")

print("Reading file from:", csv_path)

# Read CSV
df = pd.read_csv(csv_path)

print("CSV rows:", df.shape)

# Load to SQL
df.to_sql(
    name="sales_data",
    con=engine,
    if_exists="append",
    index=False
)

print("✅ CSV data SQL mein load ho gaya")
