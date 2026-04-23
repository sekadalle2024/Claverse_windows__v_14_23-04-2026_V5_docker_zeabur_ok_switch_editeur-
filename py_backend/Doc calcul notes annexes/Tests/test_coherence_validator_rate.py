"""
Test de propriété pour le calcul du taux de cohérence global.

Property 17: Coherence Rate Calculation
Valide les exigences: 10.5, 10.6

Pour tout ensemble de validations de cohérence, le Coherence_Validator doit:
1. Calculer un taux de cohérence global comme le pourcentage de validations avec écarts < 1%
2. Émettre une alerte critique si le taux est inférieur à 95%
"""

import pytest
from hypothesis import given, assume, strategies as st
from hypothesis import settings
import pandas as pd

from Modules.coherence_validator import CoherenceValidator


# ============================================================================
# STRATÉGIES HYPOTHESIS POUR LES TESTS DE TAUX DE COHÉRENCE
# ============================================================================

@st.composite
def st_note_avec_ecart_controle(draw, ecart_pct_max=0.5):
    """
    Génère une note d'immobilisation avec un écart contrôlé.
    
    Args:
        ecart_pct_max: Pourcentage d'écart maximum (0.5 = 0.5%)
    
    Cette stratégie permet de générer des notes avec des écarts
    précis pour tester les seuils de cohérence.
    """
    num_lignes = draw(st.integers(min_value=2, max_value=5))
    
    lignes = []
    total_brut_ouverture = 0.0
    total_augmentations = 0.0
    total_diminutions = 0.0
    total_brut_cloture = 0.0
    total_amort_ouverture = 0.0
    total_dotations = 0.0
    total_reprises = 0.0
    total_amort_cloture = 0.0
    total_vnc_ouverture = 0.0
    total_vnc_cloture = 0.0
    
    for i in range(num_lignes):
        # Générer les valeurs brutes
        brut_ouverture = draw(st.floats(
            min_value=100000,
            max_value=10000000,
            allow_nan=False,
            allow_infinity=False
        ))
        augmentations = draw(st.floats(
            min_value=0,
            max_value=5000000,
            allow_nan=False,
            allow_infinity=False
        ))
        diminutions = draw(st.floats(
            min_value=0,
            max_value=min(brut_ouverture, augmentations),
            allow_nan=False,
            allow_infinity=False
        ))
        brut_cloture = brut_ouverture + augmentations - diminutions
        
        # Générer les amortissements
        amort_ouverture = draw(st.floats(
            min_value=0,
            max_value=brut_ouverture * 0.8,
            allow_nan=False,
            allow_infinity=False
        ))
        dotations = draw(st.floats(
            min_value=0,
            max_value=brut_cloture * 0.2,
            allow_nan=False,
            allow_infinity=False
        ))
        reprises = draw(st.floats(
            min_value=0,
            max_value=amort_ouverture * 0.5,
            allow_nan=False,
            allow_infinity=False
        ))
        amort_cloture = amort_ouverture + dotations - reprises
        
        # Calculer les VNC
        vnc_ouverture = brut_ouverture - amort_ouverture
        vnc_cloture = brut_cloture - amort_cloture
        
        # Assurer que VNC >= 0
        assume(vnc_ouverture >= 0)
        assume(vnc_cloture >= 0)
        
        lignes.append({
            'libelle': f'Ligne {i+1}',
            'brut_ouverture': brut_ouverture,
            'augmentations': augmentations,
            'diminutions': diminutions,
            'brut_cloture': brut_cloture,
            'amort_ouverture': amort_ouverture,
            'dotations': dotations,
            'reprises': reprises,
            'amort_cloture': amort_cloture,
            'vnc_ouverture': vnc_ouverture,
            'vnc_cloture': vnc_cloture
        })
        
        # Accumuler les totaux
        total_brut_ouverture += brut_ouverture
        total_augmentations += augmentations
        total_diminutions += diminutions
        total_brut_cloture += brut_cloture
        total_amort_ouverture += amort_ouverture
        total_dotations += dotations
        total_reprises += reprises
        total_amort_cloture += amort_cloture
        total_vnc_ouverture += vnc_ouverture
        total_vnc_cloture += vnc_cloture
    
    # Ajouter un écart contrôlé au total (pour tester les seuils)
    ecart_vnc = total_vnc_cloture * (ecart_pct_max / 100.0)
    total_vnc_cloture_avec_ecart = total_vnc_cloture + ecart_vnc
    
    ecart_dotations = total_dotations * (ecart_pct_max / 100.0)
    total_dotations_avec_ecart = total_dotations + ecart_dotations
    
    # Ajouter la ligne de total
    lignes.append({
        'libelle': 'TOTAL',
        'brut_ouverture': total_brut_ouverture,
        'augmentations': total_augmentations,
        'diminutions': total_diminutions,
        'brut_cloture': total_brut_cloture,
        'amort_ouverture': total_amort_ouverture,
        'dotations': total_dotations_avec_ecart,  # Avec écart
        'reprises': total_reprises,
        'amort_cloture': total_amort_cloture,
        'vnc_ouverture': total_vnc_ouverture,
        'vnc_cloture': total_vnc_cloture_avec_ecart  # Avec écart
    })
    
    return pd.DataFrame(lignes)


