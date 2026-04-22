"""
Property Test 6: Missing Account Handling

Ce test valide la propriété suivante:
Pour toute racine de compte qui n'existe pas dans une balance, l'Account_Extractor
doit retourner un dictionnaire avec toutes les 6 valeurs définies à 0.0 sans lever
d'exception.

Propriété testée:
- Property 6: Missing Account Handling
- Valide les exigences: Requirements 2.3, 8.1

Auteur: Système de calcul automatique des notes annexes SYSCOHADA
Date: 21 Avril 2026
"""

import pytest
from hypothesis import given, strategies as st, assume
import pandas as pd
import sys
import os

# Ajouter le chemin du module parent
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Modules'))

from account_extractor import AccountExtractor

# Importer les stratégies depuis conftest (pytest les charge automatiquement)
# Mais pour l'exécution standalone, on les importe explicitement
try:
    from .conftest import st_balance, st_compte_racine
except ImportError:
    # Si l'import relatif échoue, essayer l'import absolu
    import conftest
    st_balance = conftest.st_balance
    st_compte_racine = conftest.st_compte_racine


# ============================================================================
# PROPERTY TEST 6: MISSING ACCOUNT HANDLING
# ============================================================================

@given(balance=st_balance(), racine_inexistante=st_compte_racine())
def test_property_missing_account_returns_zeros(balance, racine_inexistante):
    """
    Property 6: Missing Account Handling
    
    Pour toute racine de compte qui n'existe pas dans la balance,
    extraire_solde_compte() doit retourner un dictionnaire avec
    toutes les valeurs à 0.0 sans lever d'exception.
    
    Valide: Requirements 2.3, 8.1
    """
    # S'assurer que la racine n'existe pas dans la balance
    balance_copy = balance.copy()
    balance_copy['Numéro'] = balance_copy['Numéro'].astype(str).str.strip()
    
    # Filtrer pour s'assurer que la racine n'existe pas
    comptes_existants = balance_copy[balance_copy['Numéro'].str.startswith(racine_inexistante)]
    assume(comptes_existants.empty)
    
    # Créer l'extracteur
    extractor = AccountExtractor(balance)
    
    # Extraire le compte inexistant (ne doit pas lever d'exception)
    try:
        soldes = extractor.extraire_solde_compte(racine_inexistante)
    except Exception as e:
        pytest.fail(f"extraire_solde_compte() a levé une exception pour un compte inexistant: {e}")
    
    # Vérifier que le résultat est un dictionnaire
    assert isinstance(soldes, dict), \
        "extraire_solde_compte() doit retourner un dictionnaire"
    
    # Vérifier que toutes les clés attendues sont présentes
    cles_attendues = {'ant_debit', 'ant_credit', 'mvt_debit', 'mvt_credit', 'solde_debit', 'solde_credit'}
    assert set(soldes.keys()) == cles_attendues, \
        f"Le dictionnaire doit contenir exactement les clés {cles_attendues}"
    
    # Vérifier que toutes les valeurs sont 0.0
    for cle, valeur in soldes.items():
        assert valeur == 0.0, \
            f"Pour un compte inexistant, {cle} doit être 0.0, mais vaut {valeur}"
    
    # Vérifier que les valeurs sont de type float
    for cle, valeur in soldes.items():
        assert isinstance(valeur, float), \
            f"La valeur de {cle} doit être de type float, mais est de type {type(valeur)}"


