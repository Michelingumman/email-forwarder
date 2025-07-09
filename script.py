import imaplib
import smtplib
import email
import csv
import time
import os
import signal
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

import dotenv
dotenv.load_dotenv()

# Configuration
IMAP_HOST = "mail.sodertornkyrkan.se"
SMTP_HOST = "mail.sodertornkyrkan.se"
EMAIL = "brev@sodertornkyrkan.se"
PASSWORD = os.getenv("PASSWORD")
ADMIN_EMAIL = "mattias.michelin@gmail.com"
SUBSCRIBERS_FILE = "sodertornkyrkan-members.csv"

# Check for required environment variables
if not PASSWORD:
    print("❌ ERROR: PASSWORD environment variable not found!")
    print("Please create a .env file with: PASSWORD=your_password_here")
    sys.exit(1)

# Logging control
VERBOSE_LOGGING = False  # Set to True for detailed logging, False for clean output

# Global variables for connections and data
imap = None
smtp = None
subscribers = []
csv_last_modified = 0

def log_verbose(message):
    """Print message only if verbose logging is enabled"""
    if VERBOSE_LOGGING:
        print(message)

def log_info(message):
    """Print important information always"""
    print(message)

def load_subscribers():
    """Load subscribers from CSV file, only if file has changed"""
    global subscribers, csv_last_modified
    
    try:
        current_modified = os.path.getmtime(SUBSCRIBERS_FILE)
        if current_modified != csv_last_modified:
            subscribers = []
            with open(SUBSCRIBERS_FILE, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # Filter by the specified criteria
                    if (row['Status'].strip().lower() == 'active' and 
                        row['Membership'].strip().lower() == 'member' and 
                        row['Child'].strip().lower() == 'false' and
                        row['Home Email'].strip()):  # Check email exists and not empty
                        email = row['Home Email'].strip()
                        if email:  # Double check email is not empty
                            subscribers.append(email)
            csv_last_modified = current_modified
            log_info(f"📋 Loaded {len(subscribers)} active members with emails from database")
        return True
    except FileNotFoundError:
        log_info(f"❌ Error: {SUBSCRIBERS_FILE} not found")
        return False
    except Exception as e:
        log_info(f"❌ Error loading CSV: {e}")
        return False

def connect_imap():
    """Connect to IMAP server"""
    global imap
    try:
        if imap:
            imap.close()
            imap.logout()
    except:
        pass
    
    imap = imaplib.IMAP4_SSL(IMAP_HOST, 993)
    imap.login(EMAIL, PASSWORD)
    imap.select("INBOX")
    log_verbose("🔗 Connected to IMAP server")

def connect_smtp():
    """Connect to SMTP server"""
    global smtp
    try:
        if smtp:
            smtp.quit()
    except:
        pass
    
    smtp = smtplib.SMTP_SSL(SMTP_HOST, 465)
    if VERBOSE_LOGGING:
        smtp.set_debuglevel(1)  # Enable SMTP debugging only in verbose mode
    smtp.login(EMAIL, PASSWORD)
    log_verbose("📤 Connected to SMTP server")

def cleanup_and_exit(signum=None, frame=None):
    """Clean shutdown handler"""
    log_info("\n🛑 Shutting down gracefully...")
    try:
        if imap:
            imap.close()
            imap.logout()
    except:
        pass
    try:
        if smtp:
            smtp.quit()
    except:
        pass
    log_info("✅ Connections closed. Goodbye!")
    sys.exit(0)

def check_connections():
    """Check and reconnect if connections are lost"""
    global imap, smtp
    
    # Check IMAP connection
    try:
        imap.noop()
    except:
        log_verbose("🔄 IMAP connection lost, reconnecting...")
        connect_imap()
    
    # Check SMTP connection
    try:
        smtp.noop()
    except:
        log_verbose("🔄 SMTP connection lost, reconnecting...")
        connect_smtp()

# Set up signal handlers for graceful shutdown
signal.signal(signal.SIGINT, cleanup_and_exit)
signal.signal(signal.SIGTERM, cleanup_and_exit)

log_info("🚀 Email forwarder started...")
if VERBOSE_LOGGING:
    log_info("📝 Verbose logging enabled")
else:
    log_info("🔇 Quiet mode - only essential messages shown (set VERBOSE_LOGGING=True for details)")

# Initial connections and data loading
try:
    connect_imap()
    connect_smtp()
    if not load_subscribers():
        log_info("❌ Failed to load initial subscribers")
        cleanup_and_exit()
    log_info("✅ System ready - monitoring for emails...")
except Exception as e:
    log_info(f"❌ Initial setup failed: {e}")
    cleanup_and_exit()

def send_reply_to_admin(subject, message):
    """Send a reply email to the admin"""
    try:
        reply_msg = MIMEMultipart()
        reply_msg["From"] = EMAIL
        reply_msg["To"] = ADMIN_EMAIL
        reply_msg["Subject"] = f"Newsletter Status: {subject}"
        reply_msg.attach(MIMEText(message, "plain", "utf-8"))
        
        smtp.send_message(reply_msg)
        log_verbose(f"📧 Sent status reply to admin: {message}")
        return True
    except Exception as e:
        log_info(f"❌ Failed to send reply to admin: {e}")
        return False

def process_admin_email(msg, subject):
    """Process email from admin - forward to subscribers if subject contains 'församlingsbrev'"""
    if "samlingsbrev" not in subject.lower():
        log_info(f"⏭️ Skipping '{subject}' - doesn't contain 'församlingsbrev'")
        return
    
    log_info(f"📬 Processing newsletter: {subject}")
    
    sent_count = 0
    failed_subscribers = []
    
    for subscriber in subscribers:
        try:
            log_verbose(f"Preparing email for {subscriber}...")
            
            # Create new message with all parts (text, html, attachments)
            forward_msg = MIMEMultipart()
            forward_msg["From"] = EMAIL
            forward_msg["To"] = subscriber
            forward_msg["Subject"] = subject
            
            # Collect content parts separately
            text_content = None
            html_content = None
            attachments = []
            
            # Handle multipart messages (with attachments/html)
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition", ""))
                    
                    # Collect text content (check for inline content too)
                    if content_type == "text/plain" and not text_content:
                        # Skip if it's clearly an attachment
                        if "attachment" not in content_disposition:
                            try:
                                text_content = part.get_payload(decode=True).decode('utf-8')
                            except UnicodeDecodeError:
                                try:
                                    text_content = part.get_payload(decode=True).decode('iso-8859-1')
                                except UnicodeDecodeError:
                                    text_content = part.get_payload(decode=True).decode('utf-8', errors='replace')
                            log_verbose(f"Found text content: {len(text_content)} characters")
                    
                    # Collect HTML content (check for inline content too)
                    elif content_type == "text/html" and not html_content:
                        # Skip if it's clearly an attachment
                        if "attachment" not in content_disposition:
                            try:
                                html_content = part.get_payload(decode=True).decode('utf-8')
                            except UnicodeDecodeError:
                                try:
                                    html_content = part.get_payload(decode=True).decode('iso-8859-1')
                                except UnicodeDecodeError:
                                    html_content = part.get_payload(decode=True).decode('utf-8', errors='replace')
                            log_verbose(f"Found HTML content: {len(html_content)} characters")
                    
                    # Collect actual file attachments
                    elif ("attachment" in content_disposition and part.get_filename()) or \
                         (part.get_filename() and content_type not in ["text/plain", "text/html"]):
                        filename = part.get_filename()
                        attachment = MIMEBase('application', 'octet-stream')
                        attachment.set_payload(part.get_payload(decode=True))
                        encoders.encode_base64(attachment)
                        attachment.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {filename}'
                        )
                        attachments.append(attachment)
                        log_verbose(f"Found attachment: {filename}")
            else:
                # Handle simple text messages
                try:
                    text_content = msg.get_payload(decode=True).decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        text_content = msg.get_payload(decode=True).decode('iso-8859-1')
                    except UnicodeDecodeError:
                        text_content = msg.get_payload(decode=True).decode('utf-8', errors='replace')
                log_verbose(f"Found simple text content: {len(text_content)} characters")
            
            # Debug: Show what content we found
            log_verbose(f"Content summary: Text={len(text_content) if text_content else 0} chars, HTML={len(html_content) if html_content else 0} chars, Attachments={len(attachments)}")
            
            # Add content to message - prefer HTML over plain text
            if html_content:
                forward_msg.attach(MIMEText(html_content, "html", "utf-8"))
                log_verbose("Added HTML content to forwarded message")
            elif text_content:
                forward_msg.attach(MIMEText(text_content, "plain", "utf-8"))
                log_verbose("Added text content to forwarded message")
            else:
                # Fallback: add a simple message if no content found
                forward_msg.attach(MIMEText("Email forwarded from admin", "plain", "utf-8"))
                log_verbose("No content found, added fallback message")
            
            # Add any attachments
            for attachment in attachments:
                forward_msg.attach(attachment)
                log_verbose("Attached file to forwarded message")
            
            # Send message using persistent connection
            log_verbose(f"Sending to {subscriber}...")
            smtp.send_message(forward_msg)
            sent_count += 1
            if VERBOSE_LOGGING:
                log_verbose(f"✅ Successfully sent to {subscriber}")
            
        except Exception as e:
            log_info(f"❌ Error sending to {subscriber}: {e}")
            failed_subscribers.append(subscriber)
            # Try to reconnect SMTP if sending fails
            try:
                log_verbose("Attempting to reconnect SMTP...")
                connect_smtp()
            except Exception as reconnect_error:
                log_info(f"SMTP reconnection failed: {reconnect_error}")
            continue
    
    # Send status reply to admin
    if failed_subscribers:
        reply_message = f"Newsletter '{subject}' sent to {sent_count}/{len(subscribers)} subscribers.\n\nFailed to send to:\n" + "\n".join(failed_subscribers)
        log_info(f"⚠️ Newsletter sent to {sent_count}/{len(subscribers)} subscribers ({len(failed_subscribers)} failed)")
    else:
        reply_message = f"Everything worked! Newsletter '{subject}' successfully sent to all {sent_count} subscribers."
        log_info(f"✅ Newsletter '{subject}' successfully sent to all {sent_count} subscribers")
    
    send_reply_to_admin(subject, reply_message)

