"""
Tests basés sur les propriétés pour le Mapping_Manager.

Feature: calcul-notes-annexes-syscohada
Property 12: Mapping Lookup Consistency

**Validates: Requirements 7.2, 7.5, 7.7**
"""

import pytest
from hypothesis import given, settings, strategies as st, assume
import json
import tempfile
import os
import sys

# Ajouter le chemin des modules au PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Modules'))

from mapping_manager import MappingManager, InvalidJSONException


# ============================================================================
# STRATÉGIES HYPOTHESIS
# ============================================================================

@st.composite
def st_poste_name(draw):
    """Génère un nom de poste valide."""
    return draw(st.text(min_size=5, max_size=100, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        whitelist_characters=' -éèêàâôûùç'
    )))


@st.composite
def st_account_root(draw):
    """Génère une racine de compte numérique valide (1-5 chiffres)."""
    length = draw(st.integers(min_value=1, max_value=5))
    return draw(st.text(alphabet='0123456789', min_size=length, max_size=length))


@st.composite
def st_section_name(draw):
    """Génère un nom de section valide."""
    return draw(st.sampled_from(['bilan_actif', 'bilan_passif', 'charges', 'produits']))


@st.composite
def st_correspondances_dict(draw):
    """
    Génère un dictionnaire de correspondances valide.
    
    Structure:
    {
        "section": [
            {"ref": "XX", "libelle": "...", "racines": ["211", "212", ...]},
            ...
        ]
    }
    """
    correspondances = {}
    
    # Générer 1-4 sections
    num_sections = draw(st.integers(min_value=1, max_value=4))
    sections = draw(st.lists(
        st_section_name(),
        min_size=num_sections,
        max_size=num_sections,
        unique=True
    ))
    
    for section in sections:
        # Générer 1-10 postes par section
        num_postes = draw(st.integers(min_value=1, max_value=10))
        postes = []
        
        for i in range(num_postes):
            ref = f"{chr(65 + i)}{chr(65 + (i % 26))}"  # AA, AB, AC, etc.
            libelle = draw(st_poste_name())
            
            # Générer 0-5 racines de comptes
            num_racines = draw(st.integers(min_value=0, max_value=5))
            racines = draw(st.lists(
                st_account_root(),
                min_size=num_racines,
                max_size=num_racines,
                unique=True
            ))
            
            postes.append({
                "ref": ref,
                "libelle": libelle,
                "racines": racines
            })
        
        correspondances[section] = postes
    
    return correspondances


# ============================================================================
# PROPERTY TESTS
# ============================================================================

@given(correspondances=st_correspondances_dict())
@settings(max_examples=100, deadline=60000)
def test_property_12_mapping_lookup_consistency(correspondances):
    """
    Feature: calcul-notes-annexes-syscohada
    Property 12: Mapping Lookup Consistency
    
    For any valid poste name in the correspondances_syscohada.json file,
    the Mapping_Manager must return the associated list of account roots.
    If multiple entries have the same libelle, all racines should be returned (deduplicated).
    
    **Validates: Requirements 7.2, 7.5, 7.7**
    """
    # Créer un fichier JSON temporaire
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(correspondances, f, ensure_ascii=False, indent=2)
        temp_file = f.name
    
    try:
        # Charger le mapping
        manager = MappingManager(fichier_json=temp_file)
        
        # Vérifier que toutes les sections sont chargées
        assert manager.correspondances == correspondances
        
        # Pour chaque section et chaque poste, vérifier la cohérence du lookup
        for section_name, postes_list in correspondances.items():
            # Grouper les racines par libellé (pour gérer les duplicates)
            libelle_to_racines = {}
            for poste_data in postes_list:
                libelle = poste_data['libelle']
                racines = poste_data['racines']
                if libelle not in libelle_to_racines:
                    libelle_to_racines[libelle] = []
                libelle_to_racines[libelle].extend(racines)
            
            # Dédupliquer les racines pour chaque libellé
            for libelle, racines_list in libelle_to_racines.items():
                # Dédupliquer en préservant l'ordre
                seen = set()
                racines_attendues = []
                for r in racines_list:
                    if r not in seen:
                        seen.add(r)
                        racines_attendues.append(r)
                
                # Lookup des racines via le manager
                racines_obtenues = manager.obtenir_racines_compte(libelle, section_name)
                
                # Vérifier que les racines retournées correspondent exactement
                assert racines_obtenues == racines_attendues, \
                    f"Incohérence pour {section_name}.{libelle}: " \
                    f"attendu {racines_attendues}, obtenu {racines_obtenues}"
                
                # Vérifier que toutes les racines sont des chaînes numériques valides
                if racines_obtenues:
                    valide, invalides = manager.valider_racines(racines_obtenues)
                    assert valide, f"Racines invalides détectées: {invalides}"
                    
                    for racine in racines_obtenues:
                        assert isinstance(racine, str), \
                            f"Racine {racine} n'est pas une chaîne"
                        assert racine.isdigit(), \
                            f"Racine {racine} n'est pas numérique"
    
    finally:
        # Nettoyer le fichier temporaire
        if os.path.exists(temp_file):
            os.unlink(temp_file)


