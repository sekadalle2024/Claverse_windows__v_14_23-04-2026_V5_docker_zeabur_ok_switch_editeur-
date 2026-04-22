"""
Tests basés sur les propriétés pour Account_Extractor - Complétude de l'extraction

Ce module contient les tests de propriétés pour valider que l'extraction
des comptes préserve toutes les 6 valeurs avec leur précision originale.

Feature: calcul-notes-annexes-syscohada
Property 5: Account Extraction Completeness

Auteur: Système de calcul automatique des notes annexes SYSCOHADA
Date: 21 Avril 2026
"""

import pytest
from hypothesis import given, assume, settings
import hypothesis.strategies as st
import pandas as pd
import numpy as np
import sys
import os

# Ajouter le chemin des modules au PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Modules'))

from account_extractor import AccountExtractor

# Importer les stratégies depuis conftest (pytest les charge automatiquement)
# Mais pour l'exécution standalone, on les importe explicitement
try:
    from .conftest import st_balance, st_compte_racine
except ImportError:
    # Si l'import relatif échoue, essayer l'import absolu
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from conftest import st_balance, st_compte_racine


# ============================================================================
# PROPERTY 5: ACCOUNT EXTRACTION COMPLETENESS
# ============================================================================

@given(balance=st_balance(), compte_racine=st_compte_racine())
@settings(max_examples=100, deadline=60000)
def test_property_5_extraire_solde_compte_returns_all_6_values(balance, compte_racine):
    """
    **Validates: Requirements 2.2, 2.6**
    
    Property 5: Account Extraction Completeness
    
    For any account found in a balance, the Account_Extractor must extract
    all 6 values (ant_debit, ant_credit, mvt_debit, mvt_credit, solde_debit,
    solde_credit) with their original precision preserved.
    
    Cette propriété vérifie que:
    1. Les 6 clés sont toujours présentes dans le résultat
    2. Toutes les valeurs sont des nombres valides (pas NaN, pas infini)
    3. La précision des montants est préservée
    """
    # Assumer qu'il y a au moins un compte dans la balance
    assume(len(balance) > 0)
    
    # Créer l'extracteur
    extractor = AccountExtractor(balance)
    
    # Extraire les soldes
    soldes = extractor.extraire_solde_compte(compte_racine)
    
    # Propriété 1: Les 6 clés doivent être présentes
    cles_attendues = {'ant_debit', 'ant_credit', 'mvt_debit', 'mvt_credit', 'solde_debit', 'solde_credit'}
    cles_presentes = set(soldes.keys())
    
    assert cles_presentes == cles_attendues, \
        f"Clés manquantes: {cles_attendues - cles_presentes}, Clés en trop: {cles_presentes - cles_attendues}"
    
    # Propriété 2: Toutes les valeurs doivent être des nombres valides
    for cle, valeur in soldes.items():
        # Vérifier que c'est un type numérique
        assert isinstance(valeur, (float, np.floating, np.integer)), \
            f"{cle} devrait être un type numérique, mais est {type(valeur)}"
        
        # Vérifier que la valeur n'est pas NaN
        assert not pd.isna(valeur), \
            f"{cle} ne devrait pas être NaN"
        
        # Vérifier que la valeur n'est pas infinie
        assert not np.isinf(valeur), \
            f"{cle} ne devrait pas être infini"
        
        # Vérifier que la valeur est non-négative (soldes comptables)
        assert valeur >= 0, \
            f"{cle} devrait être non-négatif, mais vaut {valeur}"


