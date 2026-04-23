"""
Property-Based Tests for Trace Export Format Conversion

Feature: calcul-notes-annexes-syscohada
Property 24: Trace Export Format Conversion

For any trace file in JSON format, the system must be able to export it to CSV 
format preserving all calculation details for analysis in Excel.

Validates: Requirements 15.6
"""

import pytest
from hypothesis import given, settings, strategies as st, assume
import json
import csv
import os
import hashlib
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from Modules.trace_manager import TraceManager


# ============================================================================
# Hypothesis Strategies
# ============================================================================

@st.composite
def st_numero_note(draw):
    """Generate valid note numbers (01-33)"""
    numero = draw(st.integers(min_value=1, max_value=33))
    return f"{numero:02d}"


@st.composite
def st_calcul_data(draw):
    """Generate calculation data for tracing"""
    libelle = draw(st.text(min_size=5, max_size=100, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters=' -éèêàâùûôîç')))
    montant = draw(st.floats(min_value=0, max_value=1e9, allow_nan=False, allow_infinity=False))
    
    # Generate source accounts
    num_comptes = draw(st.integers(min_value=1, max_value=5))
    comptes_sources = []
    
    for _ in range(num_comptes):
        compte = {
            'compte': draw(st.text(min_size=3, max_size=5, alphabet='0123456789')),
            'intitule': draw(st.text(min_size=5, max_size=50, alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll'), whitelist_characters=' '))),
            'valeur': draw(st.floats(min_value=0, max_value=1e8, allow_nan=False, allow_infinity=False)),
            'type_valeur': draw(st.sampled_from(['brut', 'amortissement', 'vnc', 'dotation', 'reprise']))
        }
        comptes_sources.append(compte)
    
    return {
        'libelle': libelle,
        'montant': montant,
        'comptes_sources': comptes_sources
    }


@st.composite
def st_fichier_balance(draw):
    """Generate balance file name"""
    prefixe = draw(st.sampled_from(['P000', 'P001', 'BALANCE', 'TEST']))
    suffixe = draw(st.sampled_from(['N_N-1_N-2', 'DEMO', 'TEST']))
    return f"{prefixe} - {suffixe}.xlsx"


# ============================================================================
# Property 24: Trace Export Format Conversion
# ============================================================================

@given(
    numero_note=st_numero_note(),
    calculs=st.lists(st_calcul_data(), min_size=1, max_size=10),
    fichier_balance=st_fichier_balance()
)
@settings(max_examples=100, deadline=None)
def test_property_24_trace_export_format_conversion(numero_note, calculs, fichier_balance):
    """
    Property 24: Trace Export Format Conversion
    
    For any trace file in JSON format, the system must be able to export it 
    to CSV format preserving all calculation details for analysis in Excel.
    
    This property verifies that:
    1. JSON trace can be converted to CSV format
    2. All calculation details are preserved in the conversion
    3. CSV format is compatible with Excel (UTF-8-BOM, semicolon delimiter)
    4. Each source account becomes a separate CSV row
    5. Metadata is replicated across all rows for filtering in Excel
    
    Validates: Requirements 15.6
    """
    # Arrange
    trace_manager = TraceManager(numero_note)
    
    # Generate MD5 hash for the balance file
    hash_md5 = hashlib.md5(fichier_balance.encode()).hexdigest()
    
    # Record metadata
    trace_manager.enregistrer_metadata(fichier_balance, hash_md5)
    
    # Record all calculations
    for calcul in calculs:
        trace_manager.enregistrer_calcul(
            libelle=calcul['libelle'],
            montant=calcul['montant'],
            comptes_sources=calcul['comptes_sources']
        )
    
    # Act - Export to CSV
    csv_file = f"temp_trace_export_{numero_note}.csv"
    
    try:
        csv_path = trace_manager.exporter_csv(csv_file)
        
        # Assert - Verify CSV file exists
        assert os.path.exists(csv_path), "CSV file must be created"
        
        # Property 1: CSV file must be readable
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f, delimiter=';')
            rows = list(reader)
        
        assert len(rows) > 0, "CSV must contain at least header row"
        
        # Property 2: CSV must have correct headers
        headers = rows[0]
        expected_headers = [
            'Note', 'Titre', 'Date Génération', 'Fichier Balance', 'Hash MD5',
            'Libellé Ligne', 'Montant', 'Compte Source', 'Intitulé Compte',
            'Valeur Compte', 'Type Valeur'
        ]
        assert headers == expected_headers, "CSV headers must match expected format"
        
        # Property 3: CSV must contain data rows (header + data)
        data_rows = rows[1:]
        
        # Calculate expected number of rows
        # Each calculation with N source accounts generates N rows
        expected_row_count = sum(len(c['comptes_sources']) for c in calculs)
        assert len(data_rows) == expected_row_count, \
            f"CSV must have one row per source account (expected {expected_row_count}, got {len(data_rows)})"
        
        # Property 4: All calculation details must be preserved
        row_index = 0
        for calcul in calculs:
            for compte_source in calcul['comptes_sources']:
                row = data_rows[row_index]
                
                # Verify metadata is present in each row
                assert row[0] == numero_note, "Note number must be preserved"
                assert row[2] != "", "Generation date must be present"
                assert row[3] == fichier_balance, "Balance file name must be preserved"
                assert row[4] == hash_md5, "MD5 hash must be preserved"
                
                # Verify calculation details
                assert row[5] == calcul['libelle'], "Libellé must be preserved"
                
                # Verify montant (allow small floating point differences)
                montant_csv = float(row[6])
                assert abs(montant_csv - calcul['montant']) < 0.01, "Montant must be preserved"
                
                # Verify source account details
                assert row[7] == compte_source['compte'], "Account number must be preserved"
                assert row[8] == compte_source['intitule'], "Account label must be preserved"
                
                valeur_csv = float(row[9])
                assert abs(valeur_csv - compte_source['valeur']) < 0.01, "Account value must be preserved"
                
                assert row[10] == compte_source['type_valeur'], "Value type must be preserved"
                
                row_index += 1
        
        # Property 5: CSV format must be Excel-compatible
        # Verify encoding is UTF-8 with BOM (for Excel compatibility)
        with open(csv_path, 'rb') as f:
            first_bytes = f.read(3)
            # UTF-8 BOM is EF BB BF
            assert first_bytes == b'\xef\xbb\xbf', "CSV must use UTF-8-BOM encoding for Excel"
        
        # Property 6: CSV must use semicolon delimiter (Excel standard for European locales)
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            first_line = f.readline()
            assert ';' in first_line, "CSV must use semicolon delimiter"
        
        # Property 7: All rows must have the same number of columns
        column_counts = [len(row) for row in rows]
        assert len(set(column_counts)) == 1, "All rows must have the same number of columns"
        assert column_counts[0] == len(expected_headers), "All rows must have correct column count"
        
        # Property 8: CSV must be parseable back to verify round-trip
        # Read CSV and verify we can reconstruct the original data
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f, delimiter=';')
            csv_data = list(reader)
        
        # Verify we can group by libellé and reconstruct calculations
        libelles_in_csv = set(row['Libellé Ligne'] for row in csv_data)
        libelles_original = set(c['libelle'] for c in calculs)
        assert libelles_in_csv == libelles_original, "All calculation labels must be in CSV"
        
        # Property 9: Metadata must be consistent across all rows
        for row in csv_data:
            assert row['Note'] == numero_note
            assert row['Fichier Balance'] == fichier_balance
            assert row['Hash MD5'] == hash_md5
            # Date should be the same for all rows (same generation)
            assert row['Date Génération'] != ""
        
    finally:
        # Cleanup
        if os.path.exists(csv_path):
            os.remove(csv_path)


