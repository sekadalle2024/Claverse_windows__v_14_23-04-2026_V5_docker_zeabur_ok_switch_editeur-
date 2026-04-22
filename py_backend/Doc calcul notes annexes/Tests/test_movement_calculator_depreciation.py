"""
Test de propriété pour l'inversion des signes des comptes d'amortissement.

Property 8: Depreciation Account Sign Inversion
Valide les exigences: 3.7, 4.4, 4.5

Pour tout compte d'amortissement (comptes commençant par 28 ou 29),
le Movement_Calculator doit traiter les mouvements crédit comme des
augmentations (dotations) et les mouvements débit comme des diminutions
(reprises), ce qui est l'inverse des comptes normaux.
"""

import pytest
from hypothesis import given, assume, strategies as st
from hypothesis import settings
import pandas as pd

from Modules.movement_calculator import MovementCalculator


# ============================================================================
# STRATÉGIES HYPOTHESIS POUR LES COMPTES D'AMORTISSEMENT
# ============================================================================

@st.composite
def st_compte_amortissement(draw):
    """
    Génère un compte d'amortissement valide (28X ou 29X).
    
    Les comptes d'amortissement ont un comportement inversé:
    - Crédit = augmentation de l'amortissement (dotation)
    - Débit = diminution de l'amortissement (reprise)
    """
    # Choisir entre classe 28 (amortissements) ou 29 (provisions)
    classe = draw(st.sampled_from(['28', '29']))
    sous_classe = draw(st.integers(min_value=0, max_value=9))
    detail = draw(st.text(alphabet='0123456789', min_size=0, max_size=2))
    numero = f"{classe}{sous_classe}{detail}"
    
    # Générer les mouvements
    mvt_debit = draw(st.floats(
        min_value=0,
        max_value=5000000,
        allow_nan=False,
        allow_infinity=False
    ))
    mvt_credit = draw(st.floats(
        min_value=0,
        max_value=5000000,
        allow_nan=False,
        allow_infinity=False
    ))
    
    return {
        'numero': numero,
        'mvt_debit': mvt_debit,
        'mvt_credit': mvt_credit
    }


@st.composite
def st_balance_avec_amortissement(draw):
    """
    Génère une balance contenant des comptes d'amortissement.
    
    Cette stratégie crée une balance avec au moins un compte
    d'amortissement (28X ou 29X).
    """
    # Générer le compte d'amortissement principal
    compte_amort = draw(st_compte_amortissement())
    
    # Générer des comptes supplémentaires (optionnel)
    num_comptes_supplementaires = draw(st.integers(min_value=0, max_value=10))
    
    comptes = [{
        'Numéro': compte_amort['numero'],
        'Intitulé': f"Amortissement {compte_amort['numero']}",
        'Ant Débit': 0.0,
        'Ant Crédit': draw(st.floats(min_value=0, max_value=10000000, 
                                     allow_nan=False, allow_infinity=False)),
        'Débit': compte_amort['mvt_debit'],
        'Crédit': compte_amort['mvt_credit'],
        'Solde Débit': 0.0,
        'Solde Crédit': draw(st.floats(min_value=0, max_value=15000000,
                                       allow_nan=False, allow_infinity=False))
    }]
    
    # Ajouter des comptes supplémentaires
    for i in range(num_comptes_supplementaires):
        numero = draw(st.text(alphabet='0123456789', min_size=3, max_size=5))
        comptes.append({
            'Numéro': numero,
            'Intitulé': f"Compte {numero}",
            'Ant Débit': draw(st.floats(min_value=0, max_value=10000000,
                                        allow_nan=False, allow_infinity=False)),
            'Ant Crédit': draw(st.floats(min_value=0, max_value=10000000,
                                         allow_nan=False, allow_infinity=False)),
            'Débit': draw(st.floats(min_value=0, max_value=5000000,
                                   allow_nan=False, allow_infinity=False)),
            'Crédit': draw(st.floats(min_value=0, max_value=5000000,
                                    allow_nan=False, allow_infinity=False)),
            'Solde Débit': draw(st.floats(min_value=0, max_value=15000000,
                                          allow_nan=False, allow_infinity=False)),
            'Solde Crédit': draw(st.floats(min_value=0, max_value=15000000,
                                           allow_nan=False, allow_infinity=False))
        })
    
    return pd.DataFrame(comptes), compte_amort['numero']