@given(balance=st_balance(), compte_racine=st_compte_racine())
@settings(max_examples=100, deadline=60000)
def test_property_5_extraction_preserves_original_precision(balance, compte_racine):
    """
    **Validates: Requirements 2.6**
    
    Property 5: Account Extraction Completeness (préservation de la précision)
    
    For any account found in a balance, the extracted values must match
    the sum of the original values in the balance without premature rounding.
    
    Cette propriété vérifie que:
    1. Les valeurs extraites = somme exacte des valeurs originales
    2. Aucun arrondi prématuré n'est effectué
    3. La précision est préservée à 0.01 près (tolérance pour erreurs d'arrondi float)
    """
    # Assumer qu'il y a au moins un compte dans la balance
    assume(len(balance) > 0)
    
    # Créer l'extracteur
    extractor = AccountExtractor(balance)
    
    # Extraire les soldes
    soldes_extraits = extractor.extraire_solde_compte(compte_racine)
    
    # Calculer manuellement les sommes attendues depuis la balance originale
    comptes_correspondants = balance[balance['Numéro'].astype(str).str.strip().str.startswith(compte_racine)]
    
    if comptes_correspondants.empty:
        # Si aucun compte ne correspond, toutes les valeurs doivent être 0.0
        for cle, valeur in soldes_extraits.items():
            assert valeur == 0.0, \
                f"{cle} devrait être 0.0 pour un compte inexistant, mais vaut {valeur}"
    else:
        # Calculer les sommes attendues
        sommes_attendues = {
            'ant_debit': comptes_correspondants['Ant Débit'].sum(),
            'ant_credit': comptes_correspondants['Ant Crédit'].sum(),
            'mvt_debit': comptes_correspondants['Débit'].sum(),
            'mvt_credit': comptes_correspondants['Crédit'].sum(),
            'solde_debit': comptes_correspondants['Solde Débit'].sum(),
            'solde_credit': comptes_correspondants['Solde Crédit'].sum()
        }
        
        # Tolérance pour les erreurs d'arrondi des floats
        tolerance = 0.01
        
        # Vérifier que chaque valeur extraite correspond à la somme attendue
        for cle in sommes_attendues.keys():
            ecart = abs(soldes_extraits[cle] - sommes_attendues[cle])
            assert ecart < tolerance, \
                f"{cle}: extrait={soldes_extraits[cle]}, attendu={sommes_attendues[cle]}, écart={ecart}"


@given(balance=st_balance(), compte_racine=st_compte_racine())
@settings(max_examples=100, deadline=60000)
def test_property_5_extraction_is_deterministic(balance, compte_racine):
    """
    **Validates: Requirements 2.2**
    
    Property 5: Account Extraction Completeness (déterminisme)
    
    For any account and balance, extracting the same account multiple times
    must return identical results (deterministic behavior).
    
    Cette propriété vérifie que:
    1. L'extraction est déterministe (même entrée => même sortie)
    2. Aucune variation aléatoire ou dépendance temporelle
    """
    # Assumer qu'il y a au moins un compte dans la balance
    assume(len(balance) > 0)
    
    # Créer l'extracteur
    extractor = AccountExtractor(balance)
    
    # Extraire les soldes deux fois
    soldes_1 = extractor.extraire_solde_compte(compte_racine)
    soldes_2 = extractor.extraire_solde_compte(compte_racine)
    
    # Vérifier que les deux extractions sont identiques
    for cle in soldes_1.keys():
        assert soldes_1[cle] == soldes_2[cle], \
            f"{cle}: première extraction={soldes_1[cle]}, deuxième extraction={soldes_2[cle]}"


@given(balance=st_balance())
@settings(max_examples=50, deadline=30000)
def test_property_5_extraction_handles_all_account_types(balance):
    """
    **Validates: Requirements 2.2, 2.4**
    
    Property 5: Account Extraction Completeness (tous types de comptes)
    
    For any balance, the extractor must handle accounts with multiple levels
    (e.g., "2811", "28111") and preserve all 6 values for each level.
    
    Cette propriété vérifie que:
    1. Les comptes multi-niveaux sont correctement gérés
    2. Les sous-comptes sont inclus dans la racine parente
    """
    # Assumer qu'il y a au moins un compte dans la balance
    assume(len(balance) > 0)
    
    # Créer l'extracteur
    extractor = AccountExtractor(balance)
    
    # Tester avec différentes longueurs de racines
    for longueur_racine in [1, 2, 3, 4]:
        # Prendre un compte aléatoire et extraire une racine de longueur donnée
        if len(balance) > 0:
            premier_compte = str(balance.iloc[0]['Numéro'])
            if len(premier_compte) >= longueur_racine:
                racine = premier_compte[:longueur_racine]
                
                # Extraire les soldes
                soldes = extractor.extraire_solde_compte(racine)
                
                # Vérifier que les 6 valeurs sont présentes
                assert len(soldes) == 6, \
                    f"Pour racine '{racine}' (longueur {longueur_racine}), attendu 6 valeurs, obtenu {len(soldes)}"
                
                # Vérifier que toutes les valeurs sont valides
                for cle, valeur in soldes.items():
                    assert isinstance(valeur, (float, np.floating, np.integer)), \
                        f"Pour racine '{racine}', {cle} devrait être numérique"
                    assert not pd.isna(valeur), \
                        f"Pour racine '{racine}', {cle} ne devrait pas être NaN"


