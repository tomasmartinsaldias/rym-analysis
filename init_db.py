from app import create_app, db
from app.utils import process_csv_to_db
import os

app = create_app()

with app.app_context():
    db.create_all()
    print("Database tables created successfully.")
    
    csv_path = 'rym_clean1.csv'
    if os.path.exists(csv_path):
        print(f"Loading data from {csv_path}...")
        process_csv_to_db(csv_path)
        print("Data loaded successfully.")
    else:
        print(f"Warning: {csv_path} not found.")
