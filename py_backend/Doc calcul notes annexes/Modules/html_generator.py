"""
Module HTML_Generator - Génération des fichiers HTML de visualisation

Ce module fournit la classe HTMLGenerator pour générer des fichiers HTML
formatés conformes au format SYSCOHADA officiel pour les notes annexes.

Author: Claraverse
Date: 2026-04-22
"""

import pandas as pd
from typing import Dict, List, Optional


class HTMLGenerator:
    """
    Générateur de fichiers HTML pour les notes annexes SYSCOHADA.
    
    Cette classe génère des tableaux HTML formatés avec:
    - En-têtes groupés et sous-colonnes
    - Formatage des montants avec séparateurs de milliers
    - Style CSS conforme au format SYSCOHADA
    - Ligne de total avec style distinct
    - Tableau responsive adapté à différentes tailles d'écran
    
    Attributes:
        titre_note (str): Titre de la note annexe
        numero_note (str): Numéro de la note (ex: "3A", "3B")
    """
    
    def __init__(self, titre_note: str, numero_note: str):
        """
        Initialise le générateur HTML.
        
        Args:
            titre_note: Titre de la note annexe (ex: "Immobilisations Incorporelles")
            numero_note: Numéro de la note (ex: "3A", "3B", "01")
        """
        self.titre_note = titre_note
        self.numero_note = numero_note
    
    def generer_html(self, df: pd.DataFrame, colonnes_config: Dict) -> str:
        """
        Génère le HTML complet d'une note annexe.
        
        Args:
            df: DataFrame contenant les données de la note
            colonnes_config: Configuration des colonnes avec structure:
                {
                    'groupes': [
                        {
                            'titre': 'VALEURS BRUTES',
                            'colonnes': ['brut_ouverture', 'augmentations', 'diminutions', 'brut_cloture']
                        },
                        ...
                    ],
                    'labels': {
                        'brut_ouverture': 'Ouverture',
                        'augmentations': 'Augmentations',
                        ...
                    }
                }
        
        Returns:
            Code HTML complet de la note
        """
        html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NOTE {self.numero_note} - {self.titre_note}</title>
    {self.appliquer_style_css()}
</head>
<body>
    <div class="container">
        <h1>NOTE {self.numero_note}</h1>
        <h2>{self.titre_note}</h2>
        <table>
            {self.generer_entetes(colonnes_config)}
            {self.generer_lignes(df, colonnes_config)}
        </table>
        <div class="footer">
            <p>Document généré automatiquement - Système SYSCOHADA Révisé</p>
        </div>
    </div>
