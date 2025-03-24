import os
import zipfile
import sqlite3
import logging
import schedule
import time
import datetime
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ===============================
# Global Constants and Environment Variables
# ===============================
# Define project constants, including the backup schedule details,
# database file name, and log file. Also, load Google Drive credentials settings.
BACKUP_INTERVAL_DAYS = 3
BACKUP_TIME = "13:00"
DB_FILE = "backups.db"
LOG_FILE = "backup.log"

# Environment variables for Google Drive credentials:
# GOOGLE_CLIENT_SECRETS_FILE contains the client_id and client_secret.
# GOOGLE_CREDENTIALS_FILE stores the access tokens.
# SOURCE_DIRECTORY is the path to the directory to backup.
# DRIVE_FOLDER_NAME is the name of the folder in Google Drive where backups will be stored. 
# TEST_BACKUP_TIME can override the default backup time for testing purposes.
GOOGLE_CLIENT_SECRETS_FILE = os.getenv("GOOGLE_CLIENT_SECRETS_FILE", "client_secrets.json")
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "mycreds.txt")
SOURCE_DIRECTORY = os.getenv("SOURCE_DIRECTORY")
DRIVE_FOLDER_NAME = os.getenv("DRIVE_FOLDER_NAME")
TEST_BACKUP_TIME = os.getenv("TEST_BACKUP_TIME")

# ===============================
# Logger Configuration
# ===============================
# Configure the logging module to output logs both to a file and the console.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# ===============================
# Database Functions
# ===============================
def init_db():
    """
    Initialize the SQLite database.
    This function creates the 'backups' table if it doesn't already exist. 
    The table stores backup entries with the timestamp, backup name, status, and message.
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                backup_name TEXT,
                status TEXT,
                message TEXT
            )
        ''')
        conn.commit()
        conn.close()
        logging.info("Base de datos inicializada correctamente.")
    except Exception as e:
        logging.error(f"Error al inicializar la base de datos: {e}")

def register_backup(backup_name, status, message):
    """
    Register a backup in the database.
    This function inserts a new record into the 'backups' table with the current timestamp,
    the backup's name, its status (Éxito/Fallo), and a descriptive message.
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            INSERT INTO backups (timestamp, backup_name, status, message)
            VALUES (?, ?, ?, ?)
        ''', (timestamp, backup_name, status, message))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Error al registrar el backup en la base de datos: {e}")

def get_last_successful_backup():
    """
    Retrieve the timestamp of the last successful backup.
    This function queries the 'backups' table for the most recent entry with status "Éxito"
    and returns its timestamp as a datetime object. If no backup exists, it returns None.
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT timestamp FROM backups WHERE status = "Éxito" ORDER BY id DESC LIMIT 1
        ''')
        result = cursor.fetchone()
        conn.close()
        if result:
            return datetime.datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S")
        else:
            return None
    except Exception as e:
        logging.error(f"Error al obtener el último backup: {e}")
        return None

# ===============================
# Directory Compression Function
# ===============================
def compress_directory(source, output_zip):
    """
    Compress the specified directory into a zip file.
    Parameters:
        source (str): The directory to be compressed.
        output_zip (str): The path and name of the output zip file.
    Returns:
        tuple: (True, message) if compression succeeds, or (False, error message) on failure.
    """
    try:
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source)
                    zipf.write(file_path, arcname)
        return True, "Backup comprimido correctamente."
    except Exception as e:
        return False, str(e)

