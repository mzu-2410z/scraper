import requests
from bs4 import BeautifulSoup
import pandas as pd
import io

TARGET_PAGE = "https://tsbde.texas.gov/resources/licensee-lists/"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def discover_schema():
    print("[*] Connecting to TSBDE for Schema Discovery...")
    res = requests.get(TARGET_PAGE, headers=HEADERS)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    try:
        # Find the Dentist CSV
        csv_link = next(a['href'] for a in soup.find_all('a', href=True) if 'dentist' in a.text.lower() and '.csv' in a['href'].lower())
        print(f"[*] Target Link Found: {csv_link}")
        
        # Download only the first 5 rows to save time and memory
        csv_res = requests.get(csv_link, headers=HEADERS)
        df = pd.read_csv(io.StringIO(csv_res.text), nrows=5, low_memory=False)
        
        print("\n" + "="*50)
        print("CRITICAL DATA: COLUMN NAMES FOUND")
        print("="*50)
        # This prints the columns exactly as the server sends them
        for i, col in enumerate(df.columns):
            print(f"Column {i}: '{col}'")
        print("="*50 + "\n")
        
        # Also print one row so we can see the data format (e.g., is email really there?)
        print("[*] Sample Data (First Row):")
        print(df.iloc[0].to_dict())

    except Exception as e:
        print(f"[X] SCHEMA DISCOVERY FAILED: {e}")

if __name__ == "__main__":
    discover_schema()
