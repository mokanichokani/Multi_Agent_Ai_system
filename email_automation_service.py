import imaplib
import email
from email.header import decode_header
import time
import os
from dotenv import load_dotenv
from agents.classifier_agent import ClassifierAgent
from memory.shared_memory import shared_memory_instance

load_dotenv()

IMAP_SERVER = os.getenv("IMAP_SERVER")
EMAIL_USER = os.getenv("EMAIL_AUTOMATION_USER")
EMAIL_PASS = os.getenv("EMAIL_AUTOMATION_APP_PASSWORD")
MAILBOX_TO_MONITOR = "INBOX"
POLL_INTERVAL_SECONDS = 60

classifier = ClassifierAgent()

def decode_subject(msg):
    subject_parts = decode_header(msg["Subject"])
    subject = ""
    for part, charset in subject_parts:
        if isinstance(part, bytes):
            subject += part.decode(charset if charset else 'utf-8', errors='ignore')
        else:
            subject += part
    return subject

def fetch_email_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            if "attachment" not in content_disposition:
                if content_type == "text/plain":
                    try:
                        return part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8', errors='ignore')
                    except:
                        pass
                elif content_type == "text/html":
                    try:
                        html_body = part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8', errors='ignore')
                        return html_body
                    except:
                        pass
    else:
        if msg.get_content_type() == "text/plain":
            try:
                return msg.get_payload(decode=True).decode(msg.get_content_charset() or 'utf-8', errors='ignore')
            except:
                return "Could not decode plain text body."
    return "No suitable text body found."

def process_new_emails(mail):
    status, messages = mail.search(None, 'UNSEEN')
    if status != 'OK':
        print("Error searching for emails.")
        return
    email_ids = messages[0].split()
    print(f"Found {len(email_ids)} new email(s).")
    for email_id in email_ids:
        print(f"\nFetching email ID: {email_id.decode()}")
        status, msg_data = mail.fetch(email_id, '(RFC822)')
        if status != 'OK':
            print(f"Error fetching email ID {email_id.decode()}")
            continue
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                subject = decode_subject(msg)
                sender = msg.get("From")
                body = fetch_email_body(msg)
                print(f"  From: {sender}")
                print(f"  Subject: {subject}")
                print(f"  Body Preview: {body[:100]}...")
                email_content_for_classification = f"Subject: {subject}\n\nFrom: {sender}\n\n{body}"
                source_identifier = f"Email: {subject} (from {sender})"
                try:
                    thread_id, result = classifier.process(
                        input_data=email_content_for_classification,
                        source_identifier=source_identifier,
                        source_type="automated_email_ingestion"
                    )
                    print(f"  Processed by system. Thread ID: {thread_id}")
                except Exception as e:
                    print(f"  Error processing email with ClassifierAgent: {e}")

def main_loop():
    print("Starting Email Automation Service...")
    print(f"Connecting to {IMAP_SERVER} for user {EMAIL_USER}...")
    while True:
        try:
            mail = imaplib.IMAP4_SSL(IMAP_SERVER)
            mail.login(EMAIL_USER, EMAIL_PASS)
            mail.select(MAILBOX_TO_MONITOR)
            print(f"Successfully connected. Monitoring '{MAILBOX_TO_MONITOR}'.")
            process_new_emails(mail)
            mail.logout()
            print("Logged out. Waiting for next poll cycle...")
        except imaplib.IMAP4.abort as e:
            print(f"IMAP connection aborted: {e}. Retrying in {POLL_INTERVAL_SECONDS}s...")
        except imaplib.IMAP4.error as e:
            print(f"IMAP error: {e}. Retrying in {POLL_INTERVAL_SECONDS}s...")
        except ConnectionRefusedError as e:
            print(f"Connection refused: {e}. Check server/port. Retrying in {POLL_INTERVAL_SECONDS}s...")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        time.sleep(POLL_INTERVAL_SECONDS)

if __name__ == "__main__":
    if not all([IMAP_SERVER, EMAIL_USER, EMAIL_PASS]):
        print("Error: IMAP_SERVER, EMAIL_AUTOMATION_USER, or EMAIL_AUTOMATION_APP_PASSWORD not set in .env")
    else:
        main_loop()