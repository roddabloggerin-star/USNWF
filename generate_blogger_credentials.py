"""
This script performs a one-time setup to generate OAuth 2.0 credentials
for the Blogger API to be used in non-interactive environments like GitHub Actions.

RUN THIS SCRIPT LOCALLY ON YOUR MACHINE.

1. Make sure you have the required libraries installed:
   pip install google-auth-oauthlib google-auth-httplib2

2. Execute this script from your terminal:
   python generate_blogger_credentials.py

3. Follow the URL provided in your browser to authorize the application.

4. After authorization, you will be redirected to a localhost page.
   Copy the authorization code from the page and paste it back into the terminal.

5. The script will print a JSON object.
   Copy the ENTIRE JSON output.

6. Go to your GitHub repository > Settings > Secrets and variables > Actions.
   Click "New repository secret".
   Name: BLOGGER_CREDENTIALS_JSON
   Value: Paste the entire JSON output from this script.
"""

import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# --- CONFIGURATION ---
# You MUST fill in these details from your Google Cloud Console project
CLIENT_SECRETS_FILE = "client_secrets.json" # Download this from Google Cloud Console
SCOPES = ['https://www.googleapis.com/auth/blogger']
# ---------------------

def main():
    """Runs the OAuth 2.0 flow to generate credentials."""
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    creds = flow.run_local_server(port=0)

    # The credentials object contains the access token, refresh token, etc.
    # We need to save this entire object to be used later.
    creds_dict = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
        "expiry": creds.expiry.isoformat() if creds.expiry else None
    }

    print("\n" + "="*50)
    print("SUCCESS! Your credentials have been generated.")
    print("="*50)
    print("\nCopy the following JSON object in its entirety:")
    print("-"*50)
    print(json.dumps(creds_dict, indent=2))
    print("-"*50)
    print("\nNow, add this as a new secret in your GitHub repository:")
    print("  Secret Name: BLOGGER_CREDENTIALS_JSON")
    print("  Secret Value: <Paste the entire JSON output above>")
    print("\nAfter adding the secret, you can delete this script and the 'client_secrets.json' file.")


if __name__ == "__main__":
    if not os.path.exists(CLIENT_SECRETS_FILE):
        print(f"Error: The file '{CLIENT_SECRETS_FILE}' was not found.")
        print("Please download your OAuth 2.0 Client ID and Secret from the Google Cloud Console")
        print("and save them in a file named 'client_secrets.json' in the same directory as this script.")
    else:
        main()