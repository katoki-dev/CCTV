# Email Alert System - Setup Guide

## Overview
The CEMSS system now supports **both Email and WhatsApp alerts** for detection events. Email alerts include:
- ✅ HTML-formatted messages with detection details
- ✅ Video clip attachments (if available)
- ✅ Severity-based color coding
- ✅ Support for multiple recipients

## Configuration

### Step 1: Enable Email in `.env`

Copy `.env.example` to `.env` and configure the email settings:

```env
# Enable email alerts
EMAIL_ENABLED=True

# Gmail SMTP Settings (recommended)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False

# Your Gmail credentials
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-16-char-app-password

# Sender information
EMAIL_FROM_ADDRESS=your-email@gmail.com
EMAIL_FROM_NAME=CEMSS Alert System

# Recipients (comma-separated)
EMAIL_RECIPIENT_LIST=admin@example.com,security@example.com
```

### Step 2: Generate Gmail App Password

If using Gmail:

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable **2-Step Verification** (if not already enabled)
3. Go to [App Passwords](https://myaccount.google.com/apppasswords)
4. Select "Mail" and "Other (Custom name)"
5. Enter "CEMSS Alert System"
6. Copy the 16-character password
7. Use this password in `EMAIL_PASSWORD` (not your regular Gmail password)

### Step 3: Configure Other SMTP Providers

#### Outlook/Hotmail
```env
EMAIL_HOST=smtp-mail.outlook.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USERNAME=your-email@outlook.com
EMAIL_PASSWORD=your-password
```

#### Yahoo Mail
```env
EMAIL_HOST=smtp.mail.yahoo.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USERNAME=your-email@yahoo.com
EMAIL_PASSWORD=your-app-password
```

#### Custom SMTP Server
```env
EMAIL_HOST=smtp.yourdomain.com
EMAIL_PORT=587  # or 465 for SSL
EMAIL_USE_TLS=True  # or False if using SSL
EMAIL_USE_SSL=False  # or True for port 465
EMAIL_USERNAME=alerts@yourdomain.com
EMAIL_PASSWORD=your-password
```

## Features

### Detection Alerts
- **Automatic alerts** for person, fall, phone, and crowd detection
- **Severity-based formatting** (LOW/MEDIUM/HIGH/CRITICAL)
- **Video clip attachments** when available
- **Zone information** for restricted zone violations
- **Rich HTML formatting** with color-coded severity levels

### Manual Alerts
- Trigger alerts from the dashboard
- Include custom messages
- Attach video clips
- Send to all configured recipients

### Rate Limiting
- Prevents alert spam
- Configurable cooldown periods
- Maximum alerts per hour limit

## Testing Email Alerts

### Option 1: Using Python directly

```python
from alerts.email_service import get_email_service
from datetime import datetime

# Get email service instance
email_service = get_email_service()

# Test send
success = email_service.send_detection_alert(
    recipients=['test@example.com'],
    camera_name='Front Door',
    model_name='person',
    confidence=0.95,
    timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    detection_count=1,
    severity_level='HIGH',
    severity_score=8
)

print(f"Email sent: {success}")
```

### Option 2: Trigger a detection
1. Start the CEMSS system
2. Enable detection on a camera
3. Trigger a detection event
4. Check your configured email addresses

## Troubleshooting

### Email not sending

1. **Check credentials**
   ```bash
   # Verify SMTP settings in .env
   cat .env | grep EMAIL
   ```

2. **Test SMTP connection**
   ```python
   import smtplib
   server = smtplib.SMTP('smtp.gmail.com', 587)
   server.starttls()
   server.login('your-email@gmail.com', 'your-app-password')
   server.quit()
   print("✓ SMTP connection successful")
   ```

3. **Check firewall**
   - Ensure outbound SMTP ports (587/465) are not blocked

4. **Gmail-specific issues**
   - Verify 2-Step Verification is enabled
   - Use App Password, not regular password
   - Check "Less secure app access" is NOT needed (App Passwords bypass this)

### Attachment size issues

- Gmail: Max 25MB per email
- Video clips are typically 1-5MB
- If clips are too large, consider:
  - Reducing `VIDEO_CLIP_DURATION` in config.py
  - Lowering `VIDEO_FPS` setting
  - Using a different codec in `VIDEO_CODEC`

## Email + WhatsApp Integration

Both systems work **simultaneously**:
- Email alerts include video attachments
- WhatsApp alerts are text-only (instant)
- Recipients are configured separately
- Users can receive both or either

### Configure recipients

**Email only:**
```env
EMAIL_ENABLED=True
EMAIL_RECIPIENT_LIST=user@example.com
WHATSAPP_PHONE_NUMBERS=
```

**WhatsApp only:**
```env
EMAIL_ENABLED=False
WHATSAPP_PHONE_NUMBERS=+911234567890
```

**Both:**
```env
EMAIL_ENABLED=True
EMAIL_RECIPIENT_LIST=user@example.com
WHATSAPP_PHONE_NUMBERS=+911234567890
```

## Security Best Practices

1. **Never commit `.env` to version control**
2. **Use App Passwords** instead of regular passwords
3. **Enable 2FA** on your email account
4. **Rotate passwords** regularly
5. **Limit recipient list** to necessary personnel
6. **Monitor alert logs** for unusual activity

## Support

For issues or questions:
1. Check logs in `logs/` directory
2. Verify `.env` configuration
3. Test SMTP connection manually
4. Review email service logs for detailed errors
