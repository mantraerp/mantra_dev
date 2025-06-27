#!/bin/bash

# Timestamp (no colons so Windows/SMB allows the name)
DATE=$(date '+%F_%H-%M-%S')

# Paths
SOURCE_FOLDER="/home/mocula/"
SOURCE_ZIP="/home/mantra/backup/mocula_backup_$DATE.zip"
LOG_FILE="/home/mantra/backup/backup_mocula.log"

# SMB credentials
SMB_USER="Abhishek_Jain"
SMB_PASS="Mantra@62923"
SMB_HOST="192.168.1.4"
SMB_SHARE="ERP_Backup"

echo "[$(date)] Starting backup of mocula $SOURCE_FOLDER" >> "$LOG_FILE"

# 1) Zip up the source
echo "[$(date)] Creating zip archive..." >> "$LOG_FILE"
cd "$SOURCE_FOLDER" || exit 1
zip -r "$SOURCE_ZIP" . >> /dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "[$(date)] Failed to create zip." >> "$LOG_FILE"
  # exit 1
else
  echo "[$(date)] Zip created: $SOURCE_ZIP" >> "$LOG_FILE"
fi

# 2) Upload via smbclient
echo "[$(date)] Uploading via smbclient to //$SMB_HOST/$SMB_SHARE" >> "$LOG_FILE"
smbclient "//$SMB_HOST/$SMB_SHARE" \
  -U "$SMB_USER%$SMB_PASS" \
  -c "lcd $(dirname "$SOURCE_ZIP"); \
      put $(basename "$SOURCE_ZIP")" \
  >> "$LOG_FILE" 2>&1

if [ $? -ne 0 ]; then
  echo "[$(date)] SMB upload failed." >> "$LOG_FILE"
  # exit 1
else
  echo "[$(date)] SMB upload succeeded." >> "$LOG_FILE"
fi

# 3) Delete all zip files except the current one
echo "[$(date)] Deleting old zip files from /home/mantra/backup..." >> "$LOG_FILE"
find /home/mantra/backup/ -name 'mocula_backup_*.zip' -type f ! -name "$(basename "$SOURCE_ZIP")" -exec rm -f {} \;

if [ $? -ne 0 ]; then
  echo "[$(date)] Failed to delete old backups." >> "$LOG_FILE"
else
  echo "[$(date)] Old backups deleted successfully." >> "$LOG_FILE"
fi

echo "[$(date)] Backup job completed successfully." >> "$LOG_FILE"