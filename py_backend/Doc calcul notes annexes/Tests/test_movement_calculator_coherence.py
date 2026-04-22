"""
Test de propriété pour la cohérence de l'équation comptable.

Property 7: Accounting Equation Coherence
Valide les exigences: 3.1, 3.2, 3.3, 3.4, 3.5

Pour tout compte analysé, le Movement_Calculator doit vérifier que:
Solde_Cloture = Solde_Ouverture + Augmentations - Diminutions

Où:
- Solde_Ouverture = (Solde Débit N-1 - Solde Crédit N-1)
- Augmentations = Mouvement Débit N
- Diminutions = Mouvement Crédit N
- Solde_Cloture = (Solde Débit N - Solde Crédit N)
"""

import pytest
from hypothesis import given, assume, strategies as st
from hypothesis import settings
import pandas as pd

from Modules.movement_calculator import MovementCalculator


# ============================================================================
# STRATÉGIES HYPOTHESIS POUR LES TESTS DE COHÉRENCE
# ============================================================================

@st.composite
def st_compte_coherent(draw):
    """
    Génère un compte avec des soldes cohérents.
    
    Cette stratégie garantit que l'équation comptable est respectée:
    Solde_Cloture = Solde_Ouverture + Augmentations - Diminutions
    """
    # Générer les soldes d'ouverture (N-1)
    solde_debit_n1 = draw(st.floats(
        min_value=0,
        max_value=100000000,
        allow_nan=False,
        allow_infinity=False
    ))
    solde_credit_n1 = draw(st.floats(
        min_value=0,
        max_value=100000000,
        allow_nan=False,
        allow_infinity=False
    ))
    
    # Générer les mouvements de l'exercice N
    mvt_debit_n = draw(st.floats(
        min_value=0,
        max_value=50000000,
        allow_nan=False,
        allow_infinity=False
    ))
    mvt_credit_n = draw(st.floats(
        min_value=0,
        max_value=50000000,
        allow_nan=False,
        allow_infinity=False
    ))
    
    # Calculer le solde de clôture cohérent
    solde_ouverture = solde_debit_n1 - solde_credit_n1
    solde_cloture = solde_ouverture + mvt_debit_n - mvt_credit_n
    
    # Convertir en solde débit/crédit
    solde_debit_n = max(0, solde_cloture)
    solde_credit_n = max(0, -solde_cloture)
    
    return {
        'solde_debit_n1': solde_debit_n1,
        'solde_credit_n1': solde_credit_n1,
        'mvt_debit_n': mvt_debit_n,
        'mvt_credit_n': mvt_credit_n,
        'solde_debit_n': solde_debit_n,
        'solde_credit_n': solde_credit_n
    }


@st.composite
def st_compte_incoherent(draw):
    """
    Génère un compte avec des soldes incohérents.
    
    Cette stratégie génère intentionnellement des comptes où
    l'équation comptable n'est PAS respectée.
    """
    # Générer tous les soldes indépendamment
    solde_debit_n1 = draw(st.floats(
        min_value=0,
        max_value=100000000,
        allow_nan=False,
        allow_infinity=False
    ))
    solde_credit_n1 = draw(st.floats(
        min_value=0,
        max_value=100000000,
        allow_nan=False,
        allow_infinity=False
    ))
    mvt_debit_n = draw(st.floats(
        min_value=0,
        max_value=50000000,
        allow_nan=False,
        allow_infinity=False
    ))
    mvt_credit_n = draw(st.floats(
        min_value=0,
        max_value=50000000,
        allow_nan=False,
        allow_infinity=False
    ))
    solde_debit_n = draw(st.floats(
        min_value=0,
        max_value=100000000,
        allow_nan=False,
        allow_infinity=False
    ))
    solde_credit_n = draw(st.floats(
        min_value=0,
        max_value=100000000,
        allow_nan=False,
        allow_infinity=False
    ))
    
    # Vérifier que c'est vraiment incohérent (écart > 1.0)
    solde_ouverture = solde_debit_n1 - solde_credit_n1
    solde_cloture_attendu = solde_ouverture + mvt_debit_n - mvt_credit_n
    solde_cloture_reel = solde_debit_n - solde_credit_n
    ecart = abs(solde_cloture_reel - solde_cloture_attendu)
    
    assume(ecart > 1.0)  # Assurer une incohérence significative
    
    return {
        'solde_debit_n1': solde_debit_n1,
        'solde_credit_n1': solde_credit_n1,
        'mvt_debit_n': mvt_debit_n,
        'mvt_credit_n': mvt_credit_n,
        'solde_debit_n': solde_debit_n,
        'solde_credit_n': solde_credit_n
    }


