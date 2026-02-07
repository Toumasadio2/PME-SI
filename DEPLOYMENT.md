# Guide de Déploiement PME-SI sur IONOS

Ce guide explique comment déployer PME-SI sur un VPS IONOS avec GitHub.

## Prérequis

- Compte IONOS avec VPS Linux (Ubuntu 22.04 recommandé)
- Compte GitHub
- Nom de domaine configuré chez IONOS

## Architecture

```
                    ┌─────────────────────────────────────────┐
                    │              VPS IONOS                   │
                    │                                          │
   Internet ──────► │  Nginx (80/443)                         │
                    │       │                                  │
                    │       ▼                                  │
                    │  ┌─────────┐   ┌──────────┐            │
                    │  │ Django  │◄──│ Postgres │            │
                    │  │ Gunicorn│   └──────────┘            │
                    │  └────┬────┘                            │
                    │       │        ┌──────────┐            │
                    │       └───────►│  Redis   │            │
                    │                └──────────┘            │
                    └─────────────────────────────────────────┘
```

## Étape 1 : Commande du VPS IONOS

1. Connectez-vous à [IONOS](https://www.ionos.fr/)
2. Commandez un **VPS Linux M** ou **L** :
   - OS : Ubuntu 22.04
   - Minimum : 2 vCPU, 4GB RAM, 80GB SSD
   - Recommandé : 4 vCPU, 8GB RAM, 160GB SSD

3. Notez l'adresse IP de votre serveur

## Étape 2 : Configuration DNS

Dans le panneau IONOS, configurez les enregistrements DNS :

| Type | Nom | Valeur |
|------|-----|--------|
| A | @ | IP_DU_VPS |
| A | www | IP_DU_VPS |
| A | pme-si | IP_DU_VPS |

## Étape 3 : Connexion au serveur

```bash
ssh root@IP_DU_VPS
```

## Étape 4 : Installation initiale

```bash
# Télécharger et exécuter le script d'installation
curl -sSL https://raw.githubusercontent.com/VOTRE_USER/pme-si/main/deploy/setup-server.sh | bash -s votredomaine.com
```

Ou manuellement :

```bash
# Mise à jour système
apt update && apt upgrade -y

# Installation Docker
curl -fsSL https://get.docker.com | bash
systemctl enable docker

# Installation Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Clone du projet
git clone https://github.com/VOTRE_USER/pme-si.git /opt/pme-si
cd /opt/pme-si
```

## Étape 5 : Configuration SSL (Let's Encrypt)

```bash
# Installation Certbot
apt install -y certbot

# Obtention du certificat (arrêtez nginx/docker d'abord si nécessaire)
certbot certonly --standalone -d pme-si.votredomaine.com -d www.pme-si.votredomaine.com

# Renouvellement automatique (déjà configuré par défaut)
systemctl enable certbot.timer
```

## Étape 6 : Configuration de l'application

```bash
cd /opt/pme-si

# Copier le fichier d'environnement
cp .env.production.example .env.production

# Éditer la configuration
nano .env.production
```

**Modifiez ces valeurs importantes :**

```env
# Générer une nouvelle clé secrète
SECRET_KEY=votre-nouvelle-cle-secrete

# Votre domaine
ALLOWED_HOSTS=pme-si.votredomaine.com,www.pme-si.votredomaine.com
CSRF_TRUSTED_ORIGINS=https://pme-si.votredomaine.com

# Mot de passe base de données (fort!)
POSTGRES_PASSWORD=MotDePasseTresSecurise123!

# Email IONOS
EMAIL_HOST=smtp.ionos.fr
EMAIL_HOST_USER=noreply@votredomaine.com
EMAIL_HOST_PASSWORD=motdepasse-email
```

## Étape 7 : Configuration Nginx

```bash
# Mettre à jour le domaine dans nginx.conf
sed -i 's|/etc/letsencrypt/live/domain|/etc/letsencrypt/live/pme-si.votredomaine.com|g' docker/nginx/nginx.conf
```

## Étape 8 : Lancement de l'application

```bash
# Construire et lancer
docker-compose -f docker-compose.prod.yml up -d --build

# Vérifier les logs
docker-compose -f docker-compose.prod.yml logs -f

# Créer le super admin
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

## Étape 9 : Configuration GitHub Actions (CI/CD)

### Secrets GitHub à configurer

Dans votre repo GitHub → Settings → Secrets and variables → Actions :

| Secret | Description |
|--------|-------------|
| `SERVER_HOST` | IP de votre VPS IONOS |
| `SERVER_USER` | `root` ou utilisateur SSH |
| `SERVER_SSH_KEY` | Clé privée SSH |

### Générer une clé SSH pour le déploiement

```bash
# Sur votre machine locale
ssh-keygen -t ed25519 -C "deploy@pme-si" -f ~/.ssh/pme-si-deploy

# Copier la clé publique sur le serveur
ssh-copy-id -i ~/.ssh/pme-si-deploy.pub root@IP_DU_VPS

# La clé privée (~/.ssh/pme-si-deploy) va dans le secret SERVER_SSH_KEY
```

## Commandes utiles

### Logs

```bash
# Tous les logs
docker-compose -f docker-compose.prod.yml logs -f

# Logs d'un service spécifique
docker-compose -f docker-compose.prod.yml logs -f web
docker-compose -f docker-compose.prod.yml logs -f nginx
```

### Redémarrage

```bash
# Redémarrer tous les services
docker-compose -f docker-compose.prod.yml restart

# Redémarrer un service
docker-compose -f docker-compose.prod.yml restart web
```

### Base de données

```bash
# Accès au shell PostgreSQL
docker-compose -f docker-compose.prod.yml exec db psql -U pme_si_user pme_si

# Backup manuel
docker-compose -f docker-compose.prod.yml exec db pg_dump -U pme_si_user pme_si > backup.sql

# Restauration
docker-compose -f docker-compose.prod.yml exec -T db psql -U pme_si_user pme_si < backup.sql
```

### Django

```bash
# Shell Django
docker-compose -f docker-compose.prod.yml exec web python manage.py shell

# Migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Créer un super admin
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

## Backups automatiques

Configurez le cron pour les backups quotidiens :

```bash
# Éditer le crontab
crontab -e

# Ajouter cette ligne (backup à 2h du matin)
0 2 * * * /opt/pme-si/deploy/backup.sh >> /var/log/pme-si/backup.log 2>&1
```

## Monitoring

### Vérification de l'état

```bash
# État des conteneurs
docker-compose -f docker-compose.prod.yml ps

# Utilisation des ressources
docker stats
```

### Health check

L'application expose un endpoint `/health/` qui retourne `{"status": "ok"}`.

## Mise à jour de l'application

### Déploiement manuel

```bash
cd /opt/pme-si
./deploy/deploy.sh
```

### Déploiement automatique (GitHub Actions)

Chaque push sur la branche `main` déclenche automatiquement :
1. Build de l'image Docker
2. Push vers le registry GitHub
3. Déploiement sur le serveur
4. Migration de la base de données
5. Collecte des fichiers statiques

## Troubleshooting

### L'application ne démarre pas

```bash
# Vérifier les logs
docker-compose -f docker-compose.prod.yml logs web

# Vérifier la configuration
docker-compose -f docker-compose.prod.yml config
```

### Erreur de certificat SSL

```bash
# Renouveler manuellement
certbot renew --force-renewal

# Redémarrer nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

### Base de données inaccessible

```bash
# Vérifier l'état de PostgreSQL
docker-compose -f docker-compose.prod.yml logs db

# Redémarrer la base de données
docker-compose -f docker-compose.prod.yml restart db
```

## Sécurité

- [x] Firewall UFW configuré (ports 22, 80, 443 uniquement)
- [x] Fail2ban installé
- [x] HTTPS forcé
- [x] Headers de sécurité configurés
- [x] Base de données non exposée publiquement
- [ ] Configurer les backups vers un stockage externe
- [ ] Configurer Sentry pour le monitoring des erreurs

## Support

Pour toute question, consultez la documentation ou ouvrez une issue sur GitHub.
