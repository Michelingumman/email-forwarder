# Email Forwarder

An advanced Python script that manages church newsletter distribution with bidirectional email forwarding and automatic status reporting.

## How It Works

The script monitors `brev@sodertornkyrkan.se` and provides intelligent email forwarding:

1. **Newsletter Distribution**: Forwards emails from admin to subscribers (with subject filtering)
2. **Subscriber Feedback**: Forwards emails from subscribers to admin  
3. **Status Reporting**: Automatically notifies admin of delivery success/failures

## Features

- ✅ **Subject filtering**: Only forwards emails containing "församlingsbrev"
- ✅ **Bidirectional forwarding**: Admin ↔ Subscribers
- ✅ **Automatic status reports** to admin after newsletter distribution
- ✅ **Persistent IMAP/SMTP connections** for better performance
- ✅ **Smart CSV reloading** (only when file changes)
- ✅ **Graceful shutdown** with Ctrl+C
- ✅ **Swedish character support** (ÅÄÖ)
- ✅ **Attachment forwarding** (PDFs, images, etc.)
- ✅ **HTML and plain text** email support

## Email Flow

### Newsletter Distribution (Admin → Subscribers)
```
mattias.michelin@gmail.se
    ↓ (sends email with subject containing "församlingsbrev")
brev@sodertornkyrkan.se 
    ↓ (script processes & forwards)
All subscribers in CSV
    ↓ (automatic status report)
mattias.michelin@gmail.se (receives "Everything worked!" or failure details)
```

### Subscriber Feedback (Subscribers → Admin)  
```
Any subscriber from CSV
    ↓ (sends email)
brev@sodertornkyrkan.se
    ↓ (script forwards with [FROM SUBSCRIBER] prefix)
mattias.michelin@gmail.se
```

## How to Run

### 1. Setup Configuration
The script is pre-configured for Södertörnkyrkan:
```python
IMAP_HOST = "mail.sodertornkyrkan.se"
SMTP_HOST = "mail.sodertornkyrkan.se"  
EMAIL = "brev@sodertornkyrkan.se"
ADMIN_EMAIL = "mattias.michelin@gmail.se"
```

### 2. Add Subscribers
Edit `subscribers.csv` and add subscriber emails:
```csv
email
subscriber1@example.com
subscriber2@gmail.com
```

### 3. Run the Script
```bash
python email_forwarder.py
```

### 4. Send Newsletter
Send email from `mattias.michelin@gmail.se` to `brev@sodertornkyrkan.se` with subject containing "församlingsbrev"

### 5. Stop the Script
Press `Ctrl+C` for graceful shutdown

## Project Structure
```
├── email_forwarder.py    # Main script
├── subscribers.csv       # List of subscriber emails
├── requirements.txt      # Dependencies (built-in modules only)
└── README.md            # This file
```

## Subject Filtering

**Only emails with subjects containing "församlingsbrev" get forwarded to subscribers:**

✅ "Församlingsbrev Juli 2024" → **Forwarded**  
✅ "Viktigt meddelande - församlingsbrev" → **Forwarded**  
❌ "Hej, hur mår du?" → **Ignored**  

## Automatic Status Reports

After newsletter distribution, admin receives:

**Success:**
```
Subject: Newsletter Status: Församlingsbrev Juli 2024
Everything worked! Newsletter 'Församlingsbrev Juli 2024' successfully sent to all 15 subscribers.
```

**Partial failure:**
```
Subject: Newsletter Status: Församlingsbrev Juli 2024  
Newsletter 'Församlingsbrev Juli 2024' sent to 13/15 subscribers.

Failed to send to:
problematic@email.com
invalid@domain.org
```

## Dependencies
- Python 3.6+ (uses built-in modules only)
- dotenv for secure password handling is required, shown in requirements.txt

## Notes
- Script checks for new emails every 10 seconds
- Updates subscriber list automatically when CSV file changes
- Supports Swedish characters (ÅÄÖ) in all content
- Forwards all email types: text, HTML, and attachments
- Provides detailed logging of all operations 