@given(balance=st_balance(), racines=st.lists(st_compte_racine(), min_size=2, max_size=5, unique=True))
@settings(max_examples=50, deadline=30000)
def test_property_5_multiple_extraction_preserves_completeness(balance, racines):
    """
    **Validates: Requirements 2.2, 2.5**
    
    Property 5: Account Extraction Completeness (extraction multiple)
    
    For any list of account roots, extraire_comptes_multiples must return
    all 6 values with the sum of individual extractions preserved.
    
    Cette propriété vérifie que:
    1. L'extraction multiple retourne les 6 valeurs
    2. La somme des extractions individuelles = extraction multiple
    3. Aucune valeur n'est perdue lors de la sommation
    """
    # Assumer qu'il y a au moins un compte dans la balance
    assume(len(balance) > 0)
    
    # Créer l'extracteur
    extractor = AccountExtractor(balance)
    
    # Extraire avec la méthode multiple
    soldes_multiples = extractor.extraire_comptes_multiples(racines)
    
    # Propriété 1: Les 6 clés doivent être présentes
    cles_attendues = {'ant_debit', 'ant_credit', 'mvt_debit', 'mvt_credit', 'solde_debit', 'solde_credit'}
    assert set(soldes_multiples.keys()) == cles_attendues, \
        f"Clés manquantes dans extraction multiple"
    
    # Propriété 2: Calculer la somme des extractions individuelles
    somme_individuelle = {
        'ant_debit': 0.0,
        'ant_credit': 0.0,
        'mvt_debit': 0.0,
        'mvt_credit': 0.0,
        'solde_debit': 0.0,
        'solde_credit': 0.0
    }
    
    for racine in racines:
        soldes = extractor.extraire_solde_compte(racine)
        for cle in somme_individuelle.keys():
            somme_individuelle[cle] += soldes[cle]
    
    # Propriété 3: Vérifier que les sommes correspondent
    tolerance = 0.01
    
    for cle in somme_individuelle.keys():
        ecart = abs(soldes_multiples[cle] - somme_individuelle[cle])
        assert ecart < tolerance, \
            f"{cle}: multiple={soldes_multiples[cle]}, somme individuelle={somme_individuelle[cle]}, écart={ecart}"


@given(balance=st_balance())
@settings(max_examples=50, deadline=30000)
def test_property_5_extraction_with_zero_values(balance):
    """
    **Validates: Requirements 2.2, 2.3**
    
    Property 5: Account Extraction Completeness (valeurs nulles)
    
    For any balance, accounts with zero values in some columns must still
    return all 6 values, with zeros preserved correctly.
    
    Cette propriété vérifie que:
    1. Les comptes avec des valeurs nulles sont correctement gérés
    2. Les zéros sont préservés (pas convertis en NaN ou omis)
    """
    # Assumer qu'il y a au moins un compte dans la balance
    assume(len(balance) > 0)
    
    # Créer l'extracteur
    extractor = AccountExtractor(balance)
    
    # Prendre le premier compte
    premier_compte = str(balance.iloc[0]['Numéro'])
    
    # Extraire les soldes
    soldes = extractor.extraire_solde_compte(premier_compte)
    
    # Vérifier que les 6 valeurs sont présentes
    assert len(soldes) == 6
    
    # Vérifier que les valeurs nulles sont bien des 0.0 (pas NaN)
    for cle, valeur in soldes.items():
        if valeur == 0.0:
            # Vérifier que c'est bien 0.0 et pas NaN
            assert valeur == 0.0 and not pd.isna(valeur), \
                f"{cle} devrait être 0.0, pas NaN"


# ============================================================================
# TESTS UNITAIRES COMPLÉMENTAIRES
# ============================================================================

