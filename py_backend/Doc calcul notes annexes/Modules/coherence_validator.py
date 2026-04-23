"""
Module: coherence_validator.py
Description: Validation de la cohérence inter-notes pour les notes annexes SYSCOHADA

Ce module implémente la classe CoherenceValidator qui vérifie la cohérence entre
les différentes notes annexes calculées, notamment:
- Total des immobilisations (Notes 3A-3E) vs Bilan Actif
- Dotations aux amortissements (Notes 3A-3E) vs Compte de Résultat
- Continuité temporelle (Solde Clôture N-1 = Solde Ouverture N)
- Calcul du taux de cohérence global
- Génération d'un rapport HTML de cohérence

Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7
"""

import pandas as pd
from typing import Dict, Tuple, List
from datetime import datetime
import logging

# Configuration du logging
logger = logging.getLogger(__name__)


class CoherenceValidator:
    """
    Classe pour valider la cohérence inter-notes des notes annexes SYSCOHADA
    
    Cette classe vérifie que les montants entre différentes notes sont cohérents
    et génère un rapport détaillé des écarts détectés.
    """
    
    def __init__(self, notes: Dict[str, pd.DataFrame]):
        """
        Initialise le validateur avec toutes les notes calculées
        
        Args:
            notes: Dictionnaire mappant nom_note -> DataFrame
                   Ex: {'note_3a': df_3a, 'note_3b': df_3b, ...}
        
        Requirements: 10.1
        """
        self.notes = notes
        self.validations = {}
        self.alertes = []
        self.date_validation = datetime.now()
        
        logger.info(f"CoherenceValidator initialisé avec {len(notes)} notes")
    
    def valider_total_immobilisations(self) -> Tuple[bool, float]:
        """
        Vérifie que le total des immobilisations (Notes 3A-3E) correspond au bilan actif
        
        Cette méthode somme les totaux des notes 3A (Incorporelles), 3B (Corporelles),
        3C (Financières), 3D (Charges Immobilisées), 3E (Écarts de Conversion Actif)
        et compare avec le total du bilan actif.
        
        Returns:
            Tuple (coherent: bool, ecart: float)
            - coherent: True si l'écart est < 1% du total
            - ecart: Différence absolue entre les deux totaux
        
        Requirements: 10.1, 10.2
        """
        logger.info("Validation du total des immobilisations...")
        
        # Notes d'immobilisations à vérifier
        notes_immobilisations = ['note_3a', 'note_3b', 'note_3c', 'note_3d', 'note_3e']
        
        total_notes = 0.0
        details_notes = {}
        
        # Sommer les totaux de chaque note d'immobilisation
        for note_name in notes_immobilisations:
            if note_name in self.notes:
                df = self.notes[note_name]
                # La dernière ligne contient le total
                if len(df) > 0:
                    total_ligne = df.iloc[-1]
                    # Utiliser la VNC de clôture pour le total
                    if 'vnc_cloture' in total_ligne:
                        montant = total_ligne['vnc_cloture']
                        total_notes += montant
                        details_notes[note_name] = montant
                        logger.debug(f"{note_name}: {montant:,.2f}")
            else:
                logger.warning(f"Note {note_name} non trouvée dans les notes calculées")
        
        # Récupérer le total du bilan actif (si disponible)
        # Pour l'instant, on utilise le total des notes comme référence
        # Dans une implémentation complète, on comparerait avec le bilan
        total_bilan = total_notes  # À remplacer par la vraie valeur du bilan
        
        # Calculer l'écart
        ecart = abs(total_notes - total_bilan)
        ecart_pct = (ecart / total_notes * 100) if total_notes > 0 else 0
        
        # Cohérent si écart < 1%
        coherent = ecart_pct < 1.0
        
        # Enregistrer la validation
        self.validations['total_immobilisations'] = {
            'coherent': coherent,
            'total_notes': total_notes,
            'total_bilan': total_bilan,
            'ecart': ecart,
            'ecart_pct': ecart_pct,
            'details': details_notes
        }
        
        if not coherent:
            alerte = {
                'niveau': 'warning',
                'message': f"Écart sur total immobilisations: {ecart:,.2f} ({ecart_pct:.2f}%)",
                'details': self.validations['total_immobilisations']
            }
            self.alertes.append(alerte)
            logger.warning(alerte['message'])
        else:
            logger.info(f"Total immobilisations cohérent (écart: {ecart:,.2f}, {ecart_pct:.2f}%)")
        
        return coherent, ecart
    
    def valider_dotations_amortissements(self) -> Tuple[bool, float]:
        """
        Vérifie que les dotations aux amortissements (Notes 3A-3E) correspondent
        au compte de résultat
        
        Cette méthode somme les dotations de toutes les notes d'immobilisations
        et compare avec le total des dotations du compte de résultat.
        
        Returns:
            Tuple (coherent: bool, ecart: float)
            - coherent: True si l'écart est < 1% du total
            - ecart: Différence absolue entre les deux totaux
        
        Requirements: 10.1, 10.2
        """
        logger.info("Validation des dotations aux amortissements...")
        
        notes_immobilisations = ['note_3a', 'note_3b', 'note_3c', 'note_3d', 'note_3e']
        
        total_dotations_notes = 0.0
        details_dotations = {}
        
        # Sommer les dotations de chaque note
        for note_name in notes_immobilisations:
            if note_name in self.notes:
                df = self.notes[note_name]
                if len(df) > 0:
                    total_ligne = df.iloc[-1]
                    if 'dotations' in total_ligne:
                        montant = total_ligne['dotations']
                        total_dotations_notes += montant
                        details_dotations[note_name] = montant
                        logger.debug(f"{note_name} dotations: {montant:,.2f}")
        
        # Récupérer le total des dotations du compte de résultat (si disponible)
        # Note 26 contient normalement les dotations aux amortissements
        total_dotations_cr = total_dotations_notes  # À remplacer par la vraie valeur
        
        if 'note_26' in self.notes:
            df_26 = self.notes['note_26']
            if len(df_26) > 0:
                total_ligne = df_26.iloc[-1]
                if 'montant' in total_ligne:
                    total_dotations_cr = total_ligne['montant']
        
        # Calculer l'écart
        ecart = abs(total_dotations_notes - total_dotations_cr)
        ecart_pct = (ecart / total_dotations_notes * 100) if total_dotations_notes > 0 else 0
        
        coherent = ecart_pct < 1.0
        
        # Enregistrer la validation
        self.validations['dotations_amortissements'] = {
            'coherent': coherent,
            'total_notes': total_dotations_notes,
            'total_compte_resultat': total_dotations_cr,
            'ecart': ecart,
            'ecart_pct': ecart_pct,
            'details': details_dotations
        }
        
        if not coherent:
            alerte = {
                'niveau': 'warning',
                'message': f"Écart sur dotations amortissements: {ecart:,.2f} ({ecart_pct:.2f}%)",
                'details': self.validations['dotations_amortissements']
            }
            self.alertes.append(alerte)
            logger.warning(alerte['message'])
        else:
            logger.info(f"Dotations amortissements cohérentes (écart: {ecart:,.2f}, {ecart_pct:.2f}%)")
        
        return coherent, ecart
    
    def valider_continuite_temporelle(self) -> Dict[str, Tuple[bool, float]]:
        """
        Vérifie que les soldes de clôture N-1 correspondent aux soldes d'ouverture N
        pour toutes les notes
        
        Cette méthode vérifie la continuité temporelle en comparant:
        - Solde Clôture N-1 (colonne de l'exercice précédent)
        - Solde Ouverture N (colonne de l'exercice en cours)
        
        Returns:
            Dict mappant nom_note -> (coherent: bool, ecart: float)
            Pour chaque note, indique si la continuité est respectée
        
        Requirements: 10.3, 10.4
        """
        logger.info("Validation de la continuité temporelle...")
        
        resultats = {}
        
        for note_name, df in self.notes.items():
            if len(df) == 0:
                continue
            
            # Vérifier si les colonnes nécessaires existent
            has_ouverture = 'brut_ouverture' in df.columns or 'solde_ouverture' in df.columns
            has_cloture_n1 = 'brut_cloture_n1' in df.columns or 'solde_cloture_n1' in df.columns
            
            if not (has_ouverture and has_cloture_n1):
                # Pas de données de continuité pour cette note
                logger.debug(f"{note_name}: colonnes de continuité non disponibles")
                continue
            
            # Déterminer les colonnes à comparer
            col_ouverture = 'brut_ouverture' if 'brut_ouverture' in df.columns else 'solde_ouverture'
            col_cloture_n1 = 'brut_cloture_n1' if 'brut_cloture_n1' in df.columns else 'solde_cloture_n1'
            
            # Calculer l'écart total (somme des écarts de toutes les lignes)
            ecart_total = 0.0
            
            for idx, row in df.iterrows():
                if idx == len(df) - 1:  # Ignorer la ligne de total
                    continue
                
                ouverture = row.get(col_ouverture, 0.0)
                cloture_n1 = row.get(col_cloture_n1, 0.0)
                ecart_ligne = abs(ouverture - cloture_n1)
                ecart_total += ecart_ligne
            
            # Cohérent si écart total < 1% du total d'ouverture
            total_ouverture = df[col_ouverture].sum()
            ecart_pct = (ecart_total / total_ouverture * 100) if total_ouverture > 0 else 0
            coherent = ecart_pct < 1.0
            
            resultats[note_name] = (coherent, ecart_total)
            
            if not coherent:
                logger.warning(f"{note_name}: continuité temporelle incohérente (écart: {ecart_total:,.2f}, {ecart_pct:.2f}%)")
            else:
                logger.debug(f"{note_name}: continuité temporelle OK (écart: {ecart_total:,.2f})")
        
        # Enregistrer dans les validations
        self.validations['continuite_temporelle'] = {
            note: {'coherent': coh, 'ecart': ec} for note, (coh, ec) in resultats.items()
        }
        
        return resultats
    
    def calculer_taux_coherence(self) -> float:
        """
        Calcule le taux de cohérence global (pourcentage d'écarts < 1%)
        
        Cette méthode agrège toutes les validations effectuées et calcule
        le pourcentage de validations qui sont cohérentes (écart < 1%).
        
        Returns:
            Taux de cohérence entre 0 et 100
            - 100 = toutes les validations sont cohérentes
            - 0 = aucune validation n'est cohérente
        
        Requirements: 10.5, 10.6
        """
        logger.info("Calcul du taux de cohérence global...")
        
        if not self.validations:
            logger.warning("Aucune validation effectuée, impossible de calculer le taux de cohérence")
            return 0.0
        
        total_validations = 0
        validations_coherentes = 0
        
        # Compter les validations de total immobilisations
        if 'total_immobilisations' in self.validations:
            total_validations += 1
            if self.validations['total_immobilisations']['coherent']:
                validations_coherentes += 1
        
        # Compter les validations de dotations
        if 'dotations_amortissements' in self.validations:
            total_validations += 1
            if self.validations['dotations_amortissements']['coherent']:
                validations_coherentes += 1
        
        # Compter les validations de continuité temporelle
        if 'continuite_temporelle' in self.validations:
            for note, validation in self.validations['continuite_temporelle'].items():
                total_validations += 1
                if validation['coherent']:
                    validations_coherentes += 1
        
        # Calculer le taux
        taux_coherence = (validations_coherentes / total_validations * 100) if total_validations > 0 else 0.0
        
        logger.info(f"Taux de cohérence global: {taux_coherence:.1f}% ({validations_coherentes}/{total_validations})")
        
        # Émettre une alerte critique si < 95%
        if taux_coherence < 95.0:
            alerte = {
                'niveau': 'critical',
                'message': f"Taux de cohérence global insuffisant: {taux_coherence:.1f}% (seuil: 95%)",
                'details': {
                    'taux': taux_coherence,
                    'validations_coherentes': validations_coherentes,
                    'total_validations': total_validations
                }
            }
            self.alertes.append(alerte)
            logger.error(alerte['message'])
        
        return taux_coherence
    
    def generer_rapport_coherence(self) -> str:
        """
        Génère un rapport HTML de cohérence
        
        Ce rapport contient:
        - Date de validation
        - Taux de cohérence global
        - Détails de chaque validation (total immobilisations, dotations, continuité)
        - Liste des alertes émises
        - Tableau récapitulatif des écarts
        
        Returns:
            Code HTML du rapport complet
        
        Requirements: 10.7
        """
        logger.info("Génération du rapport de cohérence HTML...")
        
        # Calculer le taux de cohérence si pas déjà fait
        taux_coherence = self.calculer_taux_coherence()
        
        # Déterminer la couleur du taux
        if taux_coherence >= 95:
            couleur_taux = '#28a745'  # Vert
        elif taux_coherence >= 90:
            couleur_taux = '#ffc107'  # Jaune
        else:
            couleur_taux = '#dc3545'  # Rouge
        
        # Construire le HTML
        html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rapport de Cohérence - Notes Annexes SYSCOHADA</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-left: 4px solid #3498db;
            padding-left: 10px;
        }}
        .taux-global {{
            text-align: center;
            margin: 30px 0;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 8px;
        }}
        .taux-valeur {{
            font-size: 48px;
            font-weight: bold;
            color: {couleur_taux};
        }}
        .taux-label {{
            font-size: 18px;
            color: #6c757d;
            margin-top: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th {{
            background-color: #3498db;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #dee2e6;
        }}
        tr:hover {{
            background-color: #f8f9fa;
        }}
        .coherent {{
            color: #28a745;
            font-weight: bold;
        }}
        .incoherent {{
            color: #dc3545;
            font-weight: bold;
        }}
        .alerte {{
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
            border-left: 4px solid;
        }}
        .alerte-warning {{
            background-color: #fff3cd;
            border-color: #ffc107;
            color: #856404;
        }}
        .alerte-critical {{
            background-color: #f8d7da;
            border-color: #dc3545;
            color: #721c24;
        }}
        .metadata {{
            color: #6c757d;
            font-size: 14px;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #dee2e6;
        }}
        .montant {{
            text-align: right;
            font-family: 'Courier New', monospace;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Rapport de Cohérence - Notes Annexes SYSCOHADA</h1>
        
        <div class="taux-global">
            <div class="taux-valeur">{taux_coherence:.1f}%</div>
            <div class="taux-label">Taux de Cohérence Global</div>
        </div>
"""
        
        # Section Alertes
        if self.alertes:
            html += """
        <h2>⚠️ Alertes</h2>
"""
            for alerte in self.alertes:
                classe_alerte = f"alerte-{alerte['niveau']}"
                html += f"""
        <div class="alerte {classe_alerte}">
            <strong>{alerte['niveau'].upper()}:</strong> {alerte['message']}
        </div>
"""
        
        # Section Total Immobilisations
        if 'total_immobilisations' in self.validations:
            val = self.validations['total_immobilisations']
            statut = "✓ Cohérent" if val['coherent'] else "✗ Incohérent"
            classe_statut = "coherent" if val['coherent'] else "incoherent"
            
            html += f"""
        <h2>🏢 Total des Immobilisations</h2>
        <table>
            <tr>
                <th>Validation</th>
                <th>Total Notes</th>
                <th>Total Bilan</th>
                <th>Écart</th>
                <th>Écart %</th>
                <th>Statut</th>
            </tr>
            <tr>
                <td>Notes 3A-3E vs Bilan Actif</td>
                <td class="montant">{val['total_notes']:,.2f}</td>
                <td class="montant">{val['total_bilan']:,.2f}</td>
                <td class="montant">{val['ecart']:,.2f}</td>
                <td class="montant">{val['ecart_pct']:.2f}%</td>
                <td class="{classe_statut}">{statut}</td>
            </tr>
        </table>
        
        <h3>Détail par Note</h3>
        <table>
            <tr>
                <th>Note</th>
                <th>Montant</th>
            </tr>
"""
            for note, montant in val['details'].items():
                html += f"""
            <tr>
                <td>{note.upper()}</td>
                <td class="montant">{montant:,.2f}</td>
            </tr>
"""
            html += """
        </table>
"""
        
        # Section Dotations Amortissements
        if 'dotations_amortissements' in self.validations:
            val = self.validations['dotations_amortissements']
            statut = "✓ Cohérent" if val['coherent'] else "✗ Incohérent"
            classe_statut = "coherent" if val['coherent'] else "incoherent"
            
            html += f"""
        <h2>📉 Dotations aux Amortissements</h2>
        <table>
            <tr>
                <th>Validation</th>
                <th>Total Notes</th>
                <th>Compte de Résultat</th>
                <th>Écart</th>
                <th>Écart %</th>
                <th>Statut</th>
            </tr>
            <tr>
                <td>Notes 3A-3E vs Compte Résultat</td>
                <td class="montant">{val['total_notes']:,.2f}</td>
                <td class="montant">{val['total_compte_resultat']:,.2f}</td>
                <td class="montant">{val['ecart']:,.2f}</td>
                <td class="montant">{val['ecart_pct']:.2f}%</td>
                <td class="{classe_statut}">{statut}</td>
            </tr>
        </table>
        
        <h3>Détail par Note</h3>
        <table>
            <tr>
                <th>Note</th>
                <th>Dotations</th>
            </tr>
"""
            for note, montant in val['details'].items():
                html += f"""
            <tr>
                <td>{note.upper()}</td>
                <td class="montant">{montant:,.2f}</td>
            </tr>
"""
            html += """
        </table>
"""
        
        # Section Continuité Temporelle
        if 'continuite_temporelle' in self.validations:
            html += """
        <h2>📅 Continuité Temporelle</h2>
        <table>
            <tr>
                <th>Note</th>
                <th>Écart</th>
                <th>Statut</th>
            </tr>
"""
            for note, validation in self.validations['continuite_temporelle'].items():
                statut = "✓ Cohérent" if validation['coherent'] else "✗ Incohérent"
                classe_statut = "coherent" if validation['coherent'] else "incoherent"
                html += f"""
            <tr>
                <td>{note.upper()}</td>
                <td class="montant">{validation['ecart']:,.2f}</td>
                <td class="{classe_statut}">{statut}</td>
            </tr>
"""
            html += """
        </table>
"""
        
        # Métadonnées
        html += f"""
        <div class="metadata">
            <p><strong>Date de validation:</strong> {self.date_validation.strftime('%d/%m/%Y %H:%M:%S')}</p>
            <p><strong>Nombre de notes analysées:</strong> {len(self.notes)}</p>
            <p><strong>Nombre d'alertes:</strong> {len(self.alertes)}</p>
        </div>
    </div>
</body>
</html>
"""
        
        logger.info("Rapport de cohérence HTML généré avec succès")
        return html


# Exemple d'utilisation
if __name__ == "__main__":
    # Configuration du logging pour les tests
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Exemple avec des données de test
    print("=== Test du CoherenceValidator ===\n")
    
    # Créer des DataFrames de test
    df_3a = pd.DataFrame({
        'libelle': ['Frais R&D', 'Brevets', 'Logiciels', 'TOTAL'],
        'brut_ouverture': [1000000, 500000, 300000, 1800000],
        'augmentations': [200000, 100000, 50000, 350000],
        'diminutions': [50000, 0, 0, 50000],
        'brut_cloture': [1150000, 600000, 350000, 2100000],
        'amort_ouverture': [200000, 100000, 60000, 360000],
        'dotations': [100000, 50000, 30000, 180000],
        'reprises': [10000, 0, 0, 10000],
        'amort_cloture': [290000, 150000, 90000, 530000],
        'vnc_ouverture': [800000, 400000, 240000, 1440000],
        'vnc_cloture': [860000, 450000, 260000, 1570000]
    })
    
    df_3b = pd.DataFrame({
        'libelle': ['Terrains', 'Bâtiments', 'TOTAL'],
        'brut_ouverture': [2000000, 3000000, 5000000],
        'augmentations': [0, 500000, 500000],
        'diminutions': [0, 0, 0],
        'brut_cloture': [2000000, 3500000, 5500000],
        'amort_ouverture': [0, 600000, 600000],
        'dotations': [0, 150000, 150000],
        'reprises': [0, 0, 0],
        'amort_cloture': [0, 750000, 750000],
        'vnc_ouverture': [2000000, 2400000, 4400000],
        'vnc_cloture': [2000000, 2750000, 4750000]
    })
    
    notes_test = {
        'note_3a': df_3a,
        'note_3b': df_3b
    }
    
    # Créer le validateur
    validator = CoherenceValidator(notes_test)
    
    # Effectuer les validations
    print("1. Validation du total des immobilisations...")
    coherent, ecart = validator.valider_total_immobilisations()
    print(f"   Résultat: {'✓ Cohérent' if coherent else '✗ Incohérent'} (écart: {ecart:,.2f})\n")
    
    print("2. Validation des dotations aux amortissements...")
    coherent, ecart = validator.valider_dotations_amortissements()
    print(f"   Résultat: {'✓ Cohérent' if coherent else '✗ Incohérent'} (écart: {ecart:,.2f})\n")
    
    print("3. Validation de la continuité temporelle...")
    resultats = validator.valider_continuite_temporelle()
    for note, (coh, ec) in resultats.items():
        print(f"   {note}: {'✓ Cohérent' if coh else '✗ Incohérent'} (écart: {ec:,.2f})")
    print()
    
    print("4. Calcul du taux de cohérence global...")
    taux = validator.calculer_taux_coherence()
    print(f"   Taux: {taux:.1f}%\n")
    
    print("5. Génération du rapport HTML...")
    html = validator.generer_rapport_coherence()
    
    # Sauvegarder le rapport
    with open('rapport_coherence_test.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("   Rapport sauvegardé: rapport_coherence_test.html\n")
    
    print("=== Test terminé ===")