@st.composite
def st_ensemble_notes_taux_eleve(draw):
    """
    Génère un ensemble de notes avec un taux de cohérence élevé (>= 95%).
    
    Toutes les notes ont des écarts < 1%.
    """
    notes = {}
    
    # Générer les 5 notes d'immobilisations avec écarts < 1%
    for note_name in ['note_3a', 'note_3b', 'note_3c', 'note_3d', 'note_3e']:
        ecart_pct = draw(st.floats(min_value=0.0, max_value=0.9))  # < 1%
        notes[note_name] = draw(st_note_avec_ecart_controle(ecart_pct_max=ecart_pct))
    
    return notes


@st.composite
def st_ensemble_notes_taux_faible(draw):
    """
    Génère un ensemble de notes avec un taux de cohérence faible (< 95%).
    
    Au moins 10% des notes ont des écarts >= 1%.
    """
    notes = {}
    
    # Générer les 5 notes d'immobilisations
    # Au moins 1 note doit avoir un écart >= 1% pour avoir un taux < 100%
    for i, note_name in enumerate(['note_3a', 'note_3b', 'note_3c', 'note_3d', 'note_3e']):
        if i < 2:  # Les 2 premières notes ont des écarts >= 1%
            ecart_pct = draw(st.floats(min_value=1.0, max_value=5.0))
        else:  # Les autres ont des écarts < 1%
            ecart_pct = draw(st.floats(min_value=0.0, max_value=0.9))
        
        notes[note_name] = draw(st_note_avec_ecart_controle(ecart_pct_max=ecart_pct))
    
    return notes


@st.composite
def st_ensemble_notes_taux_variable(draw):
    """
    Génère un ensemble de notes avec un taux de cohérence variable.
    
    Le taux peut être n'importe où entre 0% et 100%.
    """
    notes = {}
    
    # Générer les 5 notes d'immobilisations avec écarts variables
    for note_name in ['note_3a', 'note_3b', 'note_3c', 'note_3d', 'note_3e']:
        ecart_pct = draw(st.floats(min_value=0.0, max_value=10.0))
        notes[note_name] = draw(st_note_avec_ecart_controle(ecart_pct_max=ecart_pct))
    
    return notes


# ============================================================================
# TESTS DE PROPRIÉTÉ
# ============================================================================

@given(notes=st_ensemble_notes_taux_eleve())
@settings(max_examples=50, deadline=60000)
def test_property_coherence_rate_high_coherence(notes):
    """
    Property 17.1: Taux de cohérence élevé pour notes cohérentes.
    
    Pour tout ensemble de notes avec écarts < 1%, le taux de cohérence
    global doit être >= 95%.
    
    **Validates: Requirements 10.5, 10.6**
    """
    validator = CoherenceValidator(notes)
    
    # Effectuer toutes les validations
    validator.valider_total_immobilisations()
    validator.valider_dotations_amortissements()
    validator.valider_continuite_temporelle()
    
    # Calculer le taux de cohérence
    taux = validator.calculer_taux_coherence()
    
    # PROPRIÉTÉ: Le taux doit être entre 0 et 100
    assert 0 <= taux <= 100, (
        f"Le taux de cohérence doit être entre 0 et 100. "
        f"Taux: {taux:.1f}%"
    )
    
    # PROPRIÉTÉ: Pour des notes avec écarts < 1%, le taux doit être >= 95%
    assert taux >= 95.0, (
        f"Le taux de cohérence devrait être >= 95% pour des notes avec écarts < 1%. "
        f"Taux: {taux:.1f}%"
    )
    
    # PROPRIÉTÉ: Aucune alerte critique ne doit être émise
    alertes_critiques = [a for a in validator.alertes if a['niveau'] == 'critical']
    assert len(alertes_critiques) == 0, (
        f"Aucune alerte critique ne devrait être émise pour un taux >= 95%. "
        f"Alertes critiques: {len(alertes_critiques)}"
    )


