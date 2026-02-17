# ABSERVICE - Systeme d'Information pour PME

ABSERVICE est une solution complete de gestion d'entreprise pour les petites et moyennes entreprises. Elle offre une architecture multi-tenant permettant a plusieurs organisations d'utiliser la meme instance de maniere isolee.

## Fonctionnalites

### CRM (Gestion de la Relation Client)
- Gestion des contacts et entreprises
- Pipeline de vente avec vue Kanban
- Suivi des opportunites commerciales
- Calendrier des activites

### Facturation
- Creation et gestion des devis
- Facturation avec generation PDF
- Suivi des paiements
- Catalogue de produits et services avec categories et tags
- Gestion de stock optionnelle

### Ressources Humaines
- Gestion des employes
- Suivi des conges et absences
- Calendrier RH
- Feuilles de temps

### Ventes
- Objectifs commerciaux
- Tableaux de bord analytiques
- Suivi des performances

## Installation

### Prerequis

- Python 3.9+
- PostgreSQL 13+ (recommande) ou SQLite
- Redis (optionnel, pour Celery)

### Installation en developpement

1. Cloner le repository
```bash
git clone https://github.com/votre-org/pme-si.git
cd pme-si
```

2. Creer un environnement virtuel
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# ou
venv\Scripts\activate  # Windows
```

3. Installer les dependances
```bash
pip install -r requirements/development.txt
```

4. Configurer l'environnement
```bash
cp .env.example .env
# Editer .env avec vos parametres
```

5. Appliquer les migrations
```bash
python manage.py migrate
```

6. Creer un super utilisateur
```bash
python manage.py createsuperuser
```

7. Lancer le serveur de developpement
```bash
python manage.py runserver
```

L'application est accessible a http://localhost:8000

### Installation en production

1. Installer les dependances de production
```bash
pip install -r requirements/production.txt
```

2. Configurer les variables d'environnement
```bash
export DJANGO_SETTINGS_MODULE=config.settings.production
# Configurer toutes les variables de .env.example
```

3. Collecter les fichiers statiques
```bash
python manage.py collectstatic --noinput
```

4. Appliquer les migrations
```bash
python manage.py migrate
```

5. Configurer un serveur WSGI (Gunicorn)
```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

## Structure du projet

```
pme-si/
├── apps/
│   ├── accounts/      # Gestion des utilisateurs
│   ├── core/          # Modeles de base et multi-tenant
│   ├── crm/           # Module CRM
│   ├── dashboard/     # Tableaux de bord
│   ├── hr/            # Module RH
│   ├── invoicing/     # Module Facturation
│   ├── notifications/ # Systeme de notifications
│   ├── permissions/   # Gestion des permissions
│   ├── sales/         # Module Ventes
│   └── search/        # Recherche globale
├── config/
│   ├── settings/
│   │   ├── base.py        # Parametres communs
│   │   ├── development.py # Parametres dev
│   │   └── production.py  # Parametres prod
│   ├── urls.py
│   └── wsgi.py
├── templates/         # Templates HTML
├── static/            # Fichiers statiques
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
└── tests/
```

## Architecture Multi-tenant

ABSERVICE utilise une architecture multi-tenant au niveau des donnees. Chaque organisation a ses propres donnees isolees des autres.

### Caracteristiques
- Un utilisateur peut appartenir a plusieurs organisations
- Roles par organisation : Proprietaire, Administrateur, Manager, Membre
- Super administrateur avec acces a toutes les organisations
- Basculement rapide entre organisations

### Migration vers le nouveau systeme
```bash
python manage.py migrate_to_memberships
```

## API et Integration

### Endpoints disponibles
- `/api/produits/<id>/` - Information produit (JSON)

### Webhooks (a venir)
- Evenements de facturation
- Mise a jour CRM

## Tests

Lancer les tests :
```bash
pytest
```

Avec couverture :
```bash
pytest --cov=apps --cov-report=html
```

## Configuration Docker

```bash
docker-compose up -d
```

## Contribution

1. Forker le projet
2. Creer une branche feature (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Commiter les changements (`git commit -m 'Ajout nouvelle fonctionnalite'`)
4. Pousser la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Ouvrir une Pull Request

## Licence

Ce projet est sous licence proprietaire. Tous droits reserves.

## Support

Pour toute question ou probleme, ouvrez une issue sur GitHub ou contactez support@exemple.com.