@given(
    correspondances=st_correspondances_dict(),
    new_poste=st_poste_name(),
    new_racines=st.lists(st_account_root(), min_size=1, max_size=5, unique=True)
)
@settings(max_examples=100, deadline=60000)
def test_property_12_adding_new_correspondences_without_code_changes(
    correspondances, new_poste, new_racines
):
    """
    Feature: calcul-notes-annexes-syscohada
    Property 12: Mapping Lookup Consistency (Dynamic Addition)
    
    Adding new correspondences to the JSON must not require code changes.
    The system must be able to add and retrieve new mappings dynamically.
    
    **Validates: Requirements 7.5**
    """
    # Créer un fichier JSON temporaire
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(correspondances, f, ensure_ascii=False, indent=2)
        temp_file = f.name
    
    try:
        # Charger le mapping initial
        manager = MappingManager(fichier_json=temp_file)
        
        # Choisir une section existante
        if correspondances:
            section = list(correspondances.keys())[0]
        else:
            section = 'bilan_actif'
        
        # Vérifier si le poste existe déjà
        racines_existantes = manager.obtenir_racines_compte(new_poste, section)
        
        # Si le poste existe déjà avec des racines différentes, skip ce test
        # car le comportement avec duplicates est de combiner les racines
        if racines_existantes and racines_existantes != new_racines:
            assume(False)  # Skip this test case
        
        # Ajouter une nouvelle correspondance via l'API (sans modifier le code)
        manager.ajouter_correspondance(new_poste, section, new_racines)
        
        # Vérifier que la nouvelle correspondance est accessible
        racines_obtenues = manager.obtenir_racines_compte(new_poste, section)
        
        assert racines_obtenues == new_racines, \
            f"Nouvelle correspondance non accessible: attendu {new_racines}, obtenu {racines_obtenues}"
        
        # Sauvegarder les modifications
        assert manager.sauvegarder() == True, "Échec de la sauvegarde"
        
        # Recharger depuis le fichier pour vérifier la persistance
        manager2 = MappingManager(fichier_json=temp_file)
        racines_rechargees = manager2.obtenir_racines_compte(new_poste, section)
        
        assert racines_rechargees == new_racines, \
            f"Correspondance non persistée: attendu {new_racines}, obtenu {racines_rechargees}"
    
    finally:
        # Nettoyer le fichier temporaire
        if os.path.exists(temp_file):
            os.unlink(temp_file)


