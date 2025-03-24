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
GOOGLE_CLIENT_SECRETS_FILE="client_secrets.json"
GOOGLE_CREDENTIALS_FILE="mycreds.txt"
# Name of the folder in Google Drive where backups will be stored.
DRIVE_FOLDER_NAME="Backup"
# Optional test override:
TEST_BACKUP_TIME="14:30"
```

### Directory Configuration
Modify `SOURCE_DIRECTORY` in `app.py` to your target backup path:
```python
SOURCE_DIRECTORY = r"C:\Path\To\Your\Directory"
```

## Usage

```bash
python app.py
```

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