@given(balance=st_balance())
def test_property_multiple_missing_accounts_returns_zeros(balance):
    """
    Property 6 (Extension): Missing Multiple Accounts Handling
    
    Pour toute liste de racines de comptes inexistantes,
    extraire_comptes_multiples() doit retourner un dictionnaire
    avec toutes les valeurs à 0.0 sans lever d'exception.
    
    Valide: Requirements 2.3, 8.1
    """
    # Générer des racines inexistantes
    racines_inexistantes = ["999", "998", "997"]
    
    # S'assurer qu'aucune de ces racines n'existe
    balance_copy = balance.copy()
    balance_copy['Numéro'] = balance_copy['Numéro'].astype(str).str.strip()
    
    for racine in racines_inexistantes:
        comptes_existants = balance_copy[balance_copy['Numéro'].str.startswith(racine)]
        assume(comptes_existants.empty)
    
    # Créer l'extracteur
    extractor = AccountExtractor(balance)
    
    # Extraire les comptes inexistants (ne doit pas lever d'exception)
    try:
        soldes = extractor.extraire_comptes_multiples(racines_inexistantes)
    except Exception as e:
        pytest.fail(f"extraire_comptes_multiples() a levé une exception pour des comptes inexistants: {e}")
    
    # Vérifier que le résultat est un dictionnaire
    assert isinstance(soldes, dict), \
        "extraire_comptes_multiples() doit retourner un dictionnaire"
    
    # Vérifier que toutes les clés attendues sont présentes
    cles_attendues = {'ant_debit', 'ant_credit', 'mvt_debit', 'mvt_credit', 'solde_debit', 'solde_credit'}
    assert set(soldes.keys()) == cles_attendues, \
        f"Le dictionnaire doit contenir exactement les clés {cles_attendues}"
    
    # Vérifier que toutes les valeurs sont 0.0
    for cle, valeur in soldes.items():
        assert valeur == 0.0, \
            f"Pour des comptes inexistants, {cle} doit être 0.0, mais vaut {valeur}"


@given(balance=st_balance())
def test_property_mixed_existing_and_missing_accounts(balance):
    """
    Property 6 (Extension): Mixed Existing and Missing Accounts
    
    Lorsqu'on extrait plusieurs comptes dont certains existent et d'autres non,
    le résultat doit être la somme des comptes existants (les comptes inexistants
    contribuent 0.0 à la somme).
    
    Valide: Requirements 2.3, 8.1
    """
    balance_copy = balance.copy()
    balance_copy['Numéro'] = balance_copy['Numéro'].astype(str).str.strip()
    
    # Prendre le premier compte existant dans la balance
    assume(len(balance_copy) > 0)
    premier_compte = balance_copy.iloc[0]['Numéro']
    racine_existante = premier_compte[:2]  # Prendre les 2 premiers chiffres
    
    # Utiliser une racine qui n'existe certainement pas
    racine_inexistante = "999"
    
    # Vérifier que la racine inexistante n'existe vraiment pas
    comptes_inexistants = balance_copy[balance_copy['Numéro'].str.startswith(racine_inexistante)]
    assume(comptes_inexistants.empty)
    
    # Créer l'extracteur
    extractor = AccountExtractor(balance)
    
    # Extraire le compte existant seul
    soldes_existant = extractor.extraire_solde_compte(racine_existante)
    
    # Extraire les deux comptes ensemble (existant + inexistant)
    soldes_mixtes = extractor.extraire_comptes_multiples([racine_existante, racine_inexistante])
    
    # Les résultats doivent être identiques (le compte inexistant contribue 0.0)
    for cle in soldes_existant.keys():
        assert abs(soldes_mixtes[cle] - soldes_existant[cle]) < 0.01, \
            f"Pour {cle}, l'ajout d'un compte inexistant ne doit pas changer le résultat: " \
            f"existant={soldes_existant[cle]}, mixte={soldes_mixtes[cle]}"


# ============================================================================
# UNIT TESTS COMPLÉMENTAIRES
# ============================================================================

def test_missing_account_with_simple_balance(balance_simple):
    """
    Test unitaire: Compte inexistant avec balance simple.
    
    Vérifie qu'un compte inexistant retourne bien des zéros
    avec une balance simple et connue.
    """
    extractor = AccountExtractor(balance_simple)
    
    # Extraire un compte qui n'existe pas
    soldes = extractor.extraire_solde_compte("999")
    
    # Vérifier que toutes les valeurs sont 0.0
    assert soldes['ant_debit'] == 0.0
    assert soldes['ant_credit'] == 0.0
    assert soldes['mvt_debit'] == 0.0
    assert soldes['mvt_credit'] == 0.0
    assert soldes['solde_debit'] == 0.0
    assert soldes['solde_credit'] == 0.0