@given(correspondances=st_correspondances_dict())
@settings(max_examples=100, deadline=60000)
def test_property_12_all_account_roots_are_valid_numeric_strings(correspondances):
    """
    Feature: calcul-notes-annexes-syscohada
    Property 12: Mapping Lookup Consistency (Validation)
    
    The Mapping_Manager must validate that each account root is a valid numeric string.
    
    **Validates: Requirements 7.7**
    """
    # Créer un fichier JSON temporaire
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(correspondances, f, ensure_ascii=False, indent=2)
        temp_file = f.name
    
    try:
        # Charger le mapping
        manager = MappingManager(fichier_json=temp_file)
        
        # Vérifier toutes les racines dans toutes les sections
        for section_name, postes_list in correspondances.items():
            for poste_data in postes_list:
                racines = poste_data['racines']
                
                if racines:
                    # Valider les racines
                    valide, invalides = manager.valider_racines(racines)
                    
                    # Toutes les racines doivent être valides (numériques)
                    assert valide, \
                        f"Racines invalides dans {section_name}.{poste_data['libelle']}: {invalides}"
                    
                    # Vérifier individuellement chaque racine
                    for racine in racines:
                        assert isinstance(racine, str), \
                            f"Racine {racine} n'est pas une chaîne"
                        assert racine.isdigit(), \
                            f"Racine {racine} n'est pas numérique"
                        assert len(racine) >= 1 and len(racine) <= 5, \
                            f"Racine {racine} a une longueur invalide: {len(racine)}"
    
    finally:
        # Nettoyer le fichier temporaire
        if os.path.exists(temp_file):
            os.unlink(temp_file)


@given(section=st_section_name(), poste=st_poste_name())
@settings(max_examples=50, deadline=60000)
def test_property_12_missing_poste_returns_empty_list(section, poste):
    """
    Feature: calcul-notes-annexes-syscohada
    Property 12: Mapping Lookup Consistency (Missing Data)
    
    When a poste is not found in the mapping, the Mapping_Manager must
    return an empty list without raising exceptions.
    
    **Validates: Requirements 7.2, 7.4**
    """
    # Créer un fichier JSON vide
    correspondances = {section: []}
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(correspondances, f, ensure_ascii=False, indent=2)
        temp_file = f.name
    
    try:
        # Charger le mapping
        manager = MappingManager(fichier_json=temp_file)
        
        # Rechercher un poste inexistant
        racines = manager.obtenir_racines_compte(poste, section)
        
        # Doit retourner une liste vide
        assert racines == [], \
            f"Poste inexistant devrait retourner [], obtenu {racines}"
    
    finally:
        # Nettoyer le fichier temporaire
        if os.path.exists(temp_file):
            os.unlink(temp_file)


@given(correspondances=st_correspondances_dict())
@settings(max_examples=50, deadline=60000)
def test_property_12_lookup_is_idempotent(correspondances):
    """
    Feature: calcul-notes-annexes-syscohada
    Property 12: Mapping Lookup Consistency (Idempotence)
    
    Looking up the same poste multiple times must return the same result.
    The lookup operation must be idempotent.
    
    **Validates: Requirements 7.2**
    """
    # Créer un fichier JSON temporaire
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(correspondances, f, ensure_ascii=False, indent=2)
        temp_file = f.name
    
    try:
        # Charger le mapping
        manager = MappingManager(fichier_json=temp_file)
        
        # Pour chaque section et chaque poste
        for section_name, postes_list in correspondances.items():
            for poste_data in postes_list:
                libelle = poste_data['libelle']
                
                # Effectuer le lookup 3 fois
                racines_1 = manager.obtenir_racines_compte(libelle, section_name)
                racines_2 = manager.obtenir_racines_compte(libelle, section_name)
                racines_3 = manager.obtenir_racines_compte(libelle, section_name)
                
                # Les 3 résultats doivent être identiques
                assert racines_1 == racines_2 == racines_3, \
                    f"Lookup non idempotent pour {section_name}.{libelle}: " \
                    f"{racines_1} != {racines_2} != {racines_3}"
    
    finally:
        # Nettoyer le fichier temporaire
        if os.path.exists(temp_file):
            os.unlink(temp_file)


# ============================================================================
# TESTS AVEC LE FICHIER RÉEL
# ============================================================================