# ============================================================================
# TESTS DE PROPRIÉTÉ
# ============================================================================

@given(compte=st_compte_coherent())
@settings(max_examples=100, deadline=60000)
def test_property_accounting_equation_coherence_valid(compte):
    """
    Property 7: Accounting Equation Coherence (cas valide).
    
    Pour tout compte avec des soldes cohérents, le Movement_Calculator
    doit valider la cohérence de l'équation comptable.
    
    Valide: Requirements 3.1, 3.2, 3.3, 3.4, 3.5
    """
    calc = MovementCalculator()
    
    # Calculer les composants de l'équation
    solde_ouverture = calc.calculer_solde_ouverture(
        compte['solde_debit_n1'],
        compte['solde_credit_n1']
    )
    
    augmentations = calc.calculer_augmentations(compte['mvt_debit_n'])
    diminutions = calc.calculer_diminutions(compte['mvt_credit_n'])
    
    solde_cloture = calc.calculer_solde_cloture(
        compte['solde_debit_n'],
        compte['solde_credit_n']
    )
    
    # Vérifier la cohérence
    coherent, ecart = calc.verifier_coherence(
        solde_ouverture,
        augmentations,
        diminutions,
        solde_cloture,
        tolerance=0.01
    )
    
    # PROPRIÉTÉ: Pour un compte cohérent, la vérification doit réussir
    assert coherent, (
        f"La cohérence devrait être validée pour un compte cohérent. "
        f"Écart: {ecart:.2f}"
    )
    
    # PROPRIÉTÉ: L'écart doit être négligeable (< 0.01)
    assert ecart < 0.01, (
        f"L'écart devrait être négligeable pour un compte cohérent. "
        f"Écart: {ecart:.2f}"
    )
    
    # PROPRIÉTÉ: L'équation comptable doit être respectée
    solde_calcule = solde_ouverture + augmentations - diminutions
    assert abs(solde_cloture - solde_calcule) < 0.01, (
        f"L'équation comptable doit être respectée: "
        f"Solde clôture={solde_cloture:.2f}, "
        f"Solde calculé={solde_calcule:.2f}"
    )


@given(compte=st_compte_incoherent())
@settings(max_examples=100, deadline=60000)
def test_property_accounting_equation_coherence_invalid(compte):
    """
    Property 7: Accounting Equation Coherence (cas invalide).
    
    Pour tout compte avec des soldes incohérents, le Movement_Calculator
    doit détecter l'incohérence et retourner un écart significatif.
    
    Valide: Requirements 3.5, 3.6
    """
    calc = MovementCalculator()
    
    # Calculer les composants de l'équation
    solde_ouverture = calc.calculer_solde_ouverture(
        compte['solde_debit_n1'],
        compte['solde_credit_n1']
    )
    
    augmentations = calc.calculer_augmentations(compte['mvt_debit_n'])
    diminutions = calc.calculer_diminutions(compte['mvt_credit_n'])
    
    solde_cloture = calc.calculer_solde_cloture(
        compte['solde_debit_n'],
        compte['solde_credit_n']
    )
    
    # Vérifier la cohérence
    coherent, ecart = calc.verifier_coherence(
        solde_ouverture,
        augmentations,
        diminutions,
        solde_cloture,
        tolerance=0.01
    )
    
    # PROPRIÉTÉ: Pour un compte incohérent, la vérification doit échouer
    assert not coherent, (
        f"L'incohérence devrait être détectée. "
        f"Écart: {ecart:.2f}"
    )
    
    # PROPRIÉTÉ: L'écart doit être significatif (> 0.01)
    assert ecart > 0.01, (
        f"L'écart devrait être significatif pour un compte incohérent. "
        f"Écart: {ecart:.2f}"
    )