# ============================================================================
# TESTS DE PROPRIÉTÉ
# ============================================================================

@given(compte=st_compte_amortissement())
@settings(max_examples=100, deadline=60000)
def test_property_depreciation_sign_inversion_credit_is_dotation(compte):
    """
    Property 8: Depreciation Account Sign Inversion (crédit = dotation).
    
    Pour tout compte d'amortissement, les mouvements crédit doivent être
    traités comme des augmentations (dotations aux amortissements).
    
    Valide: Requirements 3.7, 4.4
    """
    # Créer une balance avec le compte d'amortissement
    balance = pd.DataFrame([{
        'Numéro': compte['numero'],
        'Intitulé': f"Amortissement {compte['numero']}",
        'Ant Débit': 0.0,
        'Ant Crédit': 1000000.0,
        'Débit': compte['mvt_debit'],
        'Crédit': compte['mvt_credit'],
        'Solde Débit': 0.0,
        'Solde Crédit': 1000000.0 + compte['mvt_credit'] - compte['mvt_debit']
    }])
    
    calc = MovementCalculator()
    mouvements = calc.calculer_mouvements_amortissement(compte['numero'], balance)
    
    # PROPRIÉTÉ: Les mouvements crédit = dotations (augmentation amortissement)
    assert mouvements['dotations'] == compte['mvt_credit'], (
        f"Les mouvements crédit doivent être traités comme des dotations. "
        f"Attendu={compte['mvt_credit']:.2f}, "
        f"Obtenu={mouvements['dotations']:.2f}"
    )
    
    # PROPRIÉTÉ: Les dotations doivent être >= 0
    assert mouvements['dotations'] >= 0, (
        f"Les dotations doivent être positives ou nulles. "
        f"Obtenu={mouvements['dotations']:.2f}"
    )


@given(compte=st_compte_amortissement())
@settings(max_examples=100, deadline=60000)
def test_property_depreciation_sign_inversion_debit_is_reprise(compte):
    """
    Property 8: Depreciation Account Sign Inversion (débit = reprise).
    
    Pour tout compte d'amortissement, les mouvements débit doivent être
    traités comme des diminutions (reprises d'amortissements).
    
    Valide: Requirements 3.7, 4.5
    """
    # Créer une balance avec le compte d'amortissement
    balance = pd.DataFrame([{
        'Numéro': compte['numero'],
        'Intitulé': f"Amortissement {compte['numero']}",
        'Ant Débit': 0.0,
        'Ant Crédit': 1000000.0,
        'Débit': compte['mvt_debit'],
        'Crédit': compte['mvt_credit'],
        'Solde Débit': 0.0,
        'Solde Crédit': 1000000.0 + compte['mvt_credit'] - compte['mvt_debit']
    }])
    
    calc = MovementCalculator()
    mouvements = calc.calculer_mouvements_amortissement(compte['numero'], balance)
    
    # PROPRIÉTÉ: Les mouvements débit = reprises (diminution amortissement)
    assert mouvements['reprises'] == compte['mvt_debit'], (
        f"Les mouvements débit doivent être traités comme des reprises. "
        f"Attendu={compte['mvt_debit']:.2f}, "
        f"Obtenu={mouvements['reprises']:.2f}"
    )
    
    # PROPRIÉTÉ: Les reprises doivent être >= 0
    assert mouvements['reprises'] >= 0, (
        f"Les reprises doivent être positives ou nulles. "
        f"Obtenu={mouvements['reprises']:.2f}"
    )