@given(notes=st_ensemble_notes_taux_faible())
@settings(max_examples=50, deadline=60000)
def test_property_coherence_rate_low_coherence_alert(notes):
    """
    Property 17.2: Alerte critique pour taux de cohérence faible.
    
    Pour tout ensemble de notes avec un taux de cohérence < 95%,
    une alerte critique doit être émise.
    
    **Validates: Requirements 10.5, 10.6**
    """
    validator = CoherenceValidator(notes)
    
    # Effectuer toutes les validations
    validator.valider_total_immobilisations()
    validator.valider_dotations_amortissements()
    validator.valider_continuite_temporelle()
    
    # Calculer le taux de cohérence
    taux = validator.calculer_taux_coherence()
    
    # PROPRIÉTÉ: Le taux doit être entre 0 et 100
    assert 0 <= taux <= 100, (
        f"Le taux de cohérence doit être entre 0 et 100. "
        f"Taux: {taux:.1f}%"
    )
    
    # PROPRIÉTÉ: Si le taux < 95%, une alerte critique doit être émise
    if taux < 95.0:
        alertes_critiques = [a for a in validator.alertes if a['niveau'] == 'critical']
        assert len(alertes_critiques) > 0, (
            f"Une alerte critique devrait être émise pour un taux < 95%. "
            f"Taux: {taux:.1f}%, Alertes critiques: {len(alertes_critiques)}"
        )
        
        # PROPRIÉTÉ: L'alerte doit mentionner le taux de cohérence
        alerte_taux = alertes_critiques[0]
        assert 'taux de cohérence' in alerte_taux['message'].lower(), (
            "L'alerte critique doit mentionner le taux de cohérence"
        )
        assert '95' in alerte_taux['message'], (
            "L'alerte critique doit mentionner le seuil de 95%"
        )


@given(notes=st_ensemble_notes_taux_variable())
@settings(max_examples=50, deadline=60000)
def test_property_coherence_rate_calculation_formula(notes):
    """
    Property 17.3: Formule de calcul du taux de cohérence.
    
    Pour tout ensemble de notes, le taux de cohérence doit être calculé
    comme: (nombre de validations cohérentes / nombre total de validations) * 100
    
    **Validates: Requirements 10.5**
    """
    validator = CoherenceValidator(notes)
    
    # Effectuer toutes les validations
    validator.valider_total_immobilisations()
    validator.valider_dotations_amortissements()
    validator.valider_continuite_temporelle()
    
    # Calculer le taux de cohérence
    taux = validator.calculer_taux_coherence()
    
    # PROPRIÉTÉ: Recalculer manuellement le taux pour vérifier la formule
    total_validations = 0
    validations_coherentes = 0
    
    # Compter les validations de total immobilisations
    if 'total_immobilisations' in validator.validations:
        total_validations += 1
        if validator.validations['total_immobilisations']['coherent']:
            validations_coherentes += 1
    
    # Compter les validations de dotations
    if 'dotations_amortissements' in validator.validations:
        total_validations += 1
        if validator.validations['dotations_amortissements']['coherent']:
            validations_coherentes += 1
    
    # Compter les validations de continuité temporelle
    if 'continuite_temporelle' in validator.validations:
        for note, validation in validator.validations['continuite_temporelle'].items():
            total_validations += 1
            if validation['coherent']:
                validations_coherentes += 1
    
    # Calculer le taux attendu
    taux_attendu = (validations_coherentes / total_validations * 100) if total_validations > 0 else 0.0
    
    # PROPRIÉTÉ: Le taux calculé doit correspondre à la formule
    assert abs(taux - taux_attendu) < 0.01, (
        f"Le taux de cohérence ne correspond pas à la formule. "
        f"Taux calculé: {taux:.1f}%, Taux attendu: {taux_attendu:.1f}% "
        f"({validations_coherentes}/{total_validations})"
    )