def process_subscriber_email(msg, subject, sender):
    """Process email from subscriber - forward to admin"""
    try:
        log_info(f"📩 Forwarding subscriber email from {sender} to admin")
        
        # Create forward message
        forward_msg = MIMEMultipart()
        forward_msg["From"] = EMAIL
        forward_msg["To"] = ADMIN_EMAIL
        forward_msg["Subject"] = f"[FROM SUBSCRIBER] {subject}"
        
        # Add original sender info
        original_info = f"Original sender: {sender}\nOriginal subject: {subject}\n\n"
        
        # Get message content
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    try:
                        body = part.get_payload(decode=True).decode('utf-8')
                    except UnicodeDecodeError:
                        try:
                            body = part.get_payload(decode=True).decode('iso-8859-1')
                        except UnicodeDecodeError:
                            body = part.get_payload(decode=True).decode('utf-8', errors='replace')
                    forward_msg.attach(MIMEText(original_info + body, "plain", "utf-8"))
                    break
        else:
            try:
                body = msg.get_payload(decode=True).decode('utf-8')
            except UnicodeDecodeError:
                try:
                    body = msg.get_payload(decode=True).decode('iso-8859-1')
                except UnicodeDecodeError:
                    body = msg.get_payload(decode=True).decode('utf-8', errors='replace')
            forward_msg.attach(MIMEText(original_info + body, "plain", "utf-8"))
        
        # Send to admin
        smtp.send_message(forward_msg)
        log_info(f"✅ Subscriber email forwarded to admin")
        
    except Exception as e:
        log_info(f"❌ Error forwarding subscriber email: {e}")

