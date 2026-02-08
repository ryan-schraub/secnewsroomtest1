import requests
import time

# SEC COMPLIANCE: Use your actual email so the SEC doesn't throttle you
HEADERS = {
    'User-Agent': 'SECTicker (conantbball2@yahoo.com)',
    'Accept-Encoding': 'gzip, deflate',
    'Host': 'data.sec.gov'
}

def get_revenue_waterfall(cik, headers):
    """
    Checks multiple SEC tags in order of priority to find the 
    actual 'Total Revenue' for a company.
    """
    # Priority order:
    # 1. Contract Revenue (Apple, Microsoft, Google)
    # 2. Net Sales (Retail/Manufacturing like Walmart/Ford)
    # 3. Generic Revenues (Service/Finance)
    tags = [
        'RevenueFromContractWithCustomerExcludingAssessedTax',
        'SalesRevenueNet',
        'Revenues',
        'OperatingRevenueRetail'
    ]
    
    for tag in tags:
        try:
            url = f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{tag}.json"
            resp = requests.get(url, headers=headers)
            
            if resp.status_code == 200:
                data = resp.json()
                # units/USD contains the dollar values
                if 'units' in data and 'USD' in data['units']:
                    # Filter for 10-K (Annual) data only
                    annual_data = [
                        entry for entry in data['units']['USD'] 
                        if entry.get('form') == '10-K'
                    ]
                    
                    if annual_data:
                        # Get the most recent entry based on the 'end' date
                        latest = sorted(annual_data, key=lambda x: x['end'], reverse=True)[0]
                        return latest['val'], tag # Return value and which tag worked
        except Exception:
            continue
            
    return None, None

def run_pilot_test(ticker):
    ticker = ticker.upper()
    print(f"--- Starting Pilot Test for {ticker} ---")

    # 1. Get CIK from Ticker
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

    # 2. Fetch Metadata
    sub_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    sub_data = requests.get(sub_url, headers=HEADERS).json()
    
    industry = sub_data.get('sicDescription', 'N/A')
    location = f"{sub_data.get('addresses', {}).get('business', {}).get('city')}, {sub_data.get('addresses', {}).get('business', {}).get('stateOrProvince')}"
    
    print(f"Step 2 Success: Industry: {industry} | Location: {location}")

    # 3. Fetch Revenue using Waterfall Logic
    raw_revenue, tag_used = get_revenue_waterfall(cik, HEADERS)
    
    if raw_revenue:
        # Formatting for display
        if raw_revenue >= 1_000_000_000:
            formatted_rev = f"${raw_revenue / 1_000_000_000:.2f}B"
        else:
            formatted_rev = f"${raw_revenue / 1_000_000:.2f}M"
        print(f"Step 3 Success: Found {formatted_rev} using tag: {tag_used}")
    else:
        print("Step 3 Failed: No revenue data found in standard tags.")

    print(f"\n--- TEST COMPLETE ---\n")

# Test with Apple to see the $416B result
run_pilot_test("AAPL")