def test_property_12_real_correspondances_file():
    """
    Test avec le fichier correspondances_syscohada.json réel.
    
    Vérifie que toutes les correspondances du fichier réel sont cohérentes
    et que tous les lookups fonctionnent correctement.
    
    **Validates: Requirements 7.2, 7.5, 7.7**
    """
    # Chemin vers le fichier réel
    fichier_reel = os.path.join(
        os.path.dirname(__file__),
        '..',
        '..',
        'correspondances_syscohada.json'
    )
    
    # Vérifier que le fichier existe
    if not os.path.exists(fichier_reel):
        pytest.skip(f"Fichier réel introuvable: {fichier_reel}")
    
    # Charger le mapping réel
    manager = MappingManager(fichier_json=fichier_reel)
    
    # Vérifier que les 4 sections principales sont présentes
    sections_requises = ['bilan_actif', 'bilan_passif', 'charges', 'produits']
    for section in sections_requises:
        assert section in manager.correspondances, \
            f"Section requise manquante: {section}"
    
    # Vérifier tous les postes de toutes les sections
    for section_name, postes_list in manager.correspondances.items():
        assert isinstance(postes_list, list), \
            f"Section {section_name} devrait être une liste"
        
        # Grouper les racines par libellé (pour gérer les duplicates)
        libelle_to_racines = {}
        for poste_data in postes_list:
            assert 'libelle' in poste_data, \
                f"Poste sans libellé dans {section_name}"
            assert 'racines' in poste_data, \
                f"Poste sans racines dans {section_name}"
            
            libelle = poste_data['libelle']
            racines = poste_data['racines']
            
            if libelle not in libelle_to_racines:
                libelle_to_racines[libelle] = []
            libelle_to_racines[libelle].extend(racines)
        
        # Vérifier chaque libellé unique
        for libelle, racines_list in libelle_to_racines.items():
            # Dédupliquer en préservant l'ordre
            seen = set()
            racines_attendues = []
            for r in racines_list:
                if r not in seen:
                    seen.add(r)
                    racines_attendues.append(r)
            
            # Lookup via le manager
            racines_obtenues = manager.obtenir_racines_compte(libelle, section_name)
            
            # Vérifier la cohérence
            assert racines_obtenues == racines_attendues, \
                f"Incohérence pour {section_name}.{libelle}: " \
                f"attendu {racines_attendues}, obtenu {racines_obtenues}"
            
            # Valider les racines
            if racines_obtenues:
                valide, invalides = manager.valider_racines(racines_obtenues)
                assert valide, \
                    f"Racines invalides dans {section_name}.{libelle}: {invalides}"


def test_property_12_real_file_specific_lookups():
    """
    Test de lookups spécifiques sur le fichier réel.
    
    Vérifie des cas d'usage concrets avec le fichier correspondances_syscohada.json.
    
    **Validates: Requirements 7.2**
    """
    # Chemin vers le fichier réel
    fichier_reel = os.path.join(
        os.path.dirname(__file__),
        '..',
        '..',
        'correspondances_syscohada.json'
    )
    
    # Vérifier que le fichier existe
    if not os.path.exists(fichier_reel):
        pytest.skip(f"Fichier réel introuvable: {fichier_reel}")
    
    # Charger le mapping réel
    manager = MappingManager(fichier_json=fichier_reel)
    
    # Test 1: Frais de recherche et de développement
    racines = manager.obtenir_racines_compte(
        "Frais de recherche et de développement",
        "bilan_actif"
    )
    assert "211" in racines, "Compte 211 devrait être dans les frais de R&D"
    
    # Test 2: Capital
    racines = manager.obtenir_racines_compte("Capital", "bilan_passif")
    assert "101" in racines, "Compte 101 devrait être dans le capital"
    
    # Test 3: Achats de marchandises
    racines = manager.obtenir_racines_compte("Achats de marchandises", "charges")
    assert "601" in racines, "Compte 601 devrait être dans les achats de marchandises"
    
    # Test 4: Ventes de marchandises
    racines = manager.obtenir_racines_compte("Ventes de marchandises", "produits")
    assert "701" in racines, "Compte 701 devrait être dans les ventes de marchandises"
    
    # Test 5: Poste inexistant
    racines = manager.obtenir_racines_compte("Poste Inexistant", "bilan_actif")
    assert racines == [], "Poste inexistant devrait retourner une liste vide"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--hypothesis-show-statistics'])
