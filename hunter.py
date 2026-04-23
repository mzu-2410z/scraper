import requests
from bs4 import BeautifulSoup
import pandas as pd
import io
import os

# ==========================================
# CONFIGURATION
# ==========================================
TARGET_PAGE = "https://tsbde.texas.gov/resources/licensee-lists/"
EXCEL_FILENAME = "schedsy_leads_texas.xlsx"

# Standard headers to bypass basic server rejections
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
}


def locate_and_download_csv():
    """Scrapes the Texas registry page to find the dynamic Dentist CSV link and downloads it."""
    print(f"[*] Connecting to Texas State Board of Dental Examiners: {TARGET_PAGE}")
    response = requests.get(TARGET_PAGE, headers=HEADERS, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')

    # Locate the anchor tag containing the Dentist CSV link
    # The TSBDE site typically labels the link text with "Dentist"
    csv_link = None
    for a_tag in soup.find_all('a', href=True):
        if 'dentist' in a_tag.text.lower() and '.csv' in a_tag['href'].lower():
            csv_link = a_tag['href']
            break

    if not csv_link:
        raise ValueError("Could not locate the Dentist CSV link on the target page.")

    print(f"[*] Payload located: {csv_link}")
    print("[*] Downloading raw state database...")

    csv_response = requests.get(csv_link, headers=HEADERS, timeout=30)
    csv_response.raise_for_status()

    return io.StringIO(csv_response.text)


def sanitize_and_export(raw_csv_data):
    """Processes the raw payload, filters for decision-makers, and outputs to Excel."""
    print("[*] Ingesting payload into Pandas DataFrame...")

    # Read the raw CSV. Note: We use low_memory=False to prevent dtype warnings on messy government data
    df = pd.read_csv(raw_csv_data, low_memory=False)

    # Normalize column names to lowercase to avoid strict casing errors
    df.columns = df.columns.str.strip().str.lower()

    initial_count = len(df)
    print(f"[*] Raw records ingested: {initial_count}")

    # ==========================================
    # THE SCHEDSY QUALITY GATES
    # ==========================================
    # 1. Ensure we have the required columns (Adjust these if the state changes headers)
    # Typical TSBDE columns: 'first name', 'last name', 'license status', 'designation', 'email'

    # Find the email column (it might be labeled 'email address' or just 'email')
    email_col = [col for col in df.columns if 'email' in col]
    status_col = [col for col in df.columns if 'status' in col]

    if not email_col or not status_col:
        print(f"[!] Warning: Column schema changed. Current columns: {df.columns.tolist()}")
        print("[!] Defaulting to raw dump. Manual review required.")
        df.to_excel(EXCEL_FILENAME, index=False)
        return

    email_col = email_col[0]
    status_col = status_col[0]

    # Filter 1: Active Licenses Only
    df_clean = df[df[status_col].astype(str).str.contains("Active", case=False, na=False)]

    # Filter 2: Must have a valid email address (contains @)
    df_clean = df_clean[df_clean[email_col].astype(str).str.contains("@", na=False)]

    # Filter 3: Remove junk/receptionist emails
    junk_prefixes = ['info@', 'contact@', 'office@', 'admin@', 'hello@']
    pattern = '|'.join(junk_prefixes)
    df_clean = df_clean[~df_clean[email_col].astype(str).str.contains(pattern, case=False, na=False)]

    # Select only the columns Schedsy needs for the Groq AI pitch
    # Grabbing First Name, Last Name, Email, and City (if available)
    cols_to_keep = [col for col in df.columns if any(x in col for x in ['name', 'email', 'city', 'state'])]
    df_final = df_clean[cols_to_keep]

    final_count = len(df_final)
    print(f"[+] Sanitization complete. Yielded {final_count} verified decision-makers.")

    # Export to Schedsy local state layer
    print(f"[*] Writing to {EXCEL_FILENAME}...")
    df_final.to_excel(EXCEL_FILENAME, index=False)
    print("[*] Engine spun down successfully.")


if __name__ == "__main__":
    print("[*] System: Online. Booting Texas Extraction Engine...")
    try:
        raw_data = locate_and_download_csv()
        sanitize_and_export(raw_data)
    except Exception as e:
        print(f"[X] FATAL: {e}")