@given(data=st_balance_avec_amortissement())
@settings(max_examples=100, deadline=60000)
def test_property_depreciation_sign_inversion_complete(data):
    """
    Property 8: Depreciation Account Sign Inversion (test complet).
    
    Pour tout compte d'amortissement dans une balance, le système doit
    inverser les signes: crédit = dotation, débit = reprise.
    
    Valide: Requirements 3.7, 4.4, 4.5
    """
    balance, numero_amort = data
    
    calc = MovementCalculator()
    mouvements = calc.calculer_mouvements_amortissement(numero_amort, balance)
    
    # Récupérer les mouvements réels du compte
    compte_data = balance[balance['Numéro'] == numero_amort].iloc[0]
    mvt_debit_reel = compte_data['Débit']
    mvt_credit_reel = compte_data['Crédit']
    
    # PROPRIÉTÉ: Inversion complète des signes
    assert mouvements['dotations'] == mvt_credit_reel, (
        f"Crédit doit être traité comme dotation. "
        f"Crédit={mvt_credit_reel:.2f}, "
        f"Dotations={mouvements['dotations']:.2f}"
    )
    
    assert mouvements['reprises'] == mvt_debit_reel, (
        f"Débit doit être traité comme reprise. "
        f"Débit={mvt_debit_reel:.2f}, "
        f"Reprises={mouvements['reprises']:.2f}"
    )
    
    # PROPRIÉTÉ: Les deux valeurs doivent être non-négatives
    assert mouvements['dotations'] >= 0
    assert mouvements['reprises'] >= 0


@given(
    numero_classe_28=st.text(alphabet='0123456789', min_size=1, max_size=3),
    numero_classe_29=st.text(alphabet='0123456789', min_size=1, max_size=3),
    mvt_credit=st.floats(min_value=0, max_value=1e7, allow_nan=False, allow_infinity=False),
    mvt_debit=st.floats(min_value=0, max_value=1e7, allow_nan=False, allow_infinity=False)
)
@settings(max_examples=100, deadline=60000)
def test_property_depreciation_classes_28_and_29(numero_classe_28, numero_classe_29,
                                                  mvt_credit, mvt_debit):
    """
    Property 8: Depreciation Account Sign Inversion (classes 28 et 29).
    
    Les comptes des classes 28 (amortissements) et 29 (provisions) doivent
    tous avoir le même comportement d'inversion des signes.
    
    Valide: Requirements 3.7
    """
    calc = MovementCalculator()
    
    # Tester avec un compte de classe 28
    numero_28 = f"28{numero_classe_28}"
    balance_28 = pd.DataFrame([{
        'Numéro': numero_28,
        'Intitulé': f"Amortissement {numero_28}",
        'Ant Débit': 0.0,
        'Ant Crédit': 1000000.0,
        'Débit': mvt_debit,
        'Crédit': mvt_credit,
        'Solde Débit': 0.0,
        'Solde Crédit': 1000000.0 + mvt_credit - mvt_debit
    }])
    
    mouvements_28 = calc.calculer_mouvements_amortissement(numero_28, balance_28)
    
    # Tester avec un compte de classe 29
    numero_29 = f"29{numero_classe_29}"
    balance_29 = pd.DataFrame([{
        'Numéro': numero_29,
        'Intitulé': f"Provision {numero_29}",
        'Ant Débit': 0.0,
        'Ant Crédit': 1000000.0,
        'Débit': mvt_debit,
        'Crédit': mvt_credit,
        'Solde Débit': 0.0,
        'Solde Crédit': 1000000.0 + mvt_credit - mvt_debit
    }])
    
    mouvements_29 = calc.calculer_mouvements_amortissement(numero_29, balance_29)
    
    # PROPRIÉTÉ: Les deux classes doivent avoir le même comportement
    assert mouvements_28['dotations'] == mouvements_29['dotations'] == mvt_credit, (
        f"Les classes 28 et 29 doivent traiter le crédit comme dotation. "
        f"Classe 28: {mouvements_28['dotations']:.2f}, "
        f"Classe 29: {mouvements_29['dotations']:.2f}, "
        f"Attendu: {mvt_credit:.2f}"
    )
    
    assert mouvements_28['reprises'] == mouvements_29['reprises'] == mvt_debit, (
        f"Les classes 28 et 29 doivent traiter le débit comme reprise. "
        f"Classe 28: {mouvements_28['reprises']:.2f}, "
        f"Classe 29: {mouvements_29['reprises']:.2f}, "
        f"Attendu: {mvt_debit:.2f}"
    )


# ============================================================================
# TESTS UNITAIRES COMPLÉMENTAIRES
# ============================================================================

