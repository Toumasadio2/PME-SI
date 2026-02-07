#!/bin/bash
# =============================================================================
# PME-SI - Script d'installation initiale sur VPS IONOS
# =============================================================================
# Usage: curl -sSL https://raw.githubusercontent.com/VOTRE_USER/pme-si/main/deploy/setup-server.sh | bash
# Ou: bash setup-server.sh votredomaine.com

set -e

DOMAIN=${1:-"example.com"}
APP_DIR="/opt/pme-si"
GITHUB_REPO="VOTRE_USER/pme-si"  # À modifier

echo "=============================================="
echo "Installation PME-SI sur VPS IONOS"
echo "Domaine: $DOMAIN"
echo "=============================================="

# Mise à jour système
echo "[1/8] Mise à jour du système..."
apt-get update && apt-get upgrade -y

# Installation des dépendances
echo "[2/8] Installation des dépendances..."
apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    ufw \
    fail2ban \
    certbot

# Installation Docker
echo "[3/8] Installation de Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | bash
    systemctl enable docker
    systemctl start docker
fi

# Installation Docker Compose
echo "[4/8] Installation de Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Configuration du firewall
echo "[5/8] Configuration du firewall..."
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow http
ufw allow https
ufw --force enable

# Configuration Fail2ban
echo "[6/8] Configuration de Fail2ban..."
systemctl enable fail2ban
systemctl start fail2ban

# Création des répertoires
echo "[7/8] Création des répertoires..."
mkdir -p $APP_DIR
mkdir -p $APP_DIR/backups
mkdir -p /var/log/pme-si

# Clone du repository
echo "[8/8] Clone du repository..."
if [ -d "$APP_DIR/.git" ]; then
    cd $APP_DIR && git pull origin main
else
    git clone https://github.com/$GITHUB_REPO.git $APP_DIR
fi

cd $APP_DIR

# Création du fichier .env.production
if [ ! -f ".env.production" ]; then
    echo ""
    echo "=============================================="
    echo "IMPORTANT: Configuration requise"
    echo "=============================================="
    echo ""
    echo "1. Copiez le fichier d'exemple:"
    echo "   cp .env.production.example .env.production"
    echo ""
    echo "2. Modifiez les valeurs dans .env.production:"
    echo "   nano .env.production"
    echo ""
    echo "3. Obtenez un certificat SSL:"
    echo "   certbot certonly --standalone -d $DOMAIN"
    echo ""
    echo "4. Mettez à jour nginx.conf avec votre domaine:"
    echo "   sed -i 's/domain/$DOMAIN/g' docker/nginx/nginx.conf"
    echo ""
    echo "5. Lancez l'application:"
    echo "   docker-compose -f docker-compose.prod.yml up -d"
    echo ""
    echo "=============================================="
fi

echo ""
echo "Installation terminée!"
echo "Suivez les instructions ci-dessus pour finaliser la configuration."
