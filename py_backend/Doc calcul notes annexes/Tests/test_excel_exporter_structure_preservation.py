"""
Property Test 15: Excel Export Structure Preservation

Ce test vérifie que l'export Excel préserve la structure des données
et applique le formatage correct conformément aux requirements 9.1-9.5.

Property: For any note annexe exported to Excel, the Excel_Exporter must create
a worksheet with the same structure as the HTML table (headers, data rows, total row),
with numeric formatting for amounts and styling (borders, header colors).

Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5

Author: Claraverse
Date: 2026-04-22
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from hypothesis import given, strategies as st, assume, settings
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Border
import tempfile
import shutil

from Modules.excel_exporter import ExcelExporter
from Tests.conftest import st_ligne_note_annexe, st_montant


# ============================================================================
# STRATÉGIES HYPOTHESIS POUR EXCEL EXPORT
# ============================================================================

@st.composite
def st_note_annexe_complete(draw):
    """
    Génère une note annexe complète avec configuration de colonnes.
    
    Returns:
        Tuple (numero_note, titre_note, df, colonnes_config)
    """
    # Numéro de note
    numero_note = draw(st.sampled_from(['3A', '3B', '3C', '3D', '3E', '4', '5']))
    
    # Titre de note
    titres = {
        '3A': 'Immobilisations Incorporelles',
        '3B': 'Immobilisations Corporelles',
        '3C': 'Immobilisations Financières',
        '3D': 'Charges Immobilisées',
        '3E': 'Écarts de Conversion Actif',
        '4': 'Stocks',
        '5': 'Créances Clients'
    }
    titre_note = titres[numero_note]
    
    # Générer 3 à 10 lignes de données
    num_lignes = draw(st.integers(min_value=3, max_value=10))
    lignes = [draw(st_ligne_note_annexe()) for _ in range(num_lignes)]
    
    # Ajouter une ligne de total
    ligne_total = {
        'libelle': 'TOTAL',
        'brut_ouverture': sum(l['brut_ouverture'] for l in lignes),
        'augmentations': sum(l['augmentations'] for l in lignes),
        'diminutions': sum(l['diminutions'] for l in lignes),
        'brut_cloture': sum(l['brut_cloture'] for l in lignes),
        'amort_ouverture': sum(l['amort_ouverture'] for l in lignes),
        'dotations': sum(l['dotations'] for l in lignes),
        'reprises': sum(l['reprises'] for l in lignes),
        'amort_cloture': sum(l['amort_cloture'] for l in lignes),
        'vnc_ouverture': sum(l['vnc_ouverture'] for l in lignes),
        'vnc_cloture': sum(l['vnc_cloture'] for l in lignes)
    }
    lignes.append(ligne_total)
    
    df = pd.DataFrame(lignes)
    
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
    
    return numero_note, titre_note, df, colonnes_config


# ============================================================================
# PROPERTY TESTS
# ============================================================================

@given(st_note_annexe_complete())
@settings(max_examples=50, deadline=30000)
def test_property_excel_structure_preservation(note_data):
    """
    Property 15: Excel Export Structure Preservation
    
    Vérifie que l'export Excel préserve:
    1. Le nombre de lignes (données + en-têtes)
    2. Le nombre de colonnes
    3. Les valeurs des cellules
    4. Le formatage des en-têtes
    5. Le formatage des montants
    6. Les bordures
    7. La ligne de total
    
    Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5
    """
    numero_note, titre_note, df, colonnes_config = note_data
    
    # Créer un répertoire temporaire pour les tests
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Créer le fichier Excel
        fichier_excel = os.path.join(temp_dir, 'test_export.xlsx')
        exporter = ExcelExporter(fichier_excel)
        
        # Exporter la note
        exporter.exporter_note(
            numero_note=numero_note,
            titre_note=titre_note,
            df=df,
            colonnes_config=colonnes_config
        )
        
        # Sauvegarder sans timestamp pour faciliter le test
        fichier_sauvegarde = exporter.sauvegarder(avec_timestamp=False)
        
        # Vérifier que le fichier existe
        assert os.path.exists(fichier_sauvegarde), \
            "Le fichier Excel doit être créé"
        
        # Charger le fichier Excel pour vérification
        wb = load_workbook(fichier_sauvegarde)
        nom_feuille = f"Note {numero_note}"
        
        # Vérification 1: La feuille existe
        assert nom_feuille in wb.sheetnames, \
            f"La feuille '{nom_feuille}' doit exister"
        
        ws = wb[nom_feuille]
        
        # Vérification 2: Titre de la note (ligne 1)
        titre_cell = ws['A1']
        assert titre_cell.value == f"NOTE {numero_note} - {titre_note}", \
            "Le titre de la note doit être correct"
        
        # Vérifier le formatage du titre
        assert titre_cell.font.bold == True, \
            "Le titre doit être en gras"
        assert titre_cell.fill.start_color.rgb == 'FF2C3E50', \
            "Le titre doit avoir le fond bleu foncé"
        
        # Vérification 3: Nombre de lignes de données
        # Ligne 1: Titre
        # Ligne 2: Vide
        # Ligne 3: En-têtes groupes
        # Ligne 4: Sous-en-têtes
        # Lignes 5+: Données
        expected_data_rows = len(df)
        actual_data_rows = ws.max_row - 4  # Soustraire les 4 lignes d'en-tête
        
        assert actual_data_rows == expected_data_rows, \
            f"Le nombre de lignes de données doit être {expected_data_rows}, trouvé {actual_data_rows}"
        
        # Vérification 4: Nombre de colonnes
        # 1 colonne libellé + nombre de colonnes de données
        total_colonnes_data = sum(len(g['colonnes']) for g in colonnes_config['groupes'])
        expected_columns = 1 + total_colonnes_data
        
        assert ws.max_column == expected_columns, \
            f"Le nombre de colonnes doit être {expected_columns}, trouvé {ws.max_column}"
        
        # Vérification 5: En-têtes de groupes (ligne 3)
        col_idx = 2  # Commencer après la colonne libellé
        for groupe in colonnes_config['groupes']:
            cell = ws.cell(row=3, column=col_idx)
            assert cell.value == groupe['titre'], \
                f"L'en-tête de groupe doit être '{groupe['titre']}'"
            
            # Vérifier le formatage de l'en-tête
            assert cell.font.bold == True, \
                "Les en-têtes de groupe doivent être en gras"
            assert cell.fill.start_color.rgb == 'FF34495E', \
                "Les en-têtes de groupe doivent avoir le fond gris-bleu"
            
            col_idx += len(groupe['colonnes'])
        
        # Vérification 6: Sous-en-têtes (ligne 4)
        col_idx = 2
        labels = colonnes_config['labels']
        
        for groupe in colonnes_config['groupes']:
            for colonne in groupe['colonnes']:
                cell = ws.cell(row=4, column=col_idx)
                expected_label = labels.get(colonne, colonne)
                assert cell.value == expected_label, \
                    f"Le sous-en-tête doit être '{expected_label}'"
                
                # Vérifier le formatage
                assert cell.fill.start_color.rgb == 'FF7F8C8D', \
                    "Les sous-en-têtes doivent avoir le fond gris"
                
                col_idx += 1
        
        # Vérification 7: Données et formatage des montants
        colonnes_ordre = []
        for groupe in colonnes_config['groupes']:
            colonnes_ordre.extend(groupe['colonnes'])
        
        for row_idx, (_, row_data) in enumerate(df.iterrows(), start=5):
            # Vérifier le libellé
            libelle_cell = ws.cell(row=row_idx, column=1)
            assert libelle_cell.value == row_data['libelle'], \
                f"Le libellé doit correspondre à la ligne {row_idx}"
            
            # Vérifier si c'est une ligne de total
            is_total = 'TOTAL' in str(row_data['libelle']).upper()
            
            if is_total:
                # Vérifier le formatage de la ligne de total
                assert libelle_cell.font.bold == True, \
                    "La ligne de total doit être en gras"
                assert libelle_cell.fill.start_color.rgb == 'FFECF0F1', \
                    "La ligne de total doit avoir un fond gris clair"
            
            # Vérifier les montants
            for col_idx, colonne in enumerate(colonnes_ordre, start=2):
                cell = ws.cell(row=row_idx, column=col_idx)
                montant = row_data[colonne]
                
                if pd.notna(montant) and montant != 0:
                    # Vérifier que la valeur est un nombre
                    assert isinstance(cell.value, (int, float)), \
                        f"La cellule ({row_idx}, {col_idx}) doit contenir un nombre"
                    
                    # Vérifier que la valeur correspond
                    assert abs(cell.value - montant) < 0.01, \
                        f"La valeur doit correspondre: attendu {montant}, trouvé {cell.value}"
                    
                    # Vérifier le format numérique (séparateur de milliers)
                    assert cell.number_format == '#,##0', \
                        "Les montants doivent avoir le format avec séparateur de milliers"
                else:
                    # Vérifier que les valeurs nulles sont affichées comme '-'
                    assert cell.value == '-', \
                        "Les valeurs nulles doivent être affichées comme '-'"
                
                # Vérifier le formatage de la ligne de total
                if is_total:
                    assert cell.font.bold == True, \
                        "Les montants de la ligne de total doivent être en gras"
                    assert cell.fill.start_color.rgb == 'FFECF0F1', \
                        "Les montants de la ligne de total doivent avoir un fond gris clair"
        
        # Vérification 8: Bordures
        # Vérifier que toutes les cellules de données ont des bordures
        for row in range(3, ws.max_row + 1):
            for col in range(1, ws.max_column + 1):
                cell = ws.cell(row=row, column=col)
                assert cell.border is not None, \
                    f"La cellule ({row}, {col}) doit avoir des bordures"
                assert cell.border.left.style == 'thin', \
                    "Les bordures doivent être de style 'thin'"
        
        # Vérification 9: Largeurs de colonnes
        assert ws.column_dimensions['A'].width == 40, \
            "La colonne libellé doit avoir une largeur de 40"
        
        for col in range(2, ws.max_column + 1):
            from openpyxl.utils import get_column_letter
            col_letter = get_column_letter(col)
            assert ws.column_dimensions[col_letter].width == 15, \
                f"La colonne {col_letter} doit avoir une largeur de 15"
        
        wb.close()
        
    finally:
        # Nettoyer le répertoire temporaire
        shutil.rmtree(temp_dir, ignore_errors=True)


@given(st.integers(min_value=1, max_value=10))
@settings(max_examples=20, deadline=30000)
def test_property_excel_multiple_notes_export(num_notes):
    """
    Property 15b: Multiple Notes Export Structure Preservation
    
    Vérifie que l'export de plusieurs notes crée bien une feuille par note
    avec la structure correcte pour chacune.
    
    Validates: Requirements 9.2, 9.6
    """
    temp_dir = tempfile.mkdtemp()
    
    try:
        fichier_excel = os.path.join(temp_dir, 'test_multiple.xlsx')
        exporter = ExcelExporter(fichier_excel)
        
        # Générer plusieurs notes
        notes_data = {}
        notes_list = ['3A', '3B', '3C', '3D', '3E', '4', '5', '6', '7', '8'][:num_notes]
        
        for numero_note in notes_list:
            # Créer des données simples
            data = {
                'libelle': ['Ligne 1', 'Ligne 2', 'TOTAL'],
                'brut_ouverture': [1000000, 2000000, 3000000],
                'augmentations': [100000, 200000, 300000],
                'diminutions': [50000, 100000, 150000],
                'brut_cloture': [1050000, 2100000, 3150000],
                'amort_ouverture': [200000, 400000, 600000],
                'dotations': [50000, 100000, 150000],
                'reprises': [10000, 20000, 30000],
                'amort_cloture': [240000, 480000, 720000],
                'vnc_ouverture': [800000, 1600000, 2400000],
                'vnc_cloture': [810000, 1620000, 2430000]
            }
            
            df = pd.DataFrame(data)
            
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
            
            notes_data[numero_note] = {
                'titre': f'Note {numero_note}',
                'df': df,
                'colonnes_config': colonnes_config
            }
        
        # Exporter toutes les notes
        exporter.exporter_toutes_notes(notes_data)
        fichier_sauvegarde = exporter.sauvegarder(avec_timestamp=False)
        
        # Vérifier que le fichier existe
        assert os.path.exists(fichier_sauvegarde), \
            "Le fichier Excel doit être créé"
        
        # Charger le fichier Excel
        wb = load_workbook(fichier_sauvegarde)
        
        # Vérification 1: Nombre de feuilles
        assert len(wb.sheetnames) == num_notes, \
            f"Le nombre de feuilles doit être {num_notes}, trouvé {len(wb.sheetnames)}"
        
        # Vérification 2: Noms des feuilles
        for numero_note in notes_list:
            nom_feuille = f"Note {numero_note}"
            assert nom_feuille in wb.sheetnames, \
                f"La feuille '{nom_feuille}' doit exister"
        
        # Vérification 3: Structure de chaque feuille
        for numero_note in notes_list:
            nom_feuille = f"Note {numero_note}"
            ws = wb[nom_feuille]
            
            # Vérifier que la feuille a des données
            assert ws.max_row >= 5, \
                f"La feuille '{nom_feuille}' doit avoir au moins 5 lignes"
            assert ws.max_column >= 2, \
                f"La feuille '{nom_feuille}' doit avoir au moins 2 colonnes"
            
            # Vérifier le titre
            titre_cell = ws['A1']
            assert f"NOTE {numero_note}" in titre_cell.value, \
                f"Le titre de la feuille '{nom_feuille}' doit contenir 'NOTE {numero_note}'"
        
        wb.close()
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@given(st.booleans())
@settings(max_examples=10, deadline=10000)
def test_property_excel_timestamp_filename(avec_timestamp):
    """
    Property 15c: Timestamp Filename Generation
    
    Vérifie que le nom de fichier avec timestamp est correctement généré.
    
    Validates: Requirement 9.5
    """
    temp_dir = tempfile.mkdtemp()
    
    try:
        fichier_base = os.path.join(temp_dir, 'notes_annexes.xlsx')
        exporter = ExcelExporter(fichier_base)
        
        # Créer une note simple
        data = {
            'libelle': ['Test'],
            'brut_ouverture': [1000000],
            'augmentations': [100000],
            'diminutions': [50000],
            'brut_cloture': [1050000],
            'amort_ouverture': [200000],
            'dotations': [50000],
            'reprises': [10000],
            'amort_cloture': [240000],
            'vnc_ouverture': [800000],
            'vnc_cloture': [810000]
        }
        
        df = pd.DataFrame(data)
        
        colonnes_config = {
            'groupes': [
                {
                    'titre': 'VALEURS BRUTES',
                    'colonnes': ['brut_ouverture', 'augmentations', 'diminutions', 'brut_cloture']
                }
            ],
            'labels': {
                'brut_ouverture': 'Ouverture',
                'augmentations': 'Augmentations',
                'diminutions': 'Diminutions',
                'brut_cloture': 'Clôture'
            }
        }
        
        exporter.exporter_note('TEST', 'Test', df, colonnes_config)
        
        # Sauvegarder avec ou sans timestamp
        fichier_sauvegarde = exporter.sauvegarder(avec_timestamp=avec_timestamp)
        
        # Vérifier que le fichier existe
        assert os.path.exists(fichier_sauvegarde), \
            "Le fichier Excel doit être créé"
        
        # Vérifier le nom du fichier
        nom_fichier = os.path.basename(fichier_sauvegarde)
        
        if avec_timestamp:
            # Le nom doit contenir un timestamp au format YYYYMMDD_HHMMSS
            assert '_' in nom_fichier, \
                "Le nom de fichier avec timestamp doit contenir un underscore"
            assert nom_fichier.startswith('notes_annexes_'), \
                "Le nom de fichier doit commencer par 'notes_annexes_'"
            assert nom_fichier.endswith('.xlsx'), \
                "Le nom de fichier doit se terminer par '.xlsx'"
            
            # Extraire le timestamp
            timestamp_part = nom_fichier.replace('notes_annexes_', '').replace('.xlsx', '')
            assert len(timestamp_part) == 15, \
                f"Le timestamp doit avoir 15 caractères (YYYYMMDD_HHMMSS), trouvé {len(timestamp_part)}"
        else:
            # Le nom doit être exactement le nom de base
            assert nom_fichier == 'notes_annexes.xlsx', \
                f"Le nom de fichier sans timestamp doit être 'notes_annexes.xlsx', trouvé '{nom_fichier}'"
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# ============================================================================
# TESTS UNITAIRES COMPLÉMENTAIRES
# ============================================================================

def test_excel_exporter_empty_dataframe():
    """Test avec un DataFrame vide"""
    temp_dir = tempfile.mkdtemp()
    
    try:
        fichier_excel = os.path.join(temp_dir, 'test_empty.xlsx')
        exporter = ExcelExporter(fichier_excel)
        
        # DataFrame vide
        df = pd.DataFrame()
        
        colonnes_config = {
            'groupes': [],
            'labels': {}
        }
        
        # Ne doit pas lever d'exception
        exporter.exporter_note('TEST', 'Test Vide', df, colonnes_config)
        fichier_sauvegarde = exporter.sauvegarder(avec_timestamp=False)
        
        assert os.path.exists(fichier_sauvegarde)
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_excel_exporter_large_numbers():
    """Test avec de très grands nombres"""
    temp_dir = tempfile.mkdtemp()
    
    try:
        fichier_excel = os.path.join(temp_dir, 'test_large.xlsx')
        exporter = ExcelExporter(fichier_excel)
        
        # Très grands nombres
        data = {
            'libelle': ['Ligne 1'],
            'brut_ouverture': [999999999999.99],
            'augmentations': [888888888888.88],
            'diminutions': [777777777777.77],
            'brut_cloture': [1111111111111.10],
            'amort_ouverture': [666666666666.66],
            'dotations': [555555555555.55],
            'reprises': [444444444444.44],
            'amort_cloture': [777777777777.77],
            'vnc_ouverture': [333333333333.33],
            'vnc_cloture': [333333333333.33]
        }
        
        df = pd.DataFrame(data)
        
        colonnes_config = {
            'groupes': [
                {
                    'titre': 'VALEURS BRUTES',
                    'colonnes': ['brut_ouverture', 'augmentations', 'diminutions', 'brut_cloture']
                }
            ],
            'labels': {
                'brut_ouverture': 'Ouverture',
                'augmentations': 'Augmentations',
                'diminutions': 'Diminutions',
                'brut_cloture': 'Clôture'
            }
        }
        
        exporter.exporter_note('TEST', 'Test Grands Nombres', df, colonnes_config)
        fichier_sauvegarde = exporter.sauvegarder(avec_timestamp=False)
        
        # Vérifier que le fichier est créé et lisible
        wb = load_workbook(fichier_sauvegarde)
        ws = wb['Note TEST']
        
        # Vérifier que les grands nombres sont correctement stockés
        cell = ws.cell(row=5, column=2)
        assert abs(cell.value - 999999999999.99) < 0.01
        
        wb.close()
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    print("=" * 80)
    print("PROPERTY TEST 15: Excel Export Structure Preservation")
    print("=" * 80)
    print("\nCe test vérifie que l'export Excel préserve la structure des données")
    print("et applique le formatage correct.")
    print("\nExécution des tests avec Hypothesis...")
    print("\nPour exécuter ce test:")
    print("  pytest test_excel_exporter_structure_preservation.py -v")
    print("\nOu pour voir plus de détails:")
    print("  pytest test_excel_exporter_structure_preservation.py -v -s")
    print("=" * 80)
