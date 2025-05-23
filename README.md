# 🎯 MEDDIC CRM - Application Streamlit

Une application web interactive pour préparer, suivre et analyser les rendez-vous clients selon la méthodologie MEDDIC.

## 📋 Qu'est-ce que MEDDIC ?

MEDDIC est une méthodologie de qualification des opportunités commerciales qui se base sur 6 critères essentiels :

- **M - Metrics** : Métriques quantifiables que le client souhaite améliorer
- **E - Economic Buyer** : Personne ayant le pouvoir de décision budgétaire  
- **D - Decision Criteria** : Critères de décision principaux du client
- **D - Decision Process** : Processus de décision et parties prenantes impliquées
- **I - Identify Pain** : Douleurs et problèmes identifiés chez le client
- **C - Champion** : Allié interne qui soutient votre solution

## 🚀 Fonctionnalités

### 📊 Dashboard
- Vue synthétique de toutes les opportunités
- Métriques clés (taux de qualification, complétude moyenne)
- Graphiques de répartition par statut
- Recherche rapide par entreprise ou client

### ✏️ Gestion des Fiches MEDDIC
- Formulaire complet pour saisir tous les éléments MEDDIC
- Auto-sauvegarde en base SQLite
- Calcul automatique du score de complétude
- Validation des données saisies
- Édition et suppression des fiches existantes

### 📋 Vue d'ensemble
- Liste de toutes les fiches avec filtres avancés
- Filtrage par statut, entreprise, commercial
- Export PDF individuel de chaque fiche
- Affichage du score de complétude

### 📈 Analytiques
- Statistiques globales et KPIs
- Distribution des scores de complétude
- Performance par commercial
- Évolution temporelle des créations
- Top des entreprises

## 🔧 Installation

### Prérequis
- Python 3.10 ou supérieur
- pip (gestionnaire de packages Python)

### Installation des dépendances

```bash
pip install -r requirements.txt
```

### Lancement de l'application

```bash
streamlit run app.py
```

L'application sera accessible à l'adresse : `http://localhost:8501`

## 📁 Structure du Projet

```
19_MEDDIC/
├── app.py              # Application principale Streamlit
├── config.py           # Configuration et constantes
├── utils.py            # Fonctions utilitaires
├── requirements.txt    # Dépendances Python
├── README.md          # Documentation
└── meddic_data.db     # Base de données SQLite (créée automatiquement)
```

## 💾 Stockage des Données

L'application utilise SQLite pour stocker les données :
- **Base de données** : `meddic_data.db` (créée automatiquement au premier lancement)
- **Sauvegarde automatique** : Les données sont sauvegardées en temps réel
- **Structure** : Table `meddic_fiches` avec tous les champs MEDDIC

## 🎨 Interface Utilisateur

### Navigation
L'application utilise une sidebar pour la navigation entre les différentes sections :
- 📊 Dashboard
- ✏️ Nouvelle Fiche  
- 📋 Toutes les Fiches
- 📈 Analytiques

### Formulaire MEDDIC
Le formulaire principal permet de saisir :
- **Informations générales** : Client, entreprise, date RDV, commercial
- **Les 6 critères MEDDIC** avec des zones de texte dédiées
- **Statut** : En cours, Qualifié, Non qualifié, En attente, etc.
- **Notes additionnelles** : Observations libres

### Score de Complétude
- Calcul automatique basé sur les 6 champs MEDDIC obligatoires
- Affichage en pourcentage avec code couleur
- Recommandations pour améliorer la qualification

## 📊 Métriques et KPIs

L'application calcule automatiquement :
- **Score de complétude** : Pourcentage de champs MEDDIC remplis
- **Taux de qualification** : Pourcentage d'opportunités qualifiées
- **Répartition par statut** : Distribution des différents statuts
- **Performance par commercial** : Statistiques individuelles
- **Évolution temporelle** : Suivi dans le temps

## 📄 Export et Rapports

### Export PDF
- Génération automatique de fiches PDF
- Format professionnel avec toutes les informations MEDDIC
- Téléchargement direct depuis l'interface

### Export CSV
- Export de toutes les données au format CSV
- Compatible avec Excel et autres outils d'analyse

## 🔒 Sécurité

- **Stockage local** : Toutes les données restent sur votre machine
- **Base SQLite** : Format de fichier standard et sécurisé  
- **Pas de transmission** : Aucune donnée n'est envoyée vers des serveurs externes
- **Sauvegarde** : Possibilité de sauvegarder la base de données

## 🛠️ Personnalisation

### Configuration
Le fichier `config.py` permet de personnaliser :
- Les statuts disponibles et leurs couleurs
- Les champs obligatoires pour le score de complétude
- Les templates et textes d'aide
- Les paramètres d'export

### Ajout de Fonctionnalités
L'architecture modulaire permet d'ajouter facilement :
- Nouveaux types de rapports
- Intégrations avec d'autres outils CRM
- Notifications et alertes
- Workflows automatisés

## 🚨 Dépannage

### Problèmes Courants

**L'application ne démarre pas**
- Vérifiez que toutes les dépendances sont installées : `pip install -r requirements.txt`
- Vérifiez la version de Python : `python --version`

**Erreur de base de données**
- La base SQLite sera créée automatiquement au premier lancement
- Vérifiez les permissions d'écriture dans le dossier

**Performance lente**
- L'application est optimisée pour quelques centaines de fiches
- Pour de gros volumes, considérez une base PostgreSQL

### Logs et Debug
- Les erreurs sont affichées directement dans l'interface Streamlit
- Pour plus de détails, lancez avec : `streamlit run app.py --logger.level=debug`

## 🔮 Évolutions Futures

### Fonctionnalités Prévues
- [ ] Intégration calendrier (Outlook, Google Calendar)
- [ ] Notifications par email
- [ ] Workflow de validation
- [ ] Dashboard temps réel
- [ ] API REST pour intégrations
- [ ] Mobile responsive design
- [ ] Import depuis CRM existants

### Intégrations Possibles
- **CRM** : Salesforce, HubSpot, Pipedrive
- **Calendrier** : Outlook, Google Calendar
- **Communication** : Slack, Teams, Email
- **Reporting** : Power BI, Tableau

## 👥 Contribution

Cette application est conçue pour être facilement extensible. Les contributions sont les bienvenues pour :
- Nouvelles fonctionnalités
- Corrections de bugs
- Améliorations de l'interface
- Documentation

## 📄 Licence

Application développée pour un usage interne. Libre d'utilisation et de modification selon vos besoins.

## 📞 Support

Pour toute question ou suggestion :
- Consultez cette documentation
- Vérifiez les logs d'erreur dans l'interface
- Testez avec des données d'exemple

---

🎯 **MEDDIC CRM** - Qualifiez mieux, vendez plus !