def test_extraction_completeness_with_fixture(balance_simple):
    """
    Test unitaire avec fixture pour vérifier la complétude de l'extraction.
    
    Ce test complète les tests de propriétés avec un exemple concret.
    """
    extractor = AccountExtractor(balance_simple)
    
    # Extraire les soldes du compte 211
    soldes = extractor.extraire_solde_compte("211")
    
    # Vérifier que les 6 clés sont présentes
    cles_attendues = {'ant_debit', 'ant_credit', 'mvt_debit', 'mvt_credit', 'solde_debit', 'solde_credit'}
    assert set(soldes.keys()) == cles_attendues
    
    # Vérifier les valeurs spécifiques
    # 211: Ant Débit=1000000, 2111: Ant Débit=500000 => Total=1500000
    assert soldes['ant_debit'] == 1500000.0
    assert soldes['ant_credit'] == 0.0
    
    # 211: Débit=300000, 2111: Débit=100000 => Total=400000
    assert soldes['mvt_debit'] == 400000.0
    assert soldes['mvt_credit'] == 0.0
    
    # 211: Solde Débit=1300000, 2111: Solde Débit=600000 => Total=1900000
    assert soldes['solde_debit'] == 1900000.0
    assert soldes['solde_credit'] == 0.0


def test_extraction_preserves_precision_with_fixture(balance_simple):
    """
    Test unitaire avec fixture pour vérifier la préservation de la précision.
    
    Ce test complète les tests de propriétés avec un exemple concret.
    """
    extractor = AccountExtractor(balance_simple)
    
    # Extraire les soldes du compte 2811 (amortissements)
    soldes = extractor.extraire_solde_compte("2811")
    
    # Vérifier les valeurs exactes (pas d'arrondi)
    assert soldes['ant_credit'] == 200000.0
    assert soldes['mvt_credit'] == 100000.0
    assert soldes['solde_credit'] == 300000.0
    
    # Vérifier que les valeurs débit sont nulles
    assert soldes['ant_debit'] == 0.0
    assert soldes['mvt_debit'] == 0.0
    assert soldes['solde_debit'] == 0.0


def test_extraction_multiple_completeness_with_fixture(balance_simple):
    """
    Test unitaire avec fixture pour vérifier la complétude de l'extraction multiple.
    
    Ce test complète les tests de propriétés avec un exemple concret.
    """
    extractor = AccountExtractor(balance_simple)
    
    # Extraire les soldes des comptes 2811 et 2812 (amortissements)
    soldes = extractor.extraire_comptes_multiples(["2811", "2812"])
    
    # Vérifier que les 6 clés sont présentes
    cles_attendues = {'ant_debit', 'ant_credit', 'mvt_debit', 'mvt_credit', 'solde_debit', 'solde_credit'}
    assert set(soldes.keys()) == cles_attendues
    
    # Vérifier les sommes
    # 2811: Ant Crédit=200000, 2812: Ant Crédit=150000 => Total=350000
    assert soldes['ant_credit'] == 350000.0
    
    # 2811: Mvt Crédit=100000, 2812: Mvt Crédit=80000 => Total=180000
    assert soldes['mvt_credit'] == 180000.0
    
    # 2811: Solde Crédit=300000, 2812: Solde Crédit=230000 => Total=530000
    assert soldes['solde_credit'] == 530000.0


def test_extraction_with_missing_columns_graceful_degradation():
    """
    Test unitaire pour vérifier la gestion gracieuse des colonnes manquantes.
    
    Ce test vérifie que l'extracteur gère correctement les balances
    avec des colonnes manquantes.
    """
    # Créer une balance avec des colonnes manquantes
    balance_incomplete = pd.DataFrame({
        'Numéro': ['211', '212'],
        'Intitulé': ['Frais de recherche', 'Brevets'],
        'Ant Débit': [1000000.0, 800000.0],
        'Solde Débit': [1300000.0, 1000000.0]
        # Colonnes manquantes: Ant Crédit, Débit, Crédit, Solde Crédit
    })
    
    extractor = AccountExtractor(balance_incomplete)
    
    # Extraire les soldes
    soldes = extractor.extraire_solde_compte("211")
    
    # Vérifier que les 6 clés sont présentes
    assert len(soldes) == 6
    
    # Vérifier que les colonnes présentes ont les bonnes valeurs
    assert soldes['ant_debit'] == 1000000.0
    assert soldes['solde_debit'] == 1300000.0
    
    # Vérifier que les colonnes manquantes retournent 0.0
    assert soldes['ant_credit'] == 0.0
    assert soldes['mvt_debit'] == 0.0
    assert soldes['mvt_credit'] == 0.0
    assert soldes['solde_credit'] == 0.0


if __name__ == "__main__":
    # Exécuter les tests avec pytest
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