@given(
    numero_note=st_numero_note(),
    fichier_balance=st_fichier_balance()
)
@settings(max_examples=50, deadline=None)
def test_property_24_csv_export_with_empty_calculations(numero_note, fichier_balance):
    """
    Property 24 Edge Case: CSV Export with No Calculations
    
    Even if no calculations are recorded, the CSV export must still work
    and contain at least the header row.
    
    Validates: Requirements 15.6
    """
    # Arrange
    trace_manager = TraceManager(numero_note)
    hash_md5 = hashlib.md5(fichier_balance.encode()).hexdigest()
    
    # Only record metadata, no calculations
    trace_manager.enregistrer_metadata(fichier_balance, hash_md5)
    
    # Act
    csv_file = f"temp_trace_empty_export_{numero_note}.csv"
    
    try:
        csv_path = trace_manager.exporter_csv(csv_file)
        
        # Assert
        assert os.path.exists(csv_path)
        
        # Read CSV
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f, delimiter=';')
            rows = list(reader)
        
        # Must have at least header row
        assert len(rows) >= 1, "CSV must have at least header row"
        
        # Verify headers are correct
        headers = rows[0]
        expected_headers = [
            'Note', 'Titre', 'Date Génération', 'Fichier Balance', 'Hash MD5',
            'Libellé Ligne', 'Montant', 'Compte Source', 'Intitulé Compte',
            'Valeur Compte', 'Type Valeur'
        ]
        assert headers == expected_headers
        
        # With no calculations, should have only header (or empty data rows)
        # This is acceptable - the file is still valid
        
    finally:
        # Cleanup
        if os.path.exists(csv_path):
            os.remove(csv_path)


