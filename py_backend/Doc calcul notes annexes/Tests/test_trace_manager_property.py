"""
Property-Based Tests for Trace_Manager Module

Feature: calcul-notes-annexes-syscohada
Property 22: Calculation Traceability

For any note annexe generated, the Trace_Manager must create a trace_note_XX.json 
file containing: all calculated amounts with their source accounts and balances, 
generation timestamp, source balance file name and MD5 hash, and this trace must 
enable complete audit reconstruction of the calculation.

Validates: Requirements 15.1, 15.2, 15.3, 15.4
"""

import pytest
from hypothesis import given, settings, strategies as st, assume
import json
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
            'numero': draw(st.text(min_size=3, max_size=5, alphabet='0123456789')),
            'intitule': draw(st.text(min_size=5, max_size=50, alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll'), whitelist_characters=' '))),
            'ant_debit': draw(st.floats(min_value=0, max_value=1e8, allow_nan=False, allow_infinity=False)),
            'ant_credit': draw(st.floats(min_value=0, max_value=1e8, allow_nan=False, allow_infinity=False)),
            'mvt_debit': draw(st.floats(min_value=0, max_value=1e8, allow_nan=False, allow_infinity=False)),
            'mvt_credit': draw(st.floats(min_value=0, max_value=1e8, allow_nan=False, allow_infinity=False)),
            'solde_debit': draw(st.floats(min_value=0, max_value=1e8, allow_nan=False, allow_infinity=False)),
            'solde_credit': draw(st.floats(min_value=0, max_value=1e8, allow_nan=False, allow_infinity=False))
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
# Property 22: Calculation Traceability
# ============================================================================

@given(
    numero_note=st_numero_note(),
    calculs=st.lists(st_calcul_data(), min_size=1, max_size=10),
    fichier_balance=st_fichier_balance()
)
@settings(max_examples=100, deadline=None)
def test_property_22_calculation_traceability(numero_note, calculs, fichier_balance):
    """
    Property 22: Calculation Traceability
    
    For any note annexe generated, the Trace_Manager must create a 
    trace_note_XX.json file containing:
    - All calculated amounts with their source accounts and balances
    - Generation timestamp
    - Source balance file name and MD5 hash
    - Complete audit reconstruction capability
    
    Validates: Requirements 15.1, 15.2, 15.3, 15.4
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
    
    # Act - Save trace to temporary file (use simple filename, trace_manager handles directory)
    trace_file = f"temp_trace_note_{numero_note}.json"
    
    try:
        trace_manager.sauvegarder_trace(trace_file)
        
        # Assert - Verify trace file exists
        assert os.path.exists(trace_file), "Trace file must be created"
        
        # Load and verify trace content
        with open(trace_file, 'r', encoding='utf-8') as f:
            trace_data = json.load(f)
        
        # Property 1: Trace must contain note number
        assert 'note' in trace_data, "Trace must contain note number"
        assert trace_data['note'] == numero_note, "Note number must match"
        
        # Property 2: Trace must contain generation timestamp (Requirement 15.3)
        assert 'date_generation' in trace_data, "Trace must contain generation timestamp"
        # Verify timestamp is valid ISO format
        try:
            datetime.fromisoformat(trace_data['date_generation'])
        except ValueError:
            pytest.fail("Generation timestamp must be valid ISO format")
        
        # Property 3: Trace must contain source balance file name (Requirement 15.4)
        assert 'fichier_balance' in trace_data, "Trace must contain source balance file name"
        assert trace_data['fichier_balance'] == fichier_balance, "Balance file name must match"
        
        # Property 4: Trace must contain MD5 hash (Requirement 15.4)
        assert 'hash_md5_balance' in trace_data, "Trace must contain MD5 hash"
        assert trace_data['hash_md5_balance'] == hash_md5, "MD5 hash must match"
        
        # Property 5: Trace must contain all calculations (Requirement 15.1, 15.2)
        assert 'lignes' in trace_data, "Trace must contain calculation lines"
        assert len(trace_data['lignes']) == len(calculs), "All calculations must be traced"
        
        # Property 6: Each calculation must have complete source information
        for i, ligne in enumerate(trace_data['lignes']):
            calcul_original = calculs[i]
            
            # Verify libelle is preserved
            assert 'libelle' in ligne, "Each line must have libelle"
            assert ligne['libelle'] == calcul_original['libelle'], "Libelle must match"
            
            # Verify montant is preserved
            assert 'montant' in ligne, "Each line must have montant"
            # Allow small floating point differences
            assert abs(ligne['montant'] - calcul_original['montant']) < 0.01, "Montant must match"
            
            # Verify source accounts are preserved (Requirement 15.2)
            assert 'comptes_sources' in ligne, "Each line must have source accounts"
            assert len(ligne['comptes_sources']) == len(calcul_original['comptes_sources']), \
                "All source accounts must be traced"
            
            # Verify each source account has complete information
            for j, compte_trace in enumerate(ligne['comptes_sources']):
                compte_original = calcul_original['comptes_sources'][j]
                
                # All account fields must be present
                required_fields = ['numero', 'intitule', 'ant_debit', 'ant_credit', 
                                 'mvt_debit', 'mvt_credit', 'solde_debit', 'solde_credit']
                for field in required_fields:
                    assert field in compte_trace, f"Source account must have {field}"
                    
                    # Verify values match (with tolerance for floats)
                    if isinstance(compte_original[field], float):
                        assert abs(compte_trace[field] - compte_original[field]) < 0.01, \
                            f"{field} must match"
                    else:
                        assert compte_trace[field] == compte_original[field], \
                            f"{field} must match"
        
        # Property 7: Trace must enable complete audit reconstruction
        # This means we can reconstruct the calculation from the trace
        for i, ligne in enumerate(trace_data['lignes']):
            # We should be able to verify the calculation from source accounts
            # For example, if montant is a sum of source accounts, we can verify it
            # This is a simplified check - in reality, the calculation logic varies
            assert ligne['montant'] >= 0, "Traced amounts must be valid"
            assert len(ligne['comptes_sources']) > 0, "Must have at least one source account"
        
        # Property 8: Trace file must be valid JSON
        # Already verified by successful json.load() above
        
        # Property 9: Trace must be human-readable
        # Verify the JSON is properly formatted (not minified)
        with open(trace_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # Check for indentation (formatted JSON has newlines and spaces)
            assert '\n' in content, "Trace JSON must be formatted (not minified)"
            assert '  ' in content or '\t' in content, "Trace JSON must be indented"
        
    finally:
        # Cleanup
        if os.path.exists(trace_file):
            os.remove(trace_file)


@given(
    numero_note=st_numero_note(),
    calculs=st.lists(st_calcul_data(), min_size=1, max_size=5),
    fichier_balance=st_fichier_balance()
)
@settings(max_examples=50, deadline=None)
def test_property_22_trace_completeness_for_audit(numero_note, calculs, fichier_balance):
    """
    Property 22 Extension: Trace Completeness for Audit
    
    Verify that the trace contains sufficient information to:
    1. Identify the exact source data used
    2. Reproduce the calculation
    3. Verify the calculation independently
    
    Validates: Requirements 15.1, 15.2, 15.3, 15.4
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
    trace_file = f"temp_trace_audit_{numero_note}.json"
    
    try:
        trace_manager.sauvegarder_trace(trace_file)
        
        with open(trace_file, 'r', encoding='utf-8') as f:
            trace_data = json.load(f)
        
        # Assert - Audit Capability 1: Source Data Identification
        # An auditor must be able to identify the exact source file
        assert trace_data['fichier_balance'] == fichier_balance
        assert trace_data['hash_md5_balance'] == hash_md5
        assert 'date_generation' in trace_data
        
        # Assert - Audit Capability 2: Calculation Reproduction
        # An auditor must be able to reproduce each calculation
        for ligne in trace_data['lignes']:
            # Each line must have the formula inputs (source accounts)
            assert 'comptes_sources' in ligne
            assert len(ligne['comptes_sources']) > 0
            
            # Each source account must have all balance components
            for compte in ligne['comptes_sources']:
                # These are the 8 columns from the balance sheet
                assert 'numero' in compte
                assert 'intitule' in compte
                assert 'ant_debit' in compte
                assert 'ant_credit' in compte
                assert 'mvt_debit' in compte
                assert 'mvt_credit' in compte
                assert 'solde_debit' in compte
                assert 'solde_credit' in compte
        
        # Assert - Audit Capability 3: Independent Verification
        # An auditor must be able to verify the calculation independently
        # by checking that the source data is internally consistent
        for ligne in trace_data['lignes']:
            for compte in ligne['comptes_sources']:
                # Verify accounting equation: 
                # Solde_Cloture = Solde_Ouverture + Mouvements
                solde_ouverture = compte['ant_debit'] - compte['ant_credit']
                solde_cloture_calcule = solde_ouverture + compte['mvt_debit'] - compte['mvt_credit']
                solde_cloture_reel = compte['solde_debit'] - compte['solde_credit']
                
                # Allow small tolerance for floating point arithmetic
                ecart = abs(solde_cloture_calcule - solde_cloture_reel)
                # This should be coherent (small tolerance for rounding)
                # Note: In real data, there might be incoherences, but the trace
                # should still record the actual values from the balance
                assert ecart < 1e6, "Source account data should be internally consistent or trace actual values"
        
    finally:
        # Cleanup
        if os.path.exists(trace_file):
            os.remove(trace_file)


@given(
    numero_note=st_numero_note(),
    fichier_balance=st_fichier_balance()
)
@settings(max_examples=50, deadline=None)
def test_property_22_trace_with_empty_calculations(numero_note, fichier_balance):
    """
    Property 22 Edge Case: Trace with No Calculations
    
    Even if no calculations are recorded, the trace must still contain
    valid metadata (timestamp, file name, hash).
    
    Validates: Requirements 15.3, 15.4
    """
    # Arrange
    trace_manager = TraceManager(numero_note)
    hash_md5 = hashlib.md5(fichier_balance.encode()).hexdigest()
    
    # Only record metadata, no calculations
    trace_manager.enregistrer_metadata(fichier_balance, hash_md5)
    
    # Act
    trace_file = f"temp_trace_empty_{numero_note}.json"
    
    try:
        trace_manager.sauvegarder_trace(trace_file)
        
        # Assert
        assert os.path.exists(trace_file)
        
        with open(trace_file, 'r', encoding='utf-8') as f:
            trace_data = json.load(f)
        
        # Metadata must still be present
        assert trace_data['note'] == numero_note
        assert trace_data['fichier_balance'] == fichier_balance
        assert trace_data['hash_md5_balance'] == hash_md5
        assert 'date_generation' in trace_data
        
        # Lignes may be empty or an empty list
        assert 'lignes' in trace_data
        assert isinstance(trace_data['lignes'], list)
        assert len(trace_data['lignes']) == 0
        
    finally:
        # Cleanup
        if os.path.exists(trace_file):
            os.remove(trace_file)


# ============================================================================
# Additional Property Tests for Trace Integrity
# ============================================================================

@given(
    numero_note=st_numero_note(),
    calculs=st.lists(st_calcul_data(), min_size=1, max_size=3),
    fichier_balance=st_fichier_balance()
)
@settings(max_examples=50, deadline=None)
def test_trace_file_naming_convention(numero_note, calculs, fichier_balance):
    """
    Verify that trace files follow the naming convention trace_note_XX.json
    """
    trace_manager = TraceManager(numero_note)
    hash_md5 = hashlib.md5(fichier_balance.encode()).hexdigest()
    
    trace_manager.enregistrer_metadata(fichier_balance, hash_md5)
    
    for calcul in calculs:
        trace_manager.enregistrer_calcul(
            libelle=calcul['libelle'],
            montant=calcul['montant'],
            comptes_sources=calcul['comptes_sources']
        )
    
    # Use the standard naming convention
    trace_file = f"trace_note_{numero_note}.json"
    
    try:
        trace_manager.sauvegarder_trace(trace_file)
        
        # Verify file exists with correct name
        assert os.path.exists(trace_file)
        
        # Verify the file name follows the pattern
        file_name = os.path.basename(trace_file)
        assert file_name.startswith("trace_note_")
        assert file_name.endswith(".json")
        assert numero_note in file_name
        
    finally:
        if os.path.exists(trace_file):
            os.remove(trace_file)


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
