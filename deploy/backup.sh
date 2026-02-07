#!/bin/bash
# =============================================================================
# PME-SI - Script de backup
# =============================================================================
# Usage: ./backup.sh
# Ajouter au cron: 0 2 * * * /opt/pme-si/deploy/backup.sh >> /var/log/pme-si/backup.log 2>&1

set -e

APP_DIR="/opt/pme-si"
BACKUP_DIR="/opt/pme-si/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

cd $APP_DIR

echo "=============================================="
echo "Backup PME-SI - $(date)"
echo "=============================================="

# Backup base de données
echo "[1/3] Backup de la base de données..."
docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U $POSTGRES_USER $POSTGRES_DB | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Backup des fichiers media
echo "[2/3] Backup des fichiers media..."
docker run --rm -v pme-si_media_volume:/data -v $BACKUP_DIR:/backup alpine tar czf /backup/media_$DATE.tar.gz -C /data .

# Suppression des vieux backups
echo "[3/3] Nettoyage des anciens backups..."
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "media_*.tar.gz" -mtime +$RETENTION_DAYS -delete

echo ""
echo "Backup terminé!"
echo "Fichiers créés:"
ls -lh $BACKUP_DIR/*_$DATE*