@given(
    numero_note=st_numero_note(),
    calculs=st.lists(st_calcul_data(), min_size=1, max_size=5),
    fichier_balance=st_fichier_balance()
)
@settings(max_examples=50, deadline=None)
def test_property_24_csv_preserves_special_characters(numero_note, calculs, fichier_balance):
    """
    Property 24 Extension: CSV Export Preserves Special Characters
    
    The CSV export must correctly handle special characters (accents, 
    semicolons, quotes) that are common in French accounting labels.
    
    Validates: Requirements 15.6
    """
    # Arrange
    trace_manager = TraceManager(numero_note)
    hash_md5 = hashlib.md5(fichier_balance.encode()).hexdigest()
    
    trace_manager.enregistrer_metadata(fichier_balance, hash_md5)
    
    # Add calculations with special characters
    for calcul in calculs:
        trace_manager.enregistrer_calcul(
            libelle=calcul['libelle'],
            montant=calcul['montant'],
            comptes_sources=calcul['comptes_sources']
        )
    
    # Act
    csv_file = f"temp_trace_special_chars_{numero_note}.csv"
    
    try:
        csv_path = trace_manager.exporter_csv(csv_file)
        
        # Assert - Read CSV and verify special characters are preserved
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f, delimiter=';')
            csv_data = list(reader)
        
        # Verify all libellés are preserved with their special characters
        libelles_in_csv = [row['Libellé Ligne'] for row in csv_data]
        
        for calcul in calculs:
            # The libellé should appear in CSV (once per source account)
            count_in_csv = libelles_in_csv.count(calcul['libelle'])
            expected_count = len(calcul['comptes_sources'])
            assert count_in_csv == expected_count, \
                f"Libellé '{calcul['libelle']}' must appear {expected_count} times"
        
        # Verify intitulés are preserved
        for row in csv_data:
            # Intitulé should not be corrupted
            intitule = row['Intitulé Compte']
            # Basic check: should not contain replacement characters
            assert '\ufffd' not in intitule, "Special characters must not be corrupted"
        
    finally:
        # Cleanup
        if os.path.exists(csv_path):
            os.remove(csv_path)


@given(
    numero_note=st_numero_note(),
    calculs=st.lists(st_calcul_data(), min_size=2, max_size=5),
    fichier_balance=st_fichier_balance()
)
@settings(max_examples=50, deadline=None)
def test_property_24_csv_enables_excel_analysis(numero_note, calculs, fichier_balance):
    """
    Property 24 Extension: CSV Format Enables Excel Analysis
    
    The CSV format must be structured to enable common Excel analysis tasks:
    - Filtering by note, libellé, or account
    - Pivot tables on metadata columns
    - Summing amounts by libellé or account
    
    Validates: Requirements 15.6
    """
    # Arrange
    trace_manager = TraceManager(numero_note)
    hash_md5 = hashlib.md5(fichier_balance.encode()).hexdigest()
    
    trace_manager.enregistrer_metadata(fichier_balance, hash_md5)
    
    for calcul in calculs:
        trace_manager.enregistrer_calcul(
            libelle=calcul['libelle'],
            montant=calcul['montant'],
            comptes_sources=calcul['comptes_sources']
        )
    
    # Act
    csv_file = f"temp_trace_excel_analysis_{numero_note}.csv"
    
    try:
        csv_path = trace_manager.exporter_csv(csv_file)
        
        # Assert - Verify CSV structure enables Excel analysis
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f, delimiter=';')
            csv_data = list(reader)
        
        # Analysis 1: Can filter by note number
        notes_in_csv = set(row['Note'] for row in csv_data)
        assert len(notes_in_csv) == 1, "All rows should have same note number for filtering"
        assert numero_note in notes_in_csv
        
        # Analysis 2: Can filter by libellé
        libelles_in_csv = set(row['Libellé Ligne'] for row in csv_data)
        assert len(libelles_in_csv) == len(calculs), "Each calculation should have unique libellé"
        
        # Analysis 3: Can sum amounts by libellé
        # Group by libellé and verify montant is consistent
        from collections import defaultdict
        montants_by_libelle = defaultdict(set)
        
        for row in csv_data:
            libelle = row['Libellé Ligne']
            montant = float(row['Montant'])
            montants_by_libelle[libelle].add(montant)
        
        # Each libellé should have only one montant value (replicated across source accounts)
        for libelle, montants in montants_by_libelle.items():
            assert len(montants) == 1, \
                f"Libellé '{libelle}' should have consistent montant across all source accounts"
        
        # Analysis 4: Can identify source accounts
        comptes_in_csv = [row['Compte Source'] for row in csv_data if row['Compte Source']]
        assert len(comptes_in_csv) > 0, "Must have source accounts for analysis"
        
        # Analysis 5: Metadata columns enable pivot tables
        # Verify all metadata columns are populated
        for row in csv_data:
            assert row['Note'] != "", "Note must be populated for pivot tables"
            assert row['Fichier Balance'] != "", "Balance file must be populated"
            assert row['Hash MD5'] != "", "Hash must be populated"
            assert row['Date Génération'] != "", "Date must be populated"
        
    finally:
        # Cleanup
        if os.path.exists(csv_path):
            os.remove(csv_path)


