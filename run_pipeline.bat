@echo off
cd /d "C:\Users\kaila\Desktop\big market sales"

python etl\load_csv_to_sql.py
python ml\train_model.py
python ml\predict_and_store.py