@given(
    solde_debit_n1=st.floats(min_value=0, max_value=1e8, allow_nan=False, allow_infinity=False),
    solde_credit_n1=st.floats(min_value=0, max_value=1e8, allow_nan=False, allow_infinity=False),
    mvt_debit_n=st.floats(min_value=0, max_value=5e7, allow_nan=False, allow_infinity=False),
    mvt_credit_n=st.floats(min_value=0, max_value=5e7, allow_nan=False, allow_infinity=False)
)
@settings(max_examples=100, deadline=60000)
def test_property_solde_ouverture_formula(solde_debit_n1, solde_credit_n1, 
                                          mvt_debit_n, mvt_credit_n):
    """
    Property: Formule du solde d'ouverture.
    
    Le solde d'ouverture doit toujours être égal à:
    Solde Débit N-1 - Solde Crédit N-1
    
    Valide: Requirement 3.1
    """
    calc = MovementCalculator()
    
    solde_ouverture = calc.calculer_solde_ouverture(solde_debit_n1, solde_credit_n1)
    
    # PROPRIÉTÉ: La formule doit être exacte
    assert solde_ouverture == solde_debit_n1 - solde_credit_n1, (
        f"Solde ouverture incorrect: "
        f"Attendu={solde_debit_n1 - solde_credit_n1:.2f}, "
        f"Obtenu={solde_ouverture:.2f}"
    )


@given(mvt_debit_n=st.floats(min_value=0, max_value=1e8, allow_nan=False, allow_infinity=False))
@settings(max_examples=50, deadline=30000)
def test_property_augmentations_formula(mvt_debit_n):
    """
    Property: Formule des augmentations.
    
    Les augmentations doivent toujours être égales au mouvement débit N.
    
    Valide: Requirement 3.2
    """
    calc = MovementCalculator()
    
    augmentations = calc.calculer_augmentations(mvt_debit_n)
    
    # PROPRIÉTÉ: Les augmentations = Mouvement Débit N
    assert augmentations == mvt_debit_n, (
        f"Augmentations incorrectes: "
        f"Attendu={mvt_debit_n:.2f}, "
        f"Obtenu={augmentations:.2f}"
    )


@given(mvt_credit_n=st.floats(min_value=0, max_value=1e8, allow_nan=False, allow_infinity=False))
@settings(max_examples=50, deadline=30000)
def test_property_diminutions_formula(mvt_credit_n):
    """
    Property: Formule des diminutions.
    
    Les diminutions doivent toujours être égales au mouvement crédit N.
    
    Valide: Requirement 3.3
    """
    calc = MovementCalculator()
    
    diminutions = calc.calculer_diminutions(mvt_credit_n)
    
    # PROPRIÉTÉ: Les diminutions = Mouvement Crédit N
    assert diminutions == mvt_credit_n, (
        f"Diminutions incorrectes: "
        f"Attendu={mvt_credit_n:.2f}, "
        f"Obtenu={diminutions:.2f}"
    )


@given(
    solde_debit_n=st.floats(min_value=0, max_value=1e8, allow_nan=False, allow_infinity=False),
    solde_credit_n=st.floats(min_value=0, max_value=1e8, allow_nan=False, allow_infinity=False)
)
@settings(max_examples=50, deadline=30000)
def test_property_solde_cloture_formula(solde_debit_n, solde_credit_n):
    """
    Property: Formule du solde de clôture.
    
    Le solde de clôture doit toujours être égal à:
    Solde Débit N - Solde Crédit N
    
    Valide: Requirement 3.4
    """
    calc = MovementCalculator()
    
    solde_cloture = calc.calculer_solde_cloture(solde_debit_n, solde_credit_n)
    
    # PROPRIÉTÉ: La formule doit être exacte
    assert solde_cloture == solde_debit_n - solde_credit_n, (
        f"Solde clôture incorrect: "
        f"Attendu={solde_debit_n - solde_credit_n:.2f}, "
        f"Obtenu={solde_cloture:.2f}"
    )


