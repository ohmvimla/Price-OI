import time
import requests
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. GOOGLE SHEETS SETUP ---
# अपनी डाउनलोड की हुई JSON फाइल का नाम यहाँ लिखें
JSON_KEY_FILE = 'credentials.json'
# अपनी Google Sheet का सटीक नाम यहाँ लिखें
SPREADSHEET_NAME = 'Nifty_Derivatives_Data'
# शीट के टैब (Tab) का नाम
SHEET_TAB_NAME = 'pRICE oi'

def get_google_sheet():
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_KEY_FILE, scope)
client = gspread.authorize(creds)
sheet = client.open(SPREADSHEET_NAME).worksheet(SHEET_TAB_NAME)
return sheet

# --- 2. NSE DERIVATIVES DATA FETCH ---
def fetch_nse_derivatives():
# NSE API के लिए Headers और Session सेट करना अनिवार्य है (ताकि 403 Error न आए)
headers = {
User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
Accept-Encoding': 'gzip, deflate, br',
Accept-Language': 'en-US,en;q=0.9'
}

session = requests.Session()
# कुकीज़ इनिशियलाइज़ करने के लिए होमपेज पर जाना ज़रूरी है
session.get("https://www.nseindia.com", headers=headers)

# F&O स्टॉक्स का लाइव डेटा एंडपॉइंट
url = "https://www.nseindia.com/api/live-fno-snapshot-derivatives"

print("NSE से डेटा निकाला जा रहा है...")
response = session.get(url, headers=headers)

if response.status_code == 200:
data = response.json()
raw_list = data.get('data', [])

extracted_data = []
for item in raw_list:
# केवल STOCKS का डेटा फ़िल्टर कर रहे हैं (इंडेक्स जैसे NIFTY/BANKNIFTY को छोड़कर)
if item.get('instrumentType') == 'FUTSTK':
extracted_data.append({
Ticker': item.get('symbol'),
Expiry Date': item.get('expiryDate'),
Underlying Value (Price)': item.get('underlyingValue'),
Price Change (%)': item.get('pChange'),
Open Interest (OI)': item.get('openInterest'),
OI Change (%)': item.get('pchangeinOpenInterest')
})

df = pd.DataFrame(extracted_data)
# डुप्लिकेट्स हटाकर केवल करंट/निकटतम एक्सपायरी का डेटा रखने के लिए
df = df.drop_duplicates(subset=['Ticker'], keep='first')
return df
else:
print(f"डेटा लाने में विफलता। Status Code: {response.status_code}")
return None

# --- 3. MAIN EXECUTION ---
def main():
try:
# डेटा लाएं
df_fno = fetch_nse_derivatives()

if df_fno is not None and not df_fno.empty:
# Google Sheet से कनेक्ट करें
sheet = get_google_sheet()

# शीट को साफ़ करें और हेडर सेट करें
sheet.clear()

# डेटा फ्रेम को लिस्ट ऑफ लिस्ट्स में बदलें ताकि शीट में डाला जा सके
headers = df_fno.columns.tolist()
values = df_fno.values.tolist()

# हेडर और डेटा को शीट में अपलोड करें
sheet.update('A1', [headers] + values)
print("Google Sheet को सफलतापूर्वक अपडेट कर दिया गया है! ✅")
else:
print("कोई डेटा नहीं मिला।")

except Exception as e:
print(f"त्रुटि (Error): {e}")

if __name__ == "__main__":
main()
