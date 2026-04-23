# Quick Start - TraceManager Module

## Vue d'ensemble

Le module `TraceManager` gère la traçabilité complète des calculs des notes annexes SYSCOHADA. Il enregistre tous les montants calculés avec leurs comptes sources, permettant un audit complet.

## Utilisation de base

### 1. Créer un gestionnaire de traces

```python
from trace_manager import TraceManager

# Créer un gestionnaire pour la Note 3A
trace_mgr = TraceManager("3A")
```

### 2. Enregistrer les métadonnées

```python
trace_mgr.enregistrer_metadata(
    fichier_balance="P000 -BALANCE DEMO N_N-1_N-2.xlsx",
    titre_note="Immobilisations incorporelles"
)
```

### 3. Enregistrer les calculs

```python
# Définir les comptes sources
comptes_sources = [
    {
        "compte": "211",
        "intitule": "Frais de recherche et de développement",
        "valeur": 1500000.0,
        "type_valeur": "brut_ouverture"
    }
]

# Enregistrer le calcul
trace_mgr.enregistrer_calcul(
    libelle="Frais de recherche et de développement",
    montant=1500000.0,
    comptes_sources=comptes_sources
)
```

### 4. Ajouter les totaux

```python
trace_mgr.ajouter_total({
    "brut_ouverture": 5000000.0,
    "brut_cloture": 5500000.0,
    "vnc_ouverture": 4000000.0,
    "vnc_cloture": 4200000.0
})
```

### 5. Sauvegarder la trace

```python
# Sauvegarder en JSON
fichier_json = trace_mgr.sauvegarder_trace()
print(f"Trace JSON: {fichier_json}")

# Exporter en CSV pour Excel
fichier_csv = trace_mgr.exporter_csv()
print(f"Trace CSV: {fichier_csv}")
```

### 6. Gérer l'historique

```python
# Conserver uniquement les 10 dernières traces
trace_mgr.gerer_historique(max_historique=10)
```

## Exemple complet

```python
from trace_manager import TraceManager

# 1. Initialiser
trace_mgr = TraceManager("3A")

# 2. Métadonnées
trace_mgr.enregistrer_metadata(
    fichier_balance="balance.xlsx",
    titre_note="Immobilisations incorporelles"
)

# 3. Enregistrer plusieurs calculs
for ligne in lignes_calculees:
    comptes = [
        {
            "compte": ligne["compte_brut"],
            "intitule": ligne["intitule"],
            "valeur": ligne["brut_ouverture"],
            "type_valeur": "brut_ouverture"
        }
    ]
    trace_mgr.enregistrer_calcul(
        ligne["libelle"],
        ligne["brut_ouverture"],
        comptes
    )

# 4. Totaux
trace_mgr.ajouter_total(totaux)

# 5. Sauvegarder
trace_mgr.sauvegarder_trace()
trace_mgr.exporter_csv()

# 6. Nettoyer l'historique
trace_mgr.gerer_historique()
```

## Structure des fichiers générés

### Fichier JSON
```
py_backend/Doc calcul notes annexes/Traces/
└── trace_note_3A_20260423_130748.json
```

### Fichier CSV
```
py_backend/Doc calcul notes annexes/Traces/
└── trace_note_3A_20260423_130748.csv
```

## Format des données

### Comptes sources
Chaque compte source doit contenir:
- `compte`: Numéro du compte (ex: "211")
- `intitule`: Libellé du compte
- `valeur`: Montant extrait
- `type_valeur`: Type de valeur (brut_ouverture, dotations, etc.)

### Types de valeurs courants
- `brut_ouverture`: Valeur brute d'ouverture
- `brut_cloture`: Valeur brute de clôture
- `amort_ouverture`: Amortissements d'ouverture
- `amort_cloture`: Amortissements de clôture
- `dotations`: Dotations aux amortissements
- `reprises`: Reprises d'amortissements
- `augmentations`: Augmentations de l'exercice
- `diminutions`: Diminutions de l'exercice

## Intégration avec les calculateurs

```python
class CalculateurNote3A:
    def __init__(self, fichier_balance: str):
        self.fichier_balance = fichier_balance
        self.trace_mgr = TraceManager("3A")
    
    def calculer_note(self):
        # Enregistrer les métadonnées
        self.trace_mgr.enregistrer_metadata(
            self.fichier_balance,
            titre_note="Immobilisations incorporelles"
        )
        
        # Calculer chaque ligne
        for ligne in self.lignes:
            # ... calculs ...
            
            # Enregistrer la trace
            comptes_sources = self._extraire_comptes_sources(ligne)
            self.trace_mgr.enregistrer_calcul(
                ligne["libelle"],
                ligne["montant"],
                comptes_sources
            )
        
        # Sauvegarder
        self.trace_mgr.sauvegarder_trace()
        self.trace_mgr.exporter_csv()
        self.trace_mgr.gerer_historique()
```

## Avantages

✓ **Traçabilité complète**: Chaque montant est lié à ses comptes sources
✓ **Audit facilité**: Export CSV pour analyse dans Excel
✓ **Historique géré**: Conservation automatique des 10 dernières traces
✓ **Intégrité vérifiée**: Hash MD5 du fichier de balance
✓ **Horodatage**: Date et heure de chaque génération

## Validation des exigences

- ✓ Requirement 15.1: Enregistrement des calculs avec sources
- ✓ Requirement 15.2: Enregistrement des comptes sources et soldes
- ✓ Requirement 15.3: Enregistrement date/heure de génération
- ✓ Requirement 15.4: Enregistrement nom fichier et hash MD5
- ✓ Requirement 15.5: Détail des calculs accessible
- ✓ Requirement 15.6: Export CSV pour analyse Excel
- ✓ Requirement 15.7: Conservation des 10 dernières générations