@given(
    numero_note=st_numero_note(),
    calculs=st.lists(st_calcul_data(), min_size=1, max_size=3),
    fichier_balance=st_fichier_balance()
)
@settings(max_examples=50, deadline=None)
def test_property_24_json_to_csv_round_trip_integrity(numero_note, calculs, fichier_balance):
    """
    Property 24 Extension: JSON to CSV Round-Trip Integrity
    
    Verify that converting from JSON to CSV preserves all essential information
    such that an auditor could reconstruct the calculation from the CSV alone.
    
    Validates: Requirements 15.6
    """
    # Arrange
    trace_manager = TraceManager(numero_note)
    hash_md5 = hashlib.md5(fichier_balance.encode()).hexdigest()
    
    trace_manager.enregistrer_metadata(fichier_balance, hash_md5)
    
    for calcul in calculs:
        trace_manager.enregistrer_calcul(
            libelle=calcul['libelle'],
            montant=calcul['montant'],
            comptes_sources=calcul['comptes_sources']
        )
    
    # Save JSON trace first
    json_file = f"temp_trace_json_{numero_note}.json"
    trace_manager.sauvegarder_trace(json_file)
    
    # Act - Export to CSV
    csv_file = f"temp_trace_csv_{numero_note}.csv"
    
    try:
        csv_path = trace_manager.exporter_csv(csv_file)
        
        # Load JSON trace
        with open(json_file, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        # Load CSV trace
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f, delimiter=';')
            csv_data = list(reader)
        
        # Assert - Verify essential information is preserved
        
        # 1. Metadata integrity
        assert all(row['Note'] == json_data['note'] for row in csv_data)
        assert all(row['Fichier Balance'] == json_data['fichier_balance'] for row in csv_data)
        assert all(row['Hash MD5'] == json_data['hash_md5_balance'] for row in csv_data)
        
        # 2. Calculation count integrity
        json_ligne_count = len(json_data['lignes'])
        csv_libelle_count = len(set(row['Libellé Ligne'] for row in csv_data))
        assert csv_libelle_count == json_ligne_count, \
            "CSV must preserve all calculation lines from JSON"
        
        # 3. Source account count integrity
        json_compte_count = sum(len(ligne['comptes_sources']) for ligne in json_data['lignes'])
        csv_row_count = len(csv_data)
        assert csv_row_count == json_compte_count, \
            "CSV must have one row per source account from JSON"
        
        # 4. Amount integrity
        for ligne in json_data['lignes']:
            libelle = ligne['libelle']
            montant_json = ligne['montant']
            
            # Find corresponding rows in CSV
            csv_rows_for_libelle = [row for row in csv_data if row['Libellé Ligne'] == libelle]
            assert len(csv_rows_for_libelle) > 0, f"Libellé '{libelle}' must be in CSV"
            
            # All rows for this libellé should have the same montant
            for csv_row in csv_rows_for_libelle:
                montant_csv = float(csv_row['Montant'])
                assert abs(montant_csv - montant_json) < 0.01, \
                    "Montant must be preserved in CSV"
        
        # 5. Source account detail integrity
        for ligne in json_data['lignes']:
            libelle = ligne['libelle']
            comptes_json = ligne['comptes_sources']
            
            csv_rows_for_libelle = [row for row in csv_data if row['Libellé Ligne'] == libelle]
            
            # Verify same number of source accounts
            assert len(csv_rows_for_libelle) == len(comptes_json), \
                "CSV must have same number of source accounts as JSON"
            
            # Verify each source account is present (order may differ)
            comptes_csv = [row['Compte Source'] for row in csv_rows_for_libelle]
            comptes_json_nums = [c['compte'] for c in comptes_json]
            
            assert set(comptes_csv) == set(comptes_json_nums), \
                "CSV must contain all source accounts from JSON"
        
    finally:
        # Cleanup
        if os.path.exists(json_file):
            os.remove(json_file)
        if os.path.exists(csv_path):
            os.remove(csv_path)


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
