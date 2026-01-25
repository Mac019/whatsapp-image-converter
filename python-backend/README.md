# WhatsApp Image to PDF Converter - Python Backend

## Quick Start

1. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Run the server:**
```bash
uvicorn main:app --reload --port 8000
```

4. **Expose for Meta webhook (use ngrok):**
```bash
ngrok http 8000
```

5. **Configure Meta webhook:**
   - Go to your Meta app dashboard
   - Set webhook URL to: `https://your-ngrok-url/webhook/whatsapp`
   - Use the verify token you configured in the admin dashboard

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/webhook/whatsapp` | Meta webhook verification |
| POST | `/webhook/whatsapp` | Receive WhatsApp messages |
| GET | `/api/admin/stats` | Get conversion statistics |
| GET | `/api/admin/conversions` | List recent conversions |
| GET | `/api/admin/settings` | Get current settings |
| POST | `/api/admin/settings` | Save Meta credentials |
| GET | `/health` | Health check |

## Project Structure

```
python-backend/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── utils/
│   ├── __init__.py
│   ├── whatsapp.py      # Meta WhatsApp API functions
│   ├── converter.py     # Image to PDF conversion
│   └── storage.py       # Settings & logs storage
└── data/                # Created automatically
    ├── settings.json    # Stored credentials
    └── conversions.json # Conversion logs
```

## Environment Variables (Optional)

You can also use environment variables instead of the admin dashboard:

```bash
export WHATSAPP_BUSINESS_ACCOUNT_ID="your_account_id"
export PHONE_NUMBER_ID="your_phone_number_id"
export ACCESS_TOKEN="your_access_token"
export WEBHOOK_VERIFY_TOKEN="your_verify_token"
```
