# DOCUMENTATION TECHNIQUE COMPLÈTE
# ABSERVICE - Système d'Information Modulaire pour PME

---

**Auteur :** KAMARA TOUMANI
**Version :** 1.0
**Date :** Février 2026
**Site :** abservicecom.com
**Portfolio :** https://mon-portfolio-five-chi.vercel.app/

---

## TABLE DES MATIÈRES

1. [Présentation du Projet](#1-présentation-du-projet)
2. [Technologies et Logiciels Utilisés](#2-technologies-et-logiciels-utilisés)
3. [Architecture du Projet](#3-architecture-du-projet)
4. [Les 10 Applications Django](#4-les-10-applications-django)
5. [Modèles de Données Commentés](#5-modèles-de-données-commentés)
6. [Configuration et Déploiement](#6-configuration-et-déploiement)
7. [Templates et Interface](#7-templates-et-interface)
8. [Processus de Développement](#8-processus-de-développement)

---

# 1. PRÉSENTATION DU PROJET

## 1.1 Objectif

ABSERVICE est un **Système d'Information Modulaire** conçu pour les PME de 5 à 50 employés. Il centralise 4 fonctions essentielles :

| Module | Description |
|--------|-------------|
| **CRM** | Gestion des contacts, entreprises et opportunités commerciales |
| **Facturation** | Création de devis, factures conformes et génération PDF |
| **Ventes** | Suivi des performances commerciales et objectifs |
| **RH** | Gestion des employés, congés et temps de travail |

## 1.2 Problématique Résolue

Les PME utilisent généralement des outils dispersés coûtant 120-260€/mois :
- CRM (Pipedrive, HubSpot)
- Facturation (Sellsy, QuickBooks)
- RH (Factorial, PayFit)

ABSERVICE unifie ces fonctions dans une seule plateforme **100% Open Source**.

## 1.3 Architecture Multi-Tenant

Le système permet à plusieurs entreprises (tenants) d'utiliser la même instance tout en isolant complètement leurs données.

---

# 2. TECHNOLOGIES ET LOGICIELS UTILISÉS

## 2.1 Backend

| Technologie | Version | Rôle |
|-------------|---------|------|
| **Python** | 3.11+ | Langage de programmation principal |
| **Django** | 4.2+ | Framework web MVT (Model-View-Template) |
| **PostgreSQL** | 15+ | Base de données relationnelle |
| **Redis** | 5.0+ | Cache et broker de messages |
| **Celery** | 5.3+ | Tâches asynchrones (emails, relances) |

## 2.2 Frontend

| Technologie | Version | Rôle |
|-------------|---------|------|
| **HTMX** | 1.9+ | Interactivité AJAX sans JavaScript |
| **Tailwind CSS** | 3.x | Framework CSS utilitaire |
| **Alpine.js** | 3.x | JavaScript léger pour interactions |
| **Chart.js** | 4.x | Graphiques et visualisations |

## 2.3 DevOps et Déploiement

| Technologie | Rôle |
|-------------|------|
| **Docker** | Conteneurisation de l'application |
| **Docker Compose** | Orchestration des services |
| **Nginx** | Serveur web et reverse proxy |
| **Gunicorn** | Serveur WSGI Python |
| **Let's Encrypt** | Certificats SSL gratuits |
| **GitHub Actions** | CI/CD automatisé |

## 2.4 Bibliothèques Python Principales

```txt
# ===== FRAMEWORK DJANGO =====
Django>=4.2,<5.0          # Framework web principal

# ===== BASE DE DONNÉES =====
psycopg2-binary>=2.9      # Driver PostgreSQL pour Python

# ===== VARIABLES D'ENVIRONNEMENT =====
django-environ>=0.11      # Gestion des variables d'environnement
python-dotenv>=1.0        # Chargement du fichier .env
dj-database-url>=2.1      # URL de connexion à la base de données

# ===== GÉNÉRATION PDF =====
weasyprint>=60.0          # Conversion HTML vers PDF (factures, devis)
Pillow>=10.0              # Traitement d'images

# ===== TÂCHES ASYNCHRONES =====
celery>=5.3               # Gestionnaire de tâches en arrière-plan
redis>=5.0                # Base de données en mémoire (broker Celery)
django-celery-beat>=2.5   # Tâches planifiées (cron)
django-celery-results>=2.5 # Stockage des résultats Celery

# ===== FORMULAIRES =====
django-widget-tweaks>=1.5 # Personnalisation des widgets de formulaire
django-crispy-forms>=2.1  # Formulaires avec meilleur rendu
crispy-tailwind>=0.5      # Intégration Tailwind avec crispy-forms

# ===== AUTHENTIFICATION =====
django-allauth>=0.57      # Système d'authentification complet
pyotp>=2.9                # Authentification 2FA (TOTP)
qrcode>=7.4               # Génération de QR codes pour 2FA
argon2-cffi>=23.1         # Hachage sécurisé des mots de passe

# ===== API REST =====
djangorestframework>=3.14 # Framework API REST

# ===== SÉCURITÉ =====
django-cors-headers>=4.3  # Gestion des en-têtes CORS
bleach>=6.0               # Nettoyage HTML sécurisé

# ===== DÉVELOPPEMENT =====
django-debug-toolbar>=4.2 # Barre de débogage Django
django-extensions>=3.2    # Extensions utiles pour Django
```

---

# 3. ARCHITECTURE DU PROJET

## 3.1 Structure des Dossiers

```
pme-si/
├── apps/                      # Applications Django (10 apps)
│   ├── accounts/              # Gestion des utilisateurs
│   ├── core/                  # Noyau multi-tenant
│   ├── crm/                   # Module CRM
│   ├── invoicing/             # Module Facturation
│   ├── hr/                    # Module RH
│   ├── sales/                 # Module Ventes
│   ├── dashboard/             # Tableau de bord
│   ├── notifications/         # Système de notifications
│   ├── permissions/           # Gestion des permissions (RBAC)
│   └── search/                # Recherche globale
│
├── config/                    # Configuration Django
│   ├── settings/              # Paramètres par environnement
│   │   ├── base.py            # Configuration de base
│   │   ├── development.py     # Environnement développement
│   │   ├── production.py      # Environnement production
│   │   └── test.py            # Environnement test
│   ├── urls.py                # Routes URL principales
│   ├── wsgi.py                # Point d'entrée WSGI (production)
│   ├── asgi.py                # Point d'entrée ASGI (WebSockets)
│   └── celery.py              # Configuration Celery
│
├── templates/                 # Templates HTML (127+ fichiers)
│   ├── base.html              # Template de base
│   ├── layouts/               # Layouts principaux
│   ├── components/            # Composants réutilisables
│   ├── accounts/              # Templates authentification
│   ├── core/                  # Templates core
│   ├── crm/                   # Templates CRM
│   ├── invoicing/             # Templates facturation
│   ├── hr/                    # Templates RH
│   ├── sales/                 # Templates ventes
│   └── dashboard/             # Templates tableau de bord
│
├── static/                    # Fichiers statiques
│   ├── css/                   # Feuilles de style
│   ├── js/                    # Scripts JavaScript
│   └── images/                # Images
│
├── docker/                    # Configuration Docker
│   ├── Dockerfile             # Image production
│   ├── Dockerfile.dev         # Image développement
│   └── nginx/nginx.conf       # Configuration Nginx
│
├── deploy/                    # Scripts de déploiement
│   ├── deploy.sh              # Script de déploiement
│   ├── backup.sh              # Script de sauvegarde
│   └── setup-server.sh        # Configuration serveur
│
├── requirements/              # Dépendances Python
│   ├── base.txt               # Dépendances communes
│   ├── development.txt        # Dépendances développement
│   ├── production.txt         # Dépendances production
│   └── test.txt               # Dépendances test
│
├── docker-compose.yml         # Docker Compose local
├── docker-compose.prod.yml    # Docker Compose production
├── manage.py                  # Script de gestion Django
├── pyproject.toml             # Configuration du projet Python
└── Makefile                   # Commandes utiles
```

## 3.2 Diagramme d'Architecture

```
                    ┌─────────────────────────────────────────┐
                    │              VPS IONOS                   │
                    │                                          │
   Internet ──────► │  Nginx (80/443) - SSL Let's Encrypt     │
                    │       │                                  │
                    │       ▼                                  │
                    │  ┌─────────┐   ┌──────────┐            │
                    │  │ Django  │◄──│ Postgres │            │
                    │  │ Gunicorn│   │   15+    │            │
                    │  └────┬────┘   └──────────┘            │
                    │       │                                  │
                    │       ▼        ┌──────────┐            │
                    │  ┌─────────┐   │  Redis   │            │
                    │  │ Celery  │◄──│  5.0+    │            │
                    │  │ Workers │   └──────────┘            │
                    │  └─────────┘                            │
                    └─────────────────────────────────────────┘
```

---

# 4. LES 10 APPLICATIONS DJANGO

## 4.1 APP: core - Noyau Multi-Tenant

**Chemin :** `apps/core/`

**Fichiers principaux :**
- `models.py` (8.3 KB) - Modèles Organization, TenantModel
- `views.py` (17.8 KB) - Vues principales
- `middleware.py` (4.4 KB) - Middleware d'isolation des données
- `context_processors.py` (3.9 KB) - Variables de contexte globales

**Rôle :** Gère l'architecture multi-tenant permettant à plusieurs entreprises d'utiliser la même instance.

---

## 4.2 APP: accounts - Authentification

**Chemin :** `apps/accounts/`

**Fichiers principaux :**
- `models.py` - Modèle User personnalisé
- `views.py` - Vues de connexion/inscription
- `team_views.py` (15 KB) - Gestion des équipes
- `forms.py` (6.9 KB) - Formulaires d'authentification

**Fonctionnalités :**
- Connexion par email
- Inscription avec organisation
- Récupération de mot de passe
- Authentification 2FA (TOTP)
- Gestion des invitations

---

## 4.3 APP: crm - Gestion Relation Client

**Chemin :** `apps/crm/`

**Fichiers principaux :**
- `models.py` (15.8 KB) - Contact, Company, Opportunity, Activity
- `views.py` (32.8 KB) - Vues CRUD
- `forms.py` (19.3 KB) - Formulaires
- `urls.py` (3.6 KB) - Routes URL

**Fonctionnalités :**
- Gestion des contacts
- Gestion des entreprises
- Pipeline commercial (Kanban)
- Suivi des activités
- Calendrier

---

## 4.4 APP: invoicing - Facturation

**Chemin :** `apps/invoicing/`

**Fichiers principaux :**
- `models.py` (23.5 KB) - Quote, Invoice, Product, Payment
- `views.py` (39.2 KB) - Vues facturation
- `pdf.py` (28.1 KB) - Génération PDF
- `services.py` (6.9 KB) - Logique métier
- `emails.py` (7.1 KB) - Envoi d'emails

**Fonctionnalités :**
- Création de devis
- Génération de factures
- Catalogue produits
- Génération PDF
- Suivi des paiements
- Relances automatiques

---

## 4.5 APP: hr - Ressources Humaines

**Chemin :** `apps/hr/`

**Fichiers principaux :**
- `models.py` (22.9 KB) - Employee, Leave, TimeEntry
- `views.py` (34.4 KB) - Vues RH
- `forms.py` (20.8 KB) - Formulaires
- `services.py` (31.6 KB) - Logique métier

**Fonctionnalités :**
- Gestion des employés
- Gestion des départements
- Demandes de congés
- Workflow de validation
- Calendrier des absences
- Saisie du temps de travail

---

## 4.6 APP: sales - Ventes

**Chemin :** `apps/sales/`

**Fichiers principaux :**
- `models.py` (7.7 KB) - SalesTarget, Expense
- `views.py` (15 KB) - Dashboard ventes
- `services.py` (12.8 KB) - Calculs et analyses

**Fonctionnalités :**
- Dashboard des ventes
- Objectifs commerciaux
- Suivi des dépenses
- Graphiques et KPI

---

## 4.7 APP: dashboard - Tableau de Bord

**Chemin :** `apps/dashboard/`

**Fichiers principaux :**
- `views.py` (7.3 KB) - Vue principale du dashboard

**Fonctionnalités :**
- Vue consolidée des 4 modules
- Widgets personnalisables
- KPI en temps réel

---

## 4.8 APP: notifications - Notifications

**Chemin :** `apps/notifications/`

**Fichiers principaux :**
- `models.py` (3.9 KB) - Notification
- `services.py` (3.8 KB) - Création de notifications

**Fonctionnalités :**
- Centre de notifications
- Notifications en temps réel
- Historique

---

## 4.9 APP: permissions - Gestion des Droits

**Chemin :** `apps/permissions/`

**Fichiers principaux :**
- `models.py` (3.6 KB) - Role, Permission
- `decorators.py` (2.6 KB) - Décorateurs de permission
- `mixins.py` (1.9 KB) - Mixins pour les vues
- `services.py` (6.4 KB) - Vérification des permissions

**Rôles disponibles :**
- Owner (Propriétaire)
- Admin (Administrateur)
- Manager
- Member (Membre)

---

## 4.10 APP: search - Recherche Globale

**Chemin :** `apps/search/`

**Fichiers principaux :**
- `views.py` (3 KB) - Recherche full-text

**Fonctionnalités :**
- Recherche dans tous les modules
- Résultats catégorisés

---

# 5. MODÈLES DE DONNÉES COMMENTÉS

## 5.1 Modèle Organization (Core)

```python
class Organization(TimeStampedModel):
    """
    Représente une entreprise/tenant dans le système multi-tenant.
    Toutes les données métier sont isolées par organisation.
    """

    # ===== IDENTIFIANT UNIQUE =====
    id = models.UUIDField(
        primary_key=True,      # Clé primaire
        default=uuid.uuid4,    # UUID généré automatiquement
        editable=False         # Non modifiable
    )

    # ===== INFORMATIONS DE BASE =====
    name = models.CharField(max_length=255)           # Nom de l'entreprise
    slug = models.SlugField(max_length=100, unique=True)  # URL-friendly

    # ===== INFORMATIONS LÉGALES =====
    siret = models.CharField("SIRET", max_length=14, blank=True)
    vat_number = models.CharField("N° TVA", max_length=20, blank=True)
    rcs = models.CharField("RCS", max_length=100, blank=True)
    capital = models.CharField("Capital", max_length=50, blank=True)

    # ===== COORDONNÉES =====
    address = models.TextField("Adresse", blank=True)
    city = models.CharField("Ville", max_length=100, blank=True)
    postal_code = models.CharField("Code postal", max_length=10, blank=True)
    country = models.CharField("Pays", max_length=100, default="France")
    phone = models.CharField("Téléphone", max_length=20, blank=True)
    email = models.EmailField("Email", blank=True)
    website = models.URLField("Site web", blank=True)

    # ===== INFORMATIONS BANCAIRES (pour factures) =====
    bank_name = models.CharField("Banque", max_length=100, blank=True)
    iban = models.CharField("IBAN", max_length=34, blank=True)
    bic = models.CharField("BIC/SWIFT", max_length=11, blank=True)

    # ===== PERSONNALISATION VISUELLE =====
    logo = models.ImageField(upload_to="organizations/logos/", blank=True)
    primary_color = models.CharField(max_length=7, default="#3B82F6")
    secondary_color = models.CharField(max_length=7, default="#1E40AF")

    # ===== PARAMÈTRES =====
    timezone = models.CharField(max_length=50, default="Europe/Paris")
    currency = models.CharField(max_length=3, default="EUR")
    date_format = models.CharField(max_length=20, default="%d/%m/%Y")

    # ===== STATUT =====
    is_active = models.BooleanField(default=True)
    trial_ends_at = models.DateTimeField(null=True, blank=True)
```

---

## 5.2 Modèle User (Accounts)

```python
class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    """
    Modèle utilisateur personnalisé utilisant l'email comme identifiant.
    Hérite de AbstractBaseUser pour la gestion des mots de passe.
    """

    # ===== IDENTIFIANT =====
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, verbose_name="Adresse email")

    # ===== PROFIL =====
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True)
    job_title = models.CharField(max_length=100, blank=True)

    # ===== ORGANISATION ACTIVE =====
    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,   # Ne pas supprimer l'user si org supprimée
        null=True, blank=True,
        related_name="members"
    )
    active_organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="active_users"  # Organisation actuellement sélectionnée
    )

    # ===== PERMISSIONS =====
    is_super_admin = models.BooleanField(default=False)  # Accès à tout
    is_staff = models.BooleanField(default=False)        # Accès admin Django
    is_active = models.BooleanField(default=True)        # Compte actif
    is_organization_admin = models.BooleanField(default=False)

    # ===== AUTHENTIFICATION 2FA =====
    is_2fa_enabled = models.BooleanField(default=False)
    totp_secret = models.CharField(max_length=32, blank=True)  # Secret TOTP

    # ===== CONFIGURATION =====
    USERNAME_FIELD = "email"    # Utiliser l'email pour la connexion
    REQUIRED_FIELDS = []        # Aucun champ requis supplémentaire

    objects = UserManager()     # Gestionnaire personnalisé
```

---

## 5.3 Modèle Contact (CRM)

```python
class Contact(TenantModel):
    """
    Contact/Personne dans le CRM.
    Hérite de TenantModel pour l'isolation multi-tenant.
    """

    # ===== CHOIX PRÉDÉFINIS =====
    class Category(models.TextChoices):
        CLIENT = "CLIENT", "Client"
        PROSPECT = "PROSPECT", "Prospect"
        PARTNER = "PARTNER", "Partenaire"
        OTHER = "OTHER", "Autre"

    class Civility(models.TextChoices):
        MR = "MR", "M."
        MRS = "MRS", "Mme"
        MS = "MS", "Mlle"

    # ===== IDENTITÉ =====
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    civility = models.CharField(max_length=5, choices=Civility.choices, blank=True)
    first_name = models.CharField("Prénom", max_length=100)
    last_name = models.CharField("Nom", max_length=100)

    # ===== INFORMATIONS PROFESSIONNELLES =====
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,  # Garde le contact si entreprise supprimée
        null=True, blank=True,
        related_name="contacts"
    )
    job_title = models.CharField("Fonction", max_length=100, blank=True)
    department = models.CharField("Service", max_length=100, blank=True)

    # ===== COORDONNÉES =====
    email = models.EmailField("Email", blank=True)
    phone = models.CharField("Téléphone", max_length=20, blank=True)
    mobile = models.CharField("Mobile", max_length=20, blank=True)

    # ===== CATÉGORISATION =====
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.PROSPECT
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="contacts")

    # ===== ASSIGNATION =====
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="assigned_contacts"
    )

    # ===== PROPRIÉTÉ CALCULÉE =====
    @property
    def full_name(self) -> str:
        """Retourne le nom complet avec civilité."""
        parts = []
        if self.civility:
            parts.append(self.get_civility_display())
        parts.append(self.first_name)
        parts.append(self.last_name)
        return " ".join(parts)
```

---

## 5.4 Modèle Invoice (Facturation)

```python
class Invoice(models.Model):
    """
    Facture conforme à la législation française.
    """

    # ===== STATUTS POSSIBLES =====
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),      # En cours de rédaction
        ('sent', 'Envoyée'),         # Envoyée au client
        ('paid', 'Payée'),           # Entièrement payée
        ('partial', 'Partiellement payée'),
        ('overdue', 'En retard'),    # Date d'échéance dépassée
        ('cancelled', 'Annulée'),    # Annulée
    ]

    # ===== LIENS =====
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.PROTECT)  # Client
    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True)
    quote = models.ForeignKey(Quote, on_delete=models.SET_NULL, null=True)

    # ===== IDENTIFICATION =====
    number = models.CharField('Numéro', max_length=50)  # Ex: FAC-2026-0001
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # ===== CONTENU =====
    subject = models.CharField('Objet', max_length=200)
    introduction = models.TextField('Introduction', blank=True)
    conditions = models.TextField('Conditions de paiement', blank=True)
    legal_mentions = models.TextField('Mentions légales', blank=True)

    # ===== DATES =====
    issue_date = models.DateField('Date d\'émission', default=timezone.now)
    due_date = models.DateField('Date d\'échéance')
    payment_terms_days = models.PositiveIntegerField('Délai de paiement', default=30)

    # ===== MONTANTS =====
    total_ht = models.DecimalField('Total HT', max_digits=12, decimal_places=2)
    total_vat = models.DecimalField('Total TVA', max_digits=12, decimal_places=2)
    total_ttc = models.DecimalField('Total TTC', max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField('Montant payé', max_digits=12, decimal_places=2)

    # ===== RELANCES =====
    reminder_sent_at = models.DateTimeField('Dernière relance', null=True)
    reminder_count = models.PositiveIntegerField('Nombre de relances', default=0)

    # ===== SUPPRESSION LOGIQUE =====
    is_deleted = models.BooleanField('Supprimée', default=False)
    deleted_at = models.DateTimeField('Supprimée le', null=True)

    # ===== PROPRIÉTÉS CALCULÉES =====
    @property
    def balance_due(self):
        """Reste à payer."""
        return self.total_ttc - self.amount_paid

    @property
    def is_overdue(self):
        """Vérifie si la facture est en retard."""
        return (
            self.status not in ('paid', 'cancelled', 'draft') and
            self.due_date < timezone.now().date()
        )

    @property
    def days_overdue(self):
        """Nombre de jours de retard."""
        if not self.is_overdue:
            return 0
        return (timezone.now().date() - self.due_date).days
```

---

## 5.5 Modèle TenantMixin (Multi-tenant)

```python
class TenantMixin(models.Model):
    """
    Mixin abstrait pour les modèles isolés par organisation.
    Tous les modèles métier héritent de ce mixin.

    Exemple d'utilisation:
        class MonModele(TenantModel):
            # Ce modèle sera automatiquement lié à une organisation
            name = models.CharField(max_length=100)
    """

    # ===== LIEN VERS L'ORGANISATION =====
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,     # Supprime les données si org supprimée
        related_name="%(class)ss",    # Nom dynamique: organization.contacts
        db_index=True,                # Index pour les performances
    )

    class Meta:
        abstract = True  # Ce modèle n'a pas de table propre
```

---

# 6. CONFIGURATION ET DÉPLOIEMENT

## 6.1 Variables d'Environnement (.env)

```bash
# ===== DJANGO =====
SECRET_KEY=votre-cle-secrete-tres-longue-et-complexe
DEBUG=False
ALLOWED_HOSTS=abservicecom.com,www.abservicecom.com

# ===== BASE DE DONNÉES =====
DATABASE_URL=postgres://user:password@localhost:5432/abservice
POSTGRES_DB=abservice
POSTGRES_USER=abservice_user
POSTGRES_PASSWORD=mot_de_passe_fort

# ===== REDIS =====
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1

# ===== EMAIL =====
EMAIL_HOST=smtp.ionos.fr
EMAIL_PORT=587
EMAIL_HOST_USER=noreply@abservicecom.com
EMAIL_HOST_PASSWORD=mot_de_passe_email
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=ABSERVICE <noreply@abservicecom.com>

# ===== SÉCURITÉ =====
CSRF_TRUSTED_ORIGINS=https://abservicecom.com
SECURE_SSL_REDIRECT=True
```

## 6.2 Docker Compose Production

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  # ===== APPLICATION WEB =====
  web:
    build:
      context: .
      dockerfile: docker/Dockerfile
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    env_file:
      - .env.production
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started

  # ===== BASE DE DONNÉES =====
  db:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    env_file:
      - .env.production
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER}"]
      interval: 5s
      timeout: 5s
      retries: 5

  # ===== CACHE ET BROKER =====
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  # ===== TÂCHES ASYNCHRONES =====
  celery:
    build:
      context: .
      dockerfile: docker/Dockerfile
    command: celery -A config worker -l INFO
    env_file:
      - .env.production
    depends_on:
      - db
      - redis

  # ===== TÂCHES PLANIFIÉES =====
  celery-beat:
    build:
      context: .
      dockerfile: docker/Dockerfile
    command: celery -A config beat -l INFO
    env_file:
      - .env.production
    depends_on:
      - db
      - redis

  # ===== SERVEUR WEB =====
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./docker/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - static_volume:/app/staticfiles:ro
      - media_volume:/app/media:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
    depends_on:
      - web

volumes:
  postgres_data:
  redis_data:
  static_volume:
  media_volume:
```

## 6.3 Script de Déploiement

```bash
#!/bin/bash
# deploy/deploy.sh
# Script de déploiement automatique ABSERVICE

set -e  # Arrête en cas d'erreur

echo "=== DÉPLOIEMENT ABSERVICE ==="

# 1. Récupérer les dernières modifications
echo "1. Récupération du code..."
git pull origin main

# 2. Construire les images Docker
echo "2. Construction des images..."
docker-compose -f docker-compose.prod.yml build

# 3. Appliquer les migrations
echo "3. Migrations de base de données..."
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate --noinput

# 4. Collecter les fichiers statiques
echo "4. Collecte des fichiers statiques..."
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# 5. Redémarrer les services
echo "5. Redémarrage des services..."
docker-compose -f docker-compose.prod.yml up -d

echo "=== DÉPLOIEMENT TERMINÉ ==="
```

---

# 7. TEMPLATES ET INTERFACE

## 7.1 Structure des Templates

| Dossier | Nombre | Description |
|---------|--------|-------------|
| `layouts/` | 4 | Layouts principaux (app, public, auth) |
| `components/` | 6 | Composants réutilisables |
| `accounts/` | 15 | Templates authentification |
| `core/` | 5 | Templates core/accueil |
| `crm/` | 17 | Templates CRM |
| `invoicing/` | 25 | Templates facturation |
| `hr/` | 20 | Templates RH |
| `sales/` | 8 | Templates ventes |
| `dashboard/` | 7 | Templates tableau de bord |
| **Total** | **127+** | |

## 7.2 Layout Principal (app_layout.html)

```html
{% extends "base.html" %}

{% block body %}
<div class="min-h-screen bg-gray-50 flex flex-col">

    <!-- ===== EN-TÊTE DE NAVIGATION ===== -->
    <header class="bg-gradient-to-r from-slate-900 to-slate-800 shadow-lg">
        <div class="flex items-center justify-between h-16">
            <!-- Logo ABSERVICE -->
            <a href="{% url 'dashboard:index' %}">
                <span class="text-lg font-bold text-white">ABSERVICE</span>
            </a>

            <!-- Navigation principale -->
            <nav>
                <a href="{% url 'dashboard:index' %}">Accueil</a>
                <a href="{% url 'crm:dashboard' %}">CRM</a>
                <a href="{% url 'invoicing:dashboard' %}">Facturation</a>
                <a href="{% url 'hr:dashboard' %}">RH</a>
                <a href="{% url 'sales:dashboard' %}">Ventes</a>
            </nav>

            <!-- Menu utilisateur -->
            <div>
                <!-- Recherche, notifications, profil -->
            </div>
        </div>
    </header>

    <!-- ===== CONTENU PRINCIPAL ===== -->
    <main class="flex-1 py-6 px-4">
        {% block content %}{% endblock %}
    </main>

    <!-- ===== PIED DE PAGE ===== -->
    <footer class="bg-slate-800 border-t border-slate-700">
        <p class="text-center text-sm text-slate-400">
            &copy; {% now "Y" %} ABSERVICE. Tous droits réservés.
            Développé par <a href="https://mon-portfolio-five-chi.vercel.app/">KAMARA TOUMANI</a>
        </p>
    </footer>

</div>
{% endblock %}
```

## 7.3 Composants Réutilisables

### Composant Alert

```html
<!-- templates/components/alert.html -->
{% comment %}
Composant d'alerte réutilisable.
Usage: {% include "components/alert.html" with type="success" message="Opération réussie" %}
{% endcomment %}

<div class="rounded-md p-4
    {% if type == 'success' %}bg-green-50 text-green-800{% endif %}
    {% if type == 'error' %}bg-red-50 text-red-800{% endif %}
    {% if type == 'warning' %}bg-yellow-50 text-yellow-800{% endif %}
    {% if type == 'info' %}bg-blue-50 text-blue-800{% endif %}">
    <div class="flex">
        <div class="flex-shrink-0">
            <!-- Icône selon le type -->
        </div>
        <div class="ml-3">
            <p class="text-sm font-medium">{{ message }}</p>
        </div>
    </div>
</div>
```

### Composant Pagination

```html
<!-- templates/components/pagination.html -->
{% comment %}
Composant de pagination.
Usage: {% include "components/pagination.html" with page_obj=contacts %}
{% endcomment %}

<nav class="flex items-center justify-between">
    <div>
        <p class="text-sm text-gray-700">
            Affichage de
            <span class="font-medium">{{ page_obj.start_index }}</span>
            à
            <span class="font-medium">{{ page_obj.end_index }}</span>
            sur
            <span class="font-medium">{{ page_obj.paginator.count }}</span>
            résultats
        </p>
    </div>
    <div class="flex space-x-2">
        {% if page_obj.has_previous %}
            <a href="?page={{ page_obj.previous_page_number }}"
               class="px-3 py-2 bg-white border rounded-md">
                Précédent
            </a>
        {% endif %}
        {% if page_obj.has_next %}
            <a href="?page={{ page_obj.next_page_number }}"
               class="px-3 py-2 bg-white border rounded-md">
                Suivant
            </a>
        {% endif %}
    </div>
</nav>
```

---

# 8. PROCESSUS DE DÉVELOPPEMENT

## 8.1 Phases du Projet

| Phase | Durée | Contenu |
|-------|-------|---------|
| **Phase 1** | 2-3 mois | Fondations : Auth, Multi-tenant, Dashboard |
| **Phase 2** | 1.5-2 mois | Module CRM complet |
| **Phase 3** | 2-2.5 mois | Module Facturation + PDF |
| **Phase 4** | 1.5-2 mois | Module Ventes + Analyses |
| **Phase 5** | 1.5-2 mois | Module RH complet |
| **Phase 6** | 1 mois | Production, Documentation |

## 8.2 Commandes Utiles (Makefile)

```makefile
# ===== DÉVELOPPEMENT =====
run:           # Lancer le serveur de développement
	python manage.py runserver

migrate:       # Appliquer les migrations
	python manage.py migrate

makemigrations: # Créer les fichiers de migration
	python manage.py makemigrations

shell:         # Ouvrir le shell Django
	python manage.py shell_plus

# ===== TESTS =====
test:          # Lancer tous les tests
	pytest

test-cov:      # Tests avec couverture
	pytest --cov=apps --cov-report=html

# ===== QUALITÉ DU CODE =====
lint:          # Vérifier le code
	ruff check apps

format:        # Formater le code
	ruff format apps

# ===== DOCKER =====
docker-up:     # Lancer en développement
	docker-compose up -d

docker-prod:   # Lancer en production
	docker-compose -f docker-compose.prod.yml up -d --build

docker-logs:   # Voir les logs
	docker-compose logs -f

# ===== BASE DE DONNÉES =====
backup:        # Sauvegarder la base
	./deploy/backup.sh

restore:       # Restaurer la base
	docker-compose exec db psql -U abservice_user abservice < backup.sql
```

## 8.3 Workflow Git

```bash
# 1. Créer une branche pour la fonctionnalité
git checkout -b feature/nom-fonctionnalite

# 2. Développer et commiter
git add .
git commit -m "Ajout de la fonctionnalité X"

# 3. Pousser vers GitHub
git push origin feature/nom-fonctionnalite

# 4. Créer une Pull Request sur GitHub

# 5. Après validation, merger dans main
git checkout main
git merge feature/nom-fonctionnalite
git push origin main

# 6. Le déploiement automatique se déclenche via GitHub Actions
```

---

# CONCLUSION

## Récapitulatif du Projet

**ABSERVICE** est une solution complète de gestion pour PME comprenant :

- **10 applications Django** interconnectées
- **127+ templates HTML** avec Tailwind CSS
- **Architecture multi-tenant** sécurisée
- **4 modules métier** (CRM, Facturation, Ventes, RH)
- **Déploiement Docker** automatisé

## Technologies Maîtrisées

- Python 3.11 / Django 4.2
- PostgreSQL / Redis
- Docker / Docker Compose
- HTMX / Alpine.js / Tailwind CSS
- CI/CD avec GitHub Actions

## Liens Utiles

- **Site :** https://abservicecom.com
- **GitHub :** https://github.com/Toumasadio2/PME-SI
- **Portfolio :** https://mon-portfolio-five-chi.vercel.app/

---

**Document rédigé par KAMARA TOUMANI**
**Février 2026**