@given(notes=st_ensemble_notes_taux_variable())
@settings(max_examples=30, deadline=60000)
def test_property_coherence_rate_percentage_range(notes):
    """
    Property 17.4: Le taux de cohérence est un pourcentage valide.
    
    Pour tout ensemble de notes, le taux de cohérence doit être
    un nombre entre 0 et 100 inclus.
    
    **Validates: Requirements 10.5**
    """
    validator = CoherenceValidator(notes)
    
    # Effectuer toutes les validations
    validator.valider_total_immobilisations()
    validator.valider_dotations_amortissements()
    validator.valider_continuite_temporelle()
    
    # Calculer le taux de cohérence
    taux = validator.calculer_taux_coherence()
    
    # PROPRIÉTÉ: Le taux doit être un nombre
    assert isinstance(taux, (int, float)), (
        f"Le taux de cohérence doit être un nombre. "
        f"Type: {type(taux)}"
    )
    
    # PROPRIÉTÉ: Le taux doit être entre 0 et 100
    assert 0 <= taux <= 100, (
        f"Le taux de cohérence doit être entre 0 et 100. "
        f"Taux: {taux:.1f}%"
    )
    
    # PROPRIÉTÉ: Le taux ne doit pas être NaN ou infini
    assert not (taux != taux), "Le taux ne doit pas être NaN"  # NaN != NaN
    assert taux != float('inf'), "Le taux ne doit pas être infini"
    assert taux != float('-inf'), "Le taux ne doit pas être -infini"


@given(notes=st_ensemble_notes_taux_variable())
@settings(max_examples=30, deadline=60000)
def test_property_coherence_rate_monotonicity(notes):
    """
    Property 17.5: Monotonie du taux de cohérence.
    
    Pour tout ensemble de notes, si on améliore la cohérence d'une note,
    le taux de cohérence global ne doit pas diminuer.
    
    **Validates: Requirements 10.5**
    """
    validator1 = CoherenceValidator(notes)
    
    # Effectuer toutes les validations
    validator1.valider_total_immobilisations()
    validator1.valider_dotations_amortissements()
    validator1.valider_continuite_temporelle()
    
    # Calculer le taux initial
    taux_initial = validator1.calculer_taux_coherence()
    
    # Améliorer la cohérence d'une note (réduire l'écart)
    notes_ameliorees = notes.copy()
    if 'note_3a' in notes_ameliorees:
        df = notes_ameliorees['note_3a'].copy()
        # Réduire l'écart sur le total (dernière ligne)
        if len(df) > 0:
            # Recalculer le total exact sans écart
            total_vnc = df.iloc[:-1]['vnc_cloture'].sum()
            total_dotations = df.iloc[:-1]['dotations'].sum()
            df.loc[df.index[-1], 'vnc_cloture'] = total_vnc
            df.loc[df.index[-1], 'dotations'] = total_dotations
            notes_ameliorees['note_3a'] = df
    
    validator2 = CoherenceValidator(notes_ameliorees)
    
    # Effectuer toutes les validations
    validator2.valider_total_immobilisations()
    validator2.valider_dotations_amortissements()
    validator2.valider_continuite_temporelle()
    
    # Calculer le taux amélioré
    taux_ameliore = validator2.calculer_taux_coherence()
    
    # PROPRIÉTÉ: Le taux amélioré doit être >= au taux initial
    assert taux_ameliore >= taux_initial - 0.01, (  # Tolérance de 0.01% pour les erreurs d'arrondi
        f"Le taux de cohérence ne devrait pas diminuer après amélioration. "
        f"Taux initial: {taux_initial:.1f}%, Taux amélioré: {taux_ameliore:.1f}%"
    )


@given(notes=st_ensemble_notes_taux_variable())
@settings(max_examples=30, deadline=60000)
def test_property_coherence_rate_alert_details(notes):
    """
    Property 17.6: Détails de l'alerte critique.
    
    Pour tout ensemble de notes avec taux < 95%, l'alerte critique
    doit contenir les détails du taux et des validations.
    
    **Validates: Requirements 10.6**
    """
    validator = CoherenceValidator(notes)
    
    # Effectuer toutes les validations
    validator.valider_total_immobilisations()
    validator.valider_dotations_amortissements()
    validator.valider_continuite_temporelle()
    
    # Calculer le taux de cohérence
    taux = validator.calculer_taux_coherence()
    
    # Si le taux < 95%, vérifier les détails de l'alerte
    if taux < 95.0:
        alertes_critiques = [a for a in validator.alertes if a['niveau'] == 'critical']
        
        # PROPRIÉTÉ: Au moins une alerte critique doit exister
        assert len(alertes_critiques) > 0, (
            "Une alerte critique devrait exister pour un taux < 95%"
        )
        
        alerte = alertes_critiques[0]
        
        # PROPRIÉTÉ: L'alerte doit avoir un niveau 'critical'
        assert alerte['niveau'] == 'critical', (
            f"L'alerte devrait avoir le niveau 'critical'. "
            f"Niveau: {alerte['niveau']}"
        )
        
        # PROPRIÉTÉ: L'alerte doit avoir un message
        assert 'message' in alerte, "L'alerte doit avoir un message"
        assert len(alerte['message']) > 0, "Le message ne doit pas être vide"
        
        # PROPRIÉTÉ: L'alerte doit avoir des détails
        assert 'details' in alerte, "L'alerte doit avoir des détails"
        details = alerte['details']
        
        # PROPRIÉTÉ: Les détails doivent contenir le taux
        assert 'taux' in details, "Les détails doivent contenir le taux"
        assert abs(details['taux'] - taux) < 0.01, (
            "Le taux dans les détails doit correspondre au taux calculé"
        )
        
        # PROPRIÉTÉ: Les détails doivent contenir les compteurs
        assert 'validations_coherentes' in details, (
            "Les détails doivent contenir le nombre de validations cohérentes"
        )
        assert 'total_validations' in details, (
            "Les détails doivent contenir le nombre total de validations"
        )