</body>
</html>"""
        return html
    
    def generer_entetes(self, colonnes_config: Dict) -> str:
        """
        Génère les en-têtes du tableau avec groupes et sous-colonnes.
        
        Args:
            colonnes_config: Configuration des colonnes avec groupes et labels
        
        Returns:
            HTML des en-têtes (thead)
        """
        html = "<thead>\n"
        
        # Première ligne: groupes de colonnes
        html += "    <tr class='header-group'>\n"
        html += "        <th rowspan='2' class='libelle-col'>LIBELLÉ</th>\n"
        
        for groupe in colonnes_config.get('groupes', []):
            nb_colonnes = len(groupe.get('colonnes', []))
            html += f"        <th colspan='{nb_colonnes}' class='group-header'>{groupe['titre']}</th>\n"
        
        html += "    </tr>\n"
        
        # Deuxième ligne: sous-colonnes
        html += "    <tr class='header-subgroup'>\n"
        
        labels = colonnes_config.get('labels', {})
        for groupe in colonnes_config.get('groupes', []):
            for colonne in groupe.get('colonnes', []):
                label = labels.get(colonne, colonne)
                html += f"        <th class='subgroup-header'>{label}</th>\n"
        
        html += "    </tr>\n"
        html += "</thead>\n"
        
        return html
    
    def generer_lignes(self, df: pd.DataFrame, colonnes_config: Dict) -> str:
        """
        Génère les lignes du tableau avec formatage des montants.
        
        Args:
            df: DataFrame avec les données
            colonnes_config: Configuration des colonnes
        
        Returns:
            HTML des lignes (tbody)
        """
        html = "<tbody>\n"
        
        # Extraire l'ordre des colonnes depuis la config
        colonnes_ordre = []
        for groupe in colonnes_config.get('groupes', []):
            colonnes_ordre.extend(groupe.get('colonnes', []))
        
        # Générer les lignes de données
        for idx, row in df.iterrows():
            # Déterminer si c'est la ligne de total
            is_total = 'TOTAL' in str(row.get('libelle', '')).upper()
            row_class = 'total-row' if is_total else ('even-row' if idx % 2 == 0 else 'odd-row')
            
            html += f"    <tr class='{row_class}'>\n"
            
            # Colonne libellé
            libelle = row.get('libelle', '')
            html += f"        <td class='libelle-cell'>{libelle}</td>\n"
            
            # Colonnes de montants
            for colonne in colonnes_ordre:
                montant = row.get(colonne, 0.0)
                montant_formate = self.formater_montant(montant)
                html += f"        <td class='montant-cell'>{montant_formate}</td>\n"
            
            html += "    </tr>\n"
        
        html += "</tbody>\n"
        
        return html
    
    def formater_montant(self, montant: float) -> str:
        """
        Formate un montant avec séparateur de milliers et 0 décimales.
        
        Args:
            montant: Montant à formater
        
        Returns:
            Montant formaté (ex: "1 500 000")
        """
        if pd.isna(montant) or montant == 0:
            return "-"
        
        # Formater avec séparateur d'espace pour les milliers, 0 décimales
        montant_int = int(round(montant))
        montant_str = f"{montant_int:,}".replace(',', ' ')
        
        return montant_str
    
    def appliquer_style_css(self) -> str:
        """
        Retourne le CSS pour le tableau conforme au style SYSCOHADA.
        
        Returns:
            Balise <style> avec le CSS complet
        """
        css = """<style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: Arial, sans-serif;
            background-color: #f5f5f5;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-radius: 8px;
        }
        
        h1 {
            color: #2c3e50;
            font-size: 24px;
            margin-bottom: 10px;
            text-align: center;
            font-weight: bold;
        }
        
        h2 {
            color: #34495e;
            font-size: 18px;
            margin-bottom: 30px;
            text-align: center;
            font-weight: normal;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
            font-size: 12px;
        }
        
        /* En-têtes de groupes */
        .header-group th {
            background-color: #2c3e50;
            color: white;
            padding: 12px 8px;
            text-align: center;
            font-weight: bold;
            border: 1px solid #1a252f;
        }
        
        .libelle-col {
            background-color: #2c3e50;
            color: white;
            min-width: 250px;
        }
        
        .group-header {
            background-color: #34495e;
            color: white;
        }
        
        /* Sous-en-têtes */
        .header-subgroup th {
            background-color: #7f8c8d;
            color: white;
            padding: 10px 8px;
            text-align: center;
            font-weight: normal;
            border: 1px solid #6c7a7b;
            font-size: 11px;
        }
        
        .subgroup-header {
            min-width: 100px;
        }
        
        /* Lignes de données */
        tbody tr {
            border-bottom: 1px solid #ddd;
        }
        
        .even-row {
            background-color: #ffffff;
        }
        
        .odd-row {
            background-color: #f9f9f9;
        }
        
        .even-row:hover, .odd-row:hover {
            background-color: #e8f4f8;
        }
        
        /* Ligne de total */
        .total-row {
            background-color: #ecf0f1;
            font-weight: bold;
            border-top: 2px solid #2c3e50;
            border-bottom: 2px solid #2c3e50;
        }
        
        .total-row:hover {
            background-color: #d5dbdb;
        }
        
        /* Cellules */
        td {
            padding: 10px 8px;
            border: 1px solid #ddd;
        }
        
        .libelle-cell {
            text-align: left;
            padding-left: 15px;
            font-weight: 500;
        }
        
        .montant-cell {
            text-align: right;
            font-family: 'Courier New', monospace;
            padding-right: 15px;
        }
        
        /* Footer */
        .footer {
            text-align: center;
            color: #7f8c8d;
            font-size: 11px;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
        }
        
        /* Responsive */
        @media screen and (max-width: 1200px) {
            .container {
                padding: 15px;
            }
            
            table {
                font-size: 10px;
            }
            
            .libelle-col {
                min-width: 200px;
            }
            
            .subgroup-header {
                min-width: 80px;
            }
        }
        
        @media screen and (max-width: 768px) {
            body {
                padding: 10px;
            }
            
            .container {
                padding: 10px;
            }
            
            h1 {
                font-size: 18px;
            }
            
            h2 {
                font-size: 14px;
            }
            
            table {
                font-size: 9px;
            }
            
            td, th {
                padding: 6px 4px;
            }
            
            .libelle-col {
                min-width: 150px;
            }
        }
        
        /* Impression */
        @media print {
            body {
                background-color: white;
                padding: 0;
            }
            
            .container {
                box-shadow: none;
                padding: 0;
            }
            
            .footer {
                page-break-after: avoid;
            }
        }
    </style>"""
        
        return css


# Exemple d'utilisation
if __name__ == "__main__":
    # Créer des données de test
    data = {
        'libelle': [
            'Frais de recherche et de développement',
            'Brevets, licences, logiciels',
            'Fonds commercial et droit au bail',
            'Autres immobilisations incorporelles',
            'TOTAL IMMOBILISATIONS INCORPORELLES'
        ],
        'brut_ouverture': [1500000, 2500000, 5000000, 800000, 9800000],
        'augmentations': [500000, 300000, 0, 200000, 1000000],
        'diminutions': [200000, 0, 0, 100000, 300000],
        'brut_cloture': [1800000, 2800000, 5000000, 900000, 10500000],
        'amort_ouverture': [300000, 1000000, 0, 400000, 1700000],
        'dotations': [200000, 300000, 0, 100000, 600000],
        'reprises': [50000, 0, 0, 50000, 100000],
        'amort_cloture': [450000, 1300000, 0, 450000, 2200000],
        'vnc_ouverture': [1200000, 1500000, 5000000, 400000, 8100000],
        'vnc_cloture': [1350000, 1500000, 5000000, 450000, 8300000]
    }
    
    df = pd.DataFrame(data)
    
    # Configuration des colonnes
    colonnes_config = {
        'groupes': [
            {
                'titre': 'VALEURS BRUTES',
                'colonnes': ['brut_ouverture', 'augmentations', 'diminutions', 'brut_cloture']
            },
            {
                'titre': 'AMORTISSEMENTS',
                'colonnes': ['amort_ouverture', 'dotations', 'reprises', 'amort_cloture']
            },
            {
                'titre': 'VALEURS NETTES COMPTABLES',
                'colonnes': ['vnc_ouverture', 'vnc_cloture']
            }
        ],
        'labels': {
            'brut_ouverture': 'Ouverture',
            'augmentations': 'Augmentations',
            'diminutions': 'Diminutions',
            'brut_cloture': 'Clôture',
            'amort_ouverture': 'Ouverture',
            'dotations': 'Dotations',
            'reprises': 'Reprises',
            'amort_cloture': 'Clôture',
            'vnc_ouverture': 'Ouverture',
            'vnc_cloture': 'Clôture'
        }
    }
    
    # Générer le HTML
    generator = HTMLGenerator("Immobilisations Incorporelles", "3A")
    html = generator.generer_html(df, colonnes_config)
    
    # Sauvegarder dans un fichier de test
    import os
    test_file = os.path.join('..', 'Tests', 'test_note_3a_html.html')
    os.makedirs(os.path.dirname(test_file), exist_ok=True)
    
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("✓ HTML généré avec succès: test_note_3a_html.html")
    print(f"✓ Taille du fichier: {len(html)} caractères")
    print(f"✓ Nombre de lignes: {len(df)}")
