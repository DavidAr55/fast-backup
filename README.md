# Automated Backup System for Google Drive or (Fast-Backup)

An automated backup solution that compresses directories and uploads them to Google Drive on a scheduled basis, with tracking through SQLite database and detailed logging.

## Features

- 🔒 **Secure Google Drive Integration**: OAuth2 authentication with token management
- 🗄️ **Database Tracking**: Maintains backup history with status tracking (Success/Failure)
- ⏲️ **Smart Scheduling**: Daily checks with configurable backup intervals (default: 3 days)
- 📦 **Directory Compression**: Creates ZIP archives with DEFLATE compression
- 📝 **Detailed Logging**: Dual logging to file and console with timestamps
- 🛠️ **Configuration Management**: Environment variables for sensitive data
- 📂 **Folder Management**: Auto-creates dedicated backup folder in Google Drive

## Prerequisites

- Python 3.10.0+
- Google account with Drive API enabled
- Basic terminal/command prompt knowledge

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/DavidAr55/fast-backup.git
   cd fast-backup
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

### Google Drive API Setup

1. Create a project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable **Google Drive API**
3. Create OAuth 2.0 Credentials (Desktop App type)
4. Download credentials as `client_secrets.json` and place in project root

### Environment Setup

Create `.env` file in project root:
```ini
GOOGLE_CLIENT_SECRETS_FILE=client_secrets.json
GOOGLE_CREDENTIALS_FILE=mycreds.txt
SOURCE_DIRECTORY="C:\Path\To\Your\Directory"

# Name of the folder in Google Drive where backups will be stored.
DRIVE_FOLDER_NAME="Backup"

# Development mode: True for minute-by-minute testing, False for scheduled backups:
DEVELOPMENT_MODE=True
```

## 📅 **Backup Schedule Configuration**
The default backup schedule is controlled by the `schedule_backup()` function in the code:

```python
def schedule_backup():
    """
    Schedule the backup process.
    - In DEVELOPMENT_MODE, backups run every minute (for testing).
    - In production, backups run on Wednesdays and Fridays at 15:45 hrs.
    """
    if DEVELOPMENT_MODE:
        schedule.every(1).minutes.do(perform_backup)  # Test mode
    else:
        schedule.every().wednesday.at("15:45").do(perform_backup)
        schedule.every().friday.at("15:45").do(perform_backup)
```

### How to Modify the Schedule:
1. **Change Days/Times**:  
   Edit the `schedule_backup()` function. Example:  
   ```python
   # For Mondays and Thursdays at 09:00
   schedule.every().monday.at("09:00").do(perform_backup)
   schedule.every().thursday.at("09:00").do(perform_backup)
   ```

2. **Adjust Frequency**:  
   Use `schedule.every(X).hours.do(perform_backup)` for hourly backups or other [schedule](https://schedule.readthedocs.io/) syntax.

3. **Development Mode**:  
   Set `DEVELOPMENT_MODE=True` in `.env` for minute-by-minute testing.

---

## Usage

```bash
#For windows
./env/Scripts/activate
python app.py

#For linux
source ./env/bin/activate
python app.py
```

- **First run**: Authenticate via OAuth2 in the browser.
- **Production mode**: Backups run on Wednesdays/Fridays at 15:45.
- **Test mode**: Set `DEVELOPMENT_MODE=True` for minute-by-minute backups.

**First Run Workflow:**
1. Authentication URL will appear in console
2. Follow URL and grant permissions
3. Paste authorization code into prompt
4. Credentials will be saved for future use

## System Workflow

1. **Scheduler Initialization**
   - Daily check at configured time (13:00 by default)
   - Respects 3-day interval between backups

2. **Backup Process**
   ```mermaid
   graph TD
     A[Start] --> B[Check Backup Interval]
     B -->|Due| C[Compress Directory]
     B -->|Not Due| D[Log Skip]
     C --> E[Upload to Google Drive]
     E --> F[Update Database]
     F --> G[Cleanup]
   ```

3. **File Management**
   - Creates ZIP archives with timestamped filenames
   - Stores backups in "Respaldos INDETEC" Drive folder
   - Maintains local SQLite database (`backups.db`)

## Monitoring & Maintenance

### Logs
- Located in `backup.log`
- Sample entry:
  ```
  2025-03-24 13:27:00,367 - INFO - Se cumplen las condiciones para realizar el respaldo.
  ```

### Database
Query backup history:
```sql
SELECT * FROM backups ORDER BY timestamp DESC;
```

| timestamp           | backup_name                 | status | message                                  |
|---------------------|-----------------------------|--------|------------------------------------------|
| 2025-03-24 13:27:00 | backup_Test_20250324_132700.zip | Éxito  | Backup comprimido correctamente...       |

## Troubleshooting

| Error Symptom                  | Likely Cause                 | Solution                                  |
|--------------------------------|------------------------------|-------------------------------------------|
| "Invalid client secrets file"  | Missing/misnamed credentials | Verify `client_secrets.json` exists       |
| "Error al comprimir"           | File in use/permissions      | Check directory accessibility            |
| Authentication failures        | Expired tokens               | Delete `mycreds.txt` and re-authenticate  |
| Upload timeouts                | Network issues               | Verify internet connection               |

## Contribution

Contributions welcome! Please:
1. Fork the repository
2. Create your feature branch
3. Submit a pull request
