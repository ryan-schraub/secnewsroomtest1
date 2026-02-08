import requests
import time

# SEC COMPLIANCE: You MUST use a valid User-Agent
# This identifies you to the SEC to avoid being blocked.
HEADERS = {
    'User-Agent': 'SECTicker (conantbball2@yahoo.com)',
    'Accept-Encoding': 'gzip, deflate',
    'Host': 'data.sec.gov'
}

def run_pilot_test(ticker):
    ticker = ticker.upper()
    print(f"--- Starting Pilot Test for {ticker} ---")

    # 1. Get CIK from Ticker
    # The SEC provides a mapping file for all tickers.
    mapping_url = "https://www.sec.gov/files/company_tickers.json"
    mapping_resp = requests.get(mapping_url, headers={'User-Agent': HEADERS['User-Agent']})
    companies = mapping_resp.json()
    
    cik = None
    for entry in companies.values():
        if entry['ticker'] == ticker:
            cik = str(entry['cik_str']).zfill(10)
            break
    
    if not cik:
        print(f"Error: Could not find CIK for {ticker}")
        return

    print(f"Step 1 Success: CIK found: {cik}")

    # 2. Fetch Metadata (Industry, Location, etc.)
    # We hit the Submissions endpoint for company profile info.
    sub_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    sub_data = requests.get(sub_url, headers=HEADERS).json()
    
    industry = sub_data.get('sicDescription', 'N/A')
    location = f"{sub_data.get('addresses', {}).get('business', {}).get('city')}, {sub_data.get('addresses', {}).get('business', {}).get('stateOrProvince')}"
    
    print(f"Step 2 Success: Industry: {industry} | Location: {location}")

    # 3. Fetch Revenue (The "Easy" Way)
    # We test the most common Revenue tag first.
    revenue_val = "N/A"
    rev_tag = "Revenues" # Can fallback to 'SalesRevenueNet' or others if this fails
    rev_url = f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{rev_tag}.json"
    
    rev_resp = requests.get(rev_url, headers=HEADERS)
    if rev_resp.status_code == 200:
        rev_data = rev_resp.json()
        # Filter for 10-K (Annual Reports) only
        annual_units = [u for u in rev_data['units']['USD'] if u.get('form') == '10-K']
        if annual_units:
            # Sort by date to get the most recent report
            latest = sorted(annual_units, key=lambda x: x['end'], reverse=True)[0]
            raw_val = latest['val']
            # Format to Billions for easy viewing
            revenue_val = f"${raw_val / 1_000_000_000:.2f}B"
    
    print(f"Step 3 Success: Latest {rev_tag}: {revenue_val}")
    print(f"\n--- TEST COMPLETE: Data is ready for Main Page ---\n")

# Run it
run_pilot_test("AAPL")
