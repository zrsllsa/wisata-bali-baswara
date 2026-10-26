import os
import smtplib
from dotenv import load_dotenv

load_dotenv()

email = os.getenv("SMTP_EMAIL")
password = os.getenv("SMTP_PASSWORD")

print("EMAIL:", email)
print("PASSWORD ADA:", bool(password))

try:
    print("Connecting to smtp.gmail.com:465...")

    server = smtplib.SMTP_SSL(
        "smtp.gmail.com",
        465,
        timeout=30
    )

    print("Connected SSL")

    server.login(email, password)

    print("LOGIN BERHASIL!")

    server.quit()

except Exception as e:
    print("ERROR:", type(e).__name__, repr(e))