while True:
    try:
        # Check if CSV file has been updated and reload if needed
        load_subscribers()
        
        if not subscribers:
            log_verbose("No subscribers found, skipping...")
            time.sleep(60)
            continue
        
        # Check connections and reconnect if needed
        check_connections()
        
        # Search for ALL unseen messages
        status, messages = imap.search(None, 'UNSEEN')
        
        if messages[0]:
            message_ids = messages[0].split()
            
            for msg_id in message_ids:
                try:
                    # Fetch the message
                    status, msg_data = imap.fetch(msg_id, "(RFC822)")
                    msg = email.message_from_bytes(msg_data[0][1])
                    
                    # Extract subject and sender
                    subject = msg["Subject"] or "No Subject"
                    sender = msg["From"] or "Unknown Sender"
                    
                    log_info(f"📨 New email from {sender}: {subject}")
                    
                    # Mark as seen
                    imap.store(msg_id, "+FLAGS", "\\Seen")
                    
                    # Check if email is from admin
                    if ADMIN_EMAIL.lower() in sender.lower():
                        process_admin_email(msg, subject)
                    # Check if email is from a subscriber
                    elif any(subscriber.lower() in sender.lower() for subscriber in subscribers):
                        process_subscriber_email(msg, subject, sender)
                    else:
                        log_verbose(f"⏭️ Ignoring email from unknown sender: {sender}")
                    
                except Exception as e:
                    log_info(f"❌ Error processing message {msg_id}: {e}")
                    continue
        else:
            log_verbose("📭 No new emails")
        
    except KeyboardInterrupt:
        cleanup_and_exit()
    except Exception as e:
        log_info(f"🔌 Connection error: {e}")
        log_info("🔄 Retrying in 60 seconds...")
        try:
            connect_imap()
            connect_smtp()
        except:
            pass
    
    # Wait 10 seconds before checking again
    try:
        time.sleep(10)
    except KeyboardInterrupt:
        cleanup_and_exit() 