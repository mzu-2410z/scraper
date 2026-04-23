import requests
from bs4 import BeautifulSoup
import pandas as pd
import io

TARGET_PAGE = "https://tsbde.texas.gov/resources/licensee-lists/"
EXCEL_FILENAME = "schedsy_leads_texas.xlsx"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def extract():
    print("[*] Connecting to TSBDE...")
    res = requests.get(TARGET_PAGE, headers=HEADERS)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    csv_link = next(a['href'] for a in soup.find_all('a', href=True) if 'dentist' in a.text.lower() and '.csv' in a['href'].lower())
    print(f"[*] Downloading: {csv_link}")
    
    csv_res = requests.get(csv_link, headers=HEADERS)
    df = pd.read_csv(io.StringIO(csv_res.text), low_memory=False)
    
    # DEBUG: Print the actual columns so we can see what the state named them
    print(f"[*] DETECTED COLUMNS: {df.columns.tolist()}")
    print(f"[*] FIRST ROW SAMPLE: \n{df.iloc[0]}")
    
    # RELAXED FILTERS: Let's grab everything first to ensure the pipe works
    # We will tighten these once we see the column names in the log
    print(f"[*] Total raw records: {len(df)}")
    
    # Export the RAW data to Excel just to make sure we get SOMETHING
    df.to_excel(EXCEL_FILENAME, index=False)
    print("[*] Raw export complete.")

if __name__ == "__main__":
    extract()