# ============================================================================
# TESTS UNITAIRES COMPLÉMENTAIRES
# ============================================================================

def test_coherence_rate_100_percent():
    """Test unitaire avec un taux de cohérence de 100%."""
    # Créer des notes parfaitement cohérentes
    df_3a = pd.DataFrame({
        'libelle': ['Ligne 1', 'TOTAL'],
        'brut_ouverture': [1000000, 1000000],
        'augmentations': [200000, 200000],
        'diminutions': [0, 0],
        'brut_cloture': [1200000, 1200000],
        'amort_ouverture': [200000, 200000],
        'dotations': [100000, 100000],
        'reprises': [0, 0],
        'amort_cloture': [300000, 300000],
        'vnc_ouverture': [800000, 800000],
        'vnc_cloture': [900000, 900000]
    })
    
    notes = {'note_3a': df_3a}
    
    validator = CoherenceValidator(notes)
    validator.valider_total_immobilisations()
    validator.valider_dotations_amortissements()
    
    taux = validator.calculer_taux_coherence()
    
    # Le taux devrait être 100%
    assert taux == 100.0, f"Le taux devrait être 100%. Taux: {taux:.1f}%"
    
    # Aucune alerte critique
    alertes_critiques = [a for a in validator.alertes if a['niveau'] == 'critical']
    assert len(alertes_critiques) == 0


def test_coherence_rate_below_95_percent():
    """Test unitaire avec un taux de cohérence < 95%."""
    # Créer des notes avec incohérences
    df_3a = pd.DataFrame({
        'libelle': ['Ligne 1', 'TOTAL'],
        'vnc_cloture': [900000, 900000],
        'dotations': [100000, 100000]
    })
    
    df_3b = pd.DataFrame({
        'libelle': ['Ligne 1', 'TOTAL'],
        'vnc_cloture': [1950000, 5000000],  # Incohérence > 1%
        'dotations': [150000, 500000]  # Incohérence > 1%
    })
    
    notes = {
        'note_3a': df_3a,
        'note_3b': df_3b
    }
    
    validator = CoherenceValidator(notes)
    validator.valider_total_immobilisations()
    validator.valider_dotations_amortissements()
    
    taux = validator.calculer_taux_coherence()
    
    # Le taux devrait être entre 0 et 100
    assert 0 <= taux <= 100
    
    # Si le taux < 95%, une alerte critique doit exister
    if taux < 95.0:
        alertes_critiques = [a for a in validator.alertes if a['niveau'] == 'critical']
        assert len(alertes_critiques) > 0, (
            f"Une alerte critique devrait être émise. Taux: {taux:.1f}%"
        )


def test_coherence_rate_empty_validations():
    """Test unitaire avec aucune validation effectuée."""
    notes = {}
    
    validator = CoherenceValidator(notes)
    
    # Ne pas effectuer de validations
    taux = validator.calculer_taux_coherence()
    
    # Le taux devrait être 0 si aucune validation
    assert taux == 0.0, f"Le taux devrait être 0 sans validations. Taux: {taux:.1f}%"


def test_coherence_rate_partial_validations():
    """Test unitaire avec seulement certaines validations effectuées."""
    df_3a = pd.DataFrame({
        'libelle': ['Ligne 1', 'TOTAL'],
        'vnc_cloture': [900000, 900000],
        'dotations': [100000, 100000]
    })
    
    notes = {'note_3a': df_3a}
    
    validator = CoherenceValidator(notes)
    
    # Effectuer seulement une validation
    validator.valider_total_immobilisations()
    
    taux = validator.calculer_taux_coherence()
    
    # Le taux devrait être calculé sur les validations effectuées
    assert 0 <= taux <= 100
    assert isinstance(taux, float)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short', '--hypothesis-show-statistics'])