# ===============================
# Google Drive Folder Handling Function
# ===============================
def get_or_create_folder(drive, folder_name=DRIVE_FOLDER_NAME):
    """
    Retrieve or create a folder in Google Drive.
    This function searches for a folder with the given name. If found, it returns the folder's ID.
    If not, it creates the folder and returns the new folder's ID.
    Parameters:
        drive (GoogleDrive): The authenticated Google Drive instance.
        folder_name (str): The name of the folder to search for or create.
    Returns:
        str: The Google Drive folder ID.
    """
    query = f"title='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    file_list = drive.ListFile({'q': query}).GetList()
    if file_list:
        return file_list[0]['id']
    else:
        folder_metadata = {
            'title': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = drive.CreateFile(folder_metadata)
        folder.Upload()
        return folder['id']

# ===============================
# Google Drive Upload Function
# ===============================
def upload_to_drive(file_path):
    """
    Authenticate and upload the given file to Google Drive.
    This function uses PyDrive to handle OAuth2 authentication. It attempts to load stored credentials,
    and if necessary, prompts for user authentication. The file is then uploaded to the folder specified by DRIVE_FOLDER_NAME.
    Parameters:
        file_path (str): The path to the file to be uploaded.
    Returns:
        tuple: (True, message) if the upload is successful, or (False, error message) on failure.
    """
    try:
        gauth = GoogleAuth()
        
        # Set the client configuration file for OAuth2
        gauth.settings['client_config_file'] = GOOGLE_CLIENT_SECRETS_FILE
        
        # Load stored credentials from file
        gauth.LoadCredentialsFile(GOOGLE_CREDENTIALS_FILE)
        if gauth.credentials is None:
            # No stored credentials: prompt the user for authentication via command-line
            gauth.CommandLineAuth()
        elif gauth.access_token_expired:
            # Credentials exist but token expired: refresh the token
            gauth.Refresh()
        else:
            # Credentials are valid: authorize directly
            gauth.Authorize()
        
        # Save the credentials for future use
        gauth.SaveCredentialsFile(GOOGLE_CREDENTIALS_FILE)

        drive = GoogleDrive(gauth)
        # Get or create the target folder in Google Drive
        folder_id = get_or_create_folder(drive, DRIVE_FOLDER_NAME)
        
        # Create the file in Drive and assign it to the specified folder
        drive_file = drive.CreateFile({
            'title': os.path.basename(file_path),
            'parents': [{'id': folder_id}]
        })
        drive_file.SetContentFile(file_path)
        drive_file.Upload()
        return True, "Backup subido a Google Drive correctamente."
    except Exception as e:
        return False, str(e)

# ===============================
# Backup Process Function
# ===============================
def perform_backup():
    """
    Execute the complete backup process.
    This function compresses the source directory, uploads the resulting zip file to Google Drive,
    deletes the local zip file if the upload is successful, and registers the outcome in the database.
    It logs each step's status.
    """
    try:
        current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = os.path.basename(os.path.normpath(SOURCE_DIRECTORY))
        backup_name = f"backup_{folder_name}_{current_time}.zip"
        output_path = os.path.join(os.getcwd(), backup_name)
        
        logging.info(f"Iniciando respaldo del directorio: {SOURCE_DIRECTORY}")
        success, message = compress_directory(SOURCE_DIRECTORY, output_path)
        if not success:
            logging.error(f"Error al comprimir: {message}")
            register_backup(backup_name, "Fallo", message)
            return
        
        upload_success, upload_message = upload_to_drive(output_path)
        if upload_success:
            logging.info(f"Respaldo completado y subido a Drive: {backup_name}")
            register_backup(backup_name, "Éxito", f"{message} | {upload_message}")
            # Delete the local compressed file to free up disk space
            try:
                os.remove(output_path)
                logging.info(f"Archivo local {backup_name} eliminado tras la subida exitosa.")
            except Exception as e:
                logging.error(f"Error al eliminar el archivo local: {e}")
        else:
            logging.error(f"Respaldo comprimido pero fallo la subida a Drive: {upload_message}")
            register_backup(backup_name, "Fallo", f"{message} | {upload_message}")
    except Exception as e:
        logging.error(f"Error en la función de respaldo: {e}")
        register_backup("N/A", "Fallo", str(e))

# ===============================
# Backup Scheduling Functions
# ===============================
def is_backup_due():
    """
    Determine whether a backup is due.
    This function checks the timestamp of the last successful backup and compares it with the current time.
    It returns True if no backup exists or if the elapsed days are equal to or exceed the defined interval.
    """
    last_backup = get_last_successful_backup()
    if last_backup is None:
        return True
    delta = datetime.datetime.now() - last_backup
    return delta.days >= BACKUP_INTERVAL_DAYS

def daily_task():
    """
    Execute the daily backup task.
    This function checks if the backup conditions are met (using is_backup_due) and triggers the backup process if they are.
    """
    logging.info("Verificando si es tiempo de realizar el respaldo...")
    if is_backup_due():
        logging.info("Se cumplen las condiciones para realizar el respaldo.")
        perform_backup()
    else:
        logging.info("No es momento de hacer un respaldo. Se esperan los 3 días de intervalo.")

def schedule_backup():
    """
    Schedule the daily backup process.
    This function sets up a daily scheduler using the 'schedule' module. It runs the daily_task() at the specified time,
    which can be overridden by the TEST_BACKUP_TIME environment variable.
    """
    schedule_time = TEST_BACKUP_TIME if TEST_BACKUP_TIME else BACKUP_TIME
    schedule.every().day.at(schedule_time).do(daily_task)
    logging.info(f"Programación de respaldos iniciada. Esperando ejecución diaria a las {schedule_time}.")
    while True:
        schedule.run_pending()
        time.sleep(1)

# ===============================
# Main Execution Block
# ===============================
if __name__ == "__main__":
    init_db()
    schedule_backup()