@given(
    tolerance=st.floats(min_value=0.001, max_value=10.0, allow_nan=False, allow_infinity=False)
)
@settings(max_examples=50, deadline=30000)
def test_property_tolerance_parameter(tolerance):
    """
    Property: Paramètre de tolérance.
    
    Le paramètre de tolérance doit être respecté lors de la vérification
    de cohérence.
    
    Valide: Requirement 3.6
    """
    calc = MovementCalculator()
    
    # Créer un compte avec un écart légèrement inférieur à la tolérance
    solde_ouverture = 1000.0
    augmentations = 500.0
    diminutions = 200.0
    # Utiliser 90% de la tolérance pour éviter les problèmes de précision flottante
    ecart_test = tolerance * 0.9
    solde_cloture = solde_ouverture + augmentations - diminutions + ecart_test
    
    coherent, ecart = calc.verifier_coherence(
        solde_ouverture,
        augmentations,
        diminutions,
        solde_cloture,
        tolerance=tolerance
    )
    
    # PROPRIÉTÉ: Un écart inférieur à la tolérance doit être accepté
    assert coherent, (
        f"Un écart inférieur à la tolérance devrait être accepté. "
        f"Écart={ecart:.4f}, Tolérance={tolerance:.4f}"
    )
    
    # Créer un compte avec un écart clairement supérieur à la tolérance
    # Utiliser 150% de la tolérance pour garantir le rejet
    ecart_invalide = tolerance * 1.5
    solde_cloture_invalide = solde_ouverture + augmentations - diminutions + ecart_invalide
    
    coherent_invalide, ecart_reel = calc.verifier_coherence(
        solde_ouverture,
        augmentations,
        diminutions,
        solde_cloture_invalide,
        tolerance=tolerance
    )
    
    # PROPRIÉTÉ: Un écart supérieur à la tolérance doit être rejeté
    assert not coherent_invalide, (
        f"Un écart supérieur à la tolérance devrait être rejeté. "
        f"Écart={ecart_reel:.4f}, Tolérance={tolerance:.4f}"
    )


# ============================================================================
# TESTS UNITAIRES COMPLÉMENTAIRES
# ============================================================================

def test_coherence_compte_simple():
    """Test unitaire avec un compte simple."""
    calc = MovementCalculator()
    
    # Compte simple: 1000 ouverture + 500 augmentation - 200 diminution = 1300 clôture
    solde_ouverture = calc.calculer_solde_ouverture(1000.0, 0.0)
    augmentations = calc.calculer_augmentations(500.0)
    diminutions = calc.calculer_diminutions(200.0)
    solde_cloture = calc.calculer_solde_cloture(1300.0, 0.0)
    
    coherent, ecart = calc.verifier_coherence(
        solde_ouverture,
        augmentations,
        diminutions,
        solde_cloture
    )
    
    assert coherent
    assert ecart < 0.01


def test_coherence_compte_crediteur():
    """Test unitaire avec un compte créditeur."""
    calc = MovementCalculator()
    
    # Compte créditeur: -500 ouverture + 200 augmentation - 300 diminution = -600 clôture
    solde_ouverture = calc.calculer_solde_ouverture(0.0, 500.0)
    augmentations = calc.calculer_augmentations(200.0)
    diminutions = calc.calculer_diminutions(300.0)
    solde_cloture = calc.calculer_solde_cloture(0.0, 600.0)
    
    coherent, ecart = calc.verifier_coherence(
        solde_ouverture,
        augmentations,
        diminutions,
        solde_cloture
    )
    
    assert coherent
    assert ecart < 0.01


def test_incoherence_detectee():
    """Test unitaire avec un compte incohérent."""
    calc = MovementCalculator()
    
    # Compte incohérent: 1000 + 500 - 200 = 1300, mais solde clôture = 1500
    solde_ouverture = calc.calculer_solde_ouverture(1000.0, 0.0)
    augmentations = calc.calculer_augmentations(500.0)
    diminutions = calc.calculer_diminutions(200.0)
    solde_cloture = calc.calculer_solde_cloture(1500.0, 0.0)
    
    coherent, ecart = calc.verifier_coherence(
        solde_ouverture,
        augmentations,
        diminutions,
        solde_cloture
    )
    
    assert not coherent
    assert ecart == 200.0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