def test_amortissement_dotation_simple():
    """Test unitaire avec une dotation simple."""
    calc = MovementCalculator()
    
    # Compte 2811 avec dotation de 100000
    balance = pd.DataFrame([{
        'Numéro': '2811',
        'Intitulé': 'Amortissement frais de recherche',
        'Ant Débit': 0.0,
        'Ant Crédit': 200000.0,
        'Débit': 0.0,
        'Crédit': 100000.0,
        'Solde Débit': 0.0,
        'Solde Crédit': 300000.0
    }])
    
    mouvements = calc.calculer_mouvements_amortissement('2811', balance)
    
    assert mouvements['dotations'] == 100000.0
    assert mouvements['reprises'] == 0.0


def test_amortissement_reprise_simple():
    """Test unitaire avec une reprise simple."""
    calc = MovementCalculator()
    
    # Compte 2812 avec reprise de 50000
    balance = pd.DataFrame([{
        'Numéro': '2812',
        'Intitulé': 'Amortissement brevets',
        'Ant Débit': 0.0,
        'Ant Crédit': 300000.0,
        'Débit': 50000.0,
        'Crédit': 0.0,
        'Solde Débit': 0.0,
        'Solde Crédit': 250000.0
    }])
    
    mouvements = calc.calculer_mouvements_amortissement('2812', balance)
    
    assert mouvements['dotations'] == 0.0
    assert mouvements['reprises'] == 50000.0


def test_amortissement_dotation_et_reprise():
    """Test unitaire avec dotation et reprise simultanées."""
    calc = MovementCalculator()
    
    # Compte 2813 avec dotation de 150000 et reprise de 30000
    balance = pd.DataFrame([{
        'Numéro': '2813',
        'Intitulé': 'Amortissement logiciels',
        'Ant Débit': 0.0,
        'Ant Crédit': 500000.0,
        'Débit': 30000.0,
        'Crédit': 150000.0,
        'Solde Débit': 0.0,
        'Solde Crédit': 620000.0
    }])
    
    mouvements = calc.calculer_mouvements_amortissement('2813', balance)
    
    assert mouvements['dotations'] == 150000.0
    assert mouvements['reprises'] == 30000.0


def test_amortissement_classe_29():
    """Test unitaire avec un compte de classe 29 (provisions)."""
    calc = MovementCalculator()
    
    # Compte 2911 avec dotation de 80000
    balance = pd.DataFrame([{
        'Numéro': '2911',
        'Intitulé': 'Provision pour dépréciation',
        'Ant Débit': 0.0,
        'Ant Crédit': 150000.0,
        'Débit': 0.0,
        'Crédit': 80000.0,
        'Solde Débit': 0.0,
        'Solde Crédit': 230000.0
    }])
    
    mouvements = calc.calculer_mouvements_amortissement('2911', balance)
    
    assert mouvements['dotations'] == 80000.0
    assert mouvements['reprises'] == 0.0


def test_amortissement_compte_inexistant():
    """Test unitaire avec un compte d'amortissement inexistant."""
    calc = MovementCalculator()
    
    # Balance sans le compte 2814
    balance = pd.DataFrame([{
        'Numéro': '2811',
        'Intitulé': 'Amortissement frais de recherche',
        'Ant Débit': 0.0,
        'Ant Crédit': 200000.0,
        'Débit': 0.0,
        'Crédit': 100000.0,
        'Solde Débit': 0.0,
        'Solde Crédit': 300000.0
    }])
    
    mouvements = calc.calculer_mouvements_amortissement('2814', balance)
    
    # Doit retourner des valeurs nulles pour un compte inexistant
    assert mouvements['dotations'] == 0.0
    assert mouvements['reprises'] == 0.0


def test_amortissement_valeurs_nulles():
    """Test unitaire avec des mouvements nuls."""
    calc = MovementCalculator()
    
    # Compte 2815 sans mouvements
    balance = pd.DataFrame([{
        'Numéro': '2815',
        'Intitulé': 'Amortissement autres immobilisations',
        'Ant Débit': 0.0,
        'Ant Crédit': 400000.0,
        'Débit': 0.0,
        'Crédit': 0.0,
        'Solde Débit': 0.0,
        'Solde Crédit': 400000.0
    }])
    
    mouvements = calc.calculer_mouvements_amortissement('2815', balance)
    
    assert mouvements['dotations'] == 0.0
    assert mouvements['reprises'] == 0.0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short', '--hypothesis-show-statistics'])
