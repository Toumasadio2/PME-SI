#!/bin/bash
# =============================================================================
# ABSERVICE - Script de déploiement
# =============================================================================
# Usage: ./deploy.sh

set -e

APP_DIR="/opt/pme-si"
BACKUP_DIR="/opt/pme-si/backups"
DATE=$(date +%Y%m%d_%H%M%S)

cd $APP_DIR

echo "=============================================="
echo "Déploiement ABSERVICE - $(date)"
echo "=============================================="

# Backup de la base de données avant déploiement
echo "[1/6] Backup de la base de données..."
docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U $POSTGRES_USER $POSTGRES_DB > $BACKUP_DIR/db_$DATE.sql 2>/dev/null || true

# Pull des dernières modifications
echo "[2/6] Récupération des modifications..."
git fetch origin main
git reset --hard origin/main

# Pull des nouvelles images
echo "[3/6] Téléchargement des images..."
docker-compose -f docker-compose.prod.yml pull

# Redémarrage des services
echo "[4/6] Redémarrage des services..."
docker-compose -f docker-compose.prod.yml up -d --remove-orphans

# Attente que les services soient prêts
echo "[5/6] Attente des services..."
sleep 10

# Migrations et collectstatic
echo "[6/6] Migrations et fichiers statiques..."
docker-compose -f docker-compose.prod.yml exec -T web python manage.py migrate --noinput
docker-compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput

# Nettoyage
docker system prune -f

echo ""
echo "=============================================="
echo "Déploiement terminé avec succès!"
echo "=============================================="

# Vérification du statut
docker-compose -f docker-compose.prod.yml ps
