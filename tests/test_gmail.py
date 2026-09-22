from app.services.auth_services import AuthService
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def generate_local_token():
    # Make sure credentials.json is in your root directory!
    flow = InstalledAppFlow.from_client_secrets_file(
        "credentials.json", 
        SCOPES
    )
    
    # Opens a browser window on your computer to log into Google
    creds = flow.run_local_server(port=0)
    
    # Saves the generated token file locally
    with open("token.json", "w") as token_file:
        token_file.write(creds.to_json())
        
    print("[SUCCESS] token.json generated successfully!")


def test_send():
    print("Sending test email via Gmail REST API...")
    
    success = AuthService.send_email(
        to="Llightboth369@gmail.com",  # Replace with your target email
        subject="Test OTP Email",
        body="This is a plain text test email.",
        html="<h1>OTP Code: 123456</h1><p>Sent via Gmail API!</p>"
    )
    
    if success:
        print("Test passed! Check your inbox.")
    else:
        print("Test failed. Check the error logs above.")

if __name__ == "__main__":
    generate_local_token()
    test_send()