def test_missing_account_empty_string(balance_simple):
    """
    Test unitaire: Racine vide.
    
    Vérifie le comportement avec une chaîne vide comme racine.
    """
    extractor = AccountExtractor(balance_simple)
    
    # Extraire avec une chaîne vide (ne devrait pas lever d'exception)
    soldes = extractor.extraire_solde_compte("")
    
    # Le résultat dépend de l'implémentation, mais ne doit pas crasher
    assert isinstance(soldes, dict)
    assert all(isinstance(v, float) for v in soldes.values())


def test_missing_account_special_characters(balance_simple):
    """
    Test unitaire: Caractères spéciaux.
    
    Vérifie le comportement avec des caractères spéciaux dans la racine.
    """
    extractor = AccountExtractor(balance_simple)
    
    # Extraire avec des caractères spéciaux
    racines_speciales = ["@@@", "***", "---", "   "]
    
    for racine in racines_speciales:
        soldes = extractor.extraire_solde_compte(racine)
        
        # Ne doit pas crasher et doit retourner un dictionnaire valide
        assert isinstance(soldes, dict)
        assert all(isinstance(v, float) for v in soldes.values())


def test_missing_accounts_empty_list(balance_simple):
    """
    Test unitaire: Liste vide de racines.
    
    Vérifie le comportement avec une liste vide de racines.
    """
    extractor = AccountExtractor(balance_simple)
    
    # Extraire avec une liste vide
    soldes = extractor.extraire_comptes_multiples([])
    
    # Doit retourner des zéros
    assert soldes['ant_debit'] == 0.0
    assert soldes['ant_credit'] == 0.0
    assert soldes['mvt_debit'] == 0.0
    assert soldes['mvt_credit'] == 0.0
    assert soldes['solde_debit'] == 0.0
    assert soldes['solde_credit'] == 0.0


def test_missing_account_case_sensitivity(balance_simple):
    """
    Test unitaire: Sensibilité à la casse.
    
    Vérifie que la recherche de compte n'est pas sensible à la casse
    (les numéros de compte sont numériques).
    """
    extractor = AccountExtractor(balance_simple)
    
    # Les numéros de compte sont numériques, donc pas de problème de casse
    # Mais on teste quand même avec des lettres pour vérifier la robustesse
    soldes = extractor.extraire_solde_compte("ABC")
    
    # Doit retourner des zéros (aucun compte ne commence par "ABC")
    assert all(v == 0.0 for v in soldes.values())


# ============================================================================
# TESTS DE RÉGRESSION
# ============================================================================

def test_regression_missing_account_does_not_modify_balance(balance_simple):
    """
    Test de régression: Vérifier que l'extraction d'un compte inexistant
    ne modifie pas la balance originale.
    """
    extractor = AccountExtractor(balance_simple)
    
    # Copier la balance originale
    balance_avant = balance_simple.copy()
    
    # Extraire un compte inexistant
    extractor.extraire_solde_compte("999")
    
    # Vérifier que la balance n'a pas été modifiée
    pd.testing.assert_frame_equal(balance_simple, balance_avant)


def test_regression_missing_account_consistent_results(balance_simple):
    """
    Test de régression: Vérifier que l'extraction d'un compte inexistant
    retourne toujours le même résultat (idempotence).
    """
    extractor = AccountExtractor(balance_simple)
    
    # Extraire le même compte inexistant plusieurs fois
    soldes1 = extractor.extraire_solde_compte("999")
    soldes2 = extractor.extraire_solde_compte("999")
    soldes3 = extractor.extraire_solde_compte("999")
    
    # Les résultats doivent être identiques
    assert soldes1 == soldes2 == soldes3


if __name__ == "__main__":
    # Exécuter les tests avec pytest
    pytest.main([__file__, "-v", "--tb=short"])
