#!/usr/bin/env bash
# ==============================================================================
# SafeHer — Production Database Backup & Recovery Script
# PostgreSQL + PostGIS Backup & Restore Procedure
# ==============================================================================

set -e

BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/safeher_db_backup_${TIMESTAMP}.sql"

mkdir -p "${BACKUP_DIR}"

usage() {
    echo "Usage:"
    echo "  $0 backup            # Perform full PostgreSQL/PostGIS database dump"
    echo "  $0 restore <file>    # Restore database from SQL backup file"
    exit 1
}

backup_db() {
    echo "[SafeHer DB] Starting database backup to ${BACKUP_FILE}..."
    if [ -n "${DATABASE_URL}" ]; then
        pg_dump "${DATABASE_URL}" -F c -b -v -f "${BACKUP_FILE}.dump"
        echo "[SafeHer DB] Backup successful: ${BACKUP_FILE}.dump"
    else
        echo "[SafeHer DB] DATABASE_URL not exported. Backup skipped."
    fi
}

restore_db() {
    RESTORE_SRC="$1"
    if [ -z "${RESTORE_SRC}" ]; then
        echo "[SafeHer DB] Error: Backup file path required."
        usage
    fi

    echo "[SafeHer DB] Restoring database from ${RESTORE_SRC}..."
    if [ -n "${DATABASE_URL}" ]; then
        pg_restore --clean --no-acl --no-owner -d "${DATABASE_URL}" "${RESTORE_SRC}"
        echo "[SafeHer DB] Restoration complete."
    else
        echo "[SafeHer DB] DATABASE_URL not exported. Restore skipped."
    fi
}

case "$1" in
    backup)
        backup_db
        ;;
    restore)
        restore_db "$2"
        ;;
    *)
        usage
        ;;
esac
