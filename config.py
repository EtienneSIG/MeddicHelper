# Configuration de l'application MEDDIC CRM

# Paramètres de la base de données
DATABASE_CONFIG = {
    "db_name": "meddic_data.db",
    "backup_enabled": True,
    "backup_frequency": "daily"
}

# Paramètres de l'interface
UI_CONFIG = {
    "theme": "light",
    "sidebar_expanded": True,
    "page_width": "wide"
}

# Statuts disponibles
MEDDIC_STATUS = [
    "En cours",
    "Qualifié", 
    "Non qualifié",
    "En attente",
    "Fermé - Gagné",
    "Fermé - Perdu"
]

# Couleurs pour les statuts
STATUS_COLORS = {
    "En cours": "#FFA500",      # Orange
    "Qualifié": "#32CD32",      # Vert lime
    "Non qualifié": "#FF6347",  # Rouge tomate
    "En attente": "#87CEEB",    # Bleu ciel
    "Fermé - Gagné": "#228B22", # Vert forêt
    "Fermé - Perdu": "#8B0000"  # Rouge foncé
}

# Champs obligatoires pour le score de complétude
REQUIRED_MEDDIC_FIELDS = [
    "metrics",
    "economic_buyer", 
    "decision_criteria",
    "decision_process",
    "identify_pain",
    "champion"
]

# Templates pour les champs MEDDIC
MEDDIC_TEMPLATES = {
    "metrics": {
        "placeholder": "Ex: Réduire les coûts de 20%, Augmenter la productivité de 30%, ROI de 150% en 18 mois...",
        "help": "Définissez des métriques quantifiables et mesurables"
    },
    "economic_buyer": {
        "placeholder": "Ex: Jean Dupont, Directeur Financier, jean.dupont@company.com, Décideur final budget >100k€",
        "help": "Identifiez la personne qui a le pouvoir de signer le budget"
    },
    "decision_criteria": {
        "placeholder": "Ex: Prix <100k€, Compatibilité avec SAP, Support 24/7, Références dans l'industrie...",
        "help": "Listez tous les critères qui influenceront la décision d'achat"
    },
    "decision_process": {
        "placeholder": "Ex: 1) Validation technique (IT), 2) Approbation budget (CFO), 3) Signature finale (CEO). Timeline: 8 semaines",
        "help": "Décrivez le processus complet de décision et les parties prenantes"
    },
    "identify_pain": {
        "placeholder": "Ex: Processus manuel chronophage (2h/jour), Erreurs fréquentes (15%), Manque de visibilité temps réel...",
        "help": "Identifiez les problèmes concrets et leur impact business"
    },
    "champion": {
        "placeholder": "Ex: Marie Martin, Responsable Opérations, Motivée par l'automatisation, Influence sur l'équipe IT",
        "help": "Identifiez votre allié interne et ses motivations"
    }
}

# Configuration d'export
EXPORT_CONFIG = {
    "pdf_enabled": True,
    "csv_enabled": True,
    "excel_enabled": True
}

# Paramètres de sécurité
SECURITY_CONFIG = {
    "backup_retention_days": 30,
    "auto_save_enabled": True,
    "audit_trail_enabled": True
}
