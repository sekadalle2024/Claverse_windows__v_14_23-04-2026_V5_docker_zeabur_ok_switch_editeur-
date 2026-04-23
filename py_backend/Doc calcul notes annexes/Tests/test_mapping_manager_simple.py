"""
Test simple pour vérifier le fonctionnement du MappingManager.
"""

import sys
import os

# Ajouter le chemin des modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Modules'))

from mapping_manager import MappingManager, InvalidJSONException


def test_mapping_manager_basic():
    """Test basique du MappingManager."""
    print("=" * 60)
    print("TEST MAPPING MANAGER - FONCTIONNALITÉS DE BASE")
    print("=" * 60)
    
    # Test 1: Initialisation avec fichier par défaut
    print("\n1. Test d'initialisation...")
    try:
        # Utiliser le fichier existant dans Ressources
        fichier_json = os.path.join(
            os.path.dirname(__file__), 
            '..', 'Ressources', 
            'correspondances_syscohada.json'
        )
        manager = MappingManager(fichier_json)
        print("   ✓ MappingManager initialisé avec succès")
    except Exception as e:
        print(f"   ✗ Erreur d'initialisation: {e}")
        return False
    
    # Test 2: Charger les correspondances
    print("\n2. Test de chargement des correspondances...")
    try:
        correspondances = manager.charger_correspondances()
        sections = list(correspondances.keys())
        print(f"   ✓ Correspondances chargées: {len(sections)} sections")
        print(f"   Sections: {sections}")
    except Exception as e:
        print(f"   ✗ Erreur de chargement: {e}")
        return False
    
    # Test 3: Obtenir racines de compte
    print("\n3. Test d'obtention des racines de compte...")
    try:
        # Test avec un poste existant
        racines = manager.obtenir_racines_compte(
            "Immobilisations incorporelles", 
            "bilan_actif"
        )
        print(f"   ✓ Racines obtenues: {racines}")
        
        # Test avec un poste inexistant
        racines_vides = manager.obtenir_racines_compte(
            "Poste Inexistant", 
            "bilan_actif"
        )
        print(f"   ✓ Poste inexistant retourne: {racines_vides}")
    except Exception as e:
        print(f"   ✗ Erreur d'obtention des racines: {e}")
        return False
    
    # Test 4: Valider racines
    print("\n4. Test de validation des racines...")
    try:
        # Racines valides
        valide, invalides = manager.valider_racines(["211", "212", "213"])
        print(f"   ✓ Racines valides: {valide}, invalides: {invalides}")
        
        # Racines invalides
        valide, invalides = manager.valider_racines(["211", "ABC", "213"])
        print(f"   ✓ Racines mixtes: valide={valide}, invalides={invalides}")
    except Exception as e:
        print(f"   ✗ Erreur de validation: {e}")
        return False
    
    # Test 5: Ajouter correspondance
    print("\n5. Test d'ajout de correspondance...")
    try:
        manager.ajouter_correspondance(
            "Test Poste", 
            "bilan_actif", 
            ["999"]
        )
        racines_test = manager.obtenir_racines_compte("Test Poste", "bilan_actif")
        print(f"   ✓ Correspondance ajoutée: {racines_test}")
    except Exception as e:
        print(f"   ✗ Erreur d'ajout: {e}")
        return False
    
    # Test 6: Gestion des exceptions
    print("\n6. Test de gestion des exceptions...")
    try:
        manager_invalide = MappingManager("fichier_inexistant.json")
        print("   ✗ Exception non levée pour fichier inexistant")
        return False
    except InvalidJSONException as e:
        print(f"   ✓ InvalidJSONException levée correctement: {e}")
    except Exception as e:
        print(f"   ✗ Exception inattendue: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✓ TOUS LES TESTS RÉUSSIS")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_mapping_manager_basic()
    sys.exit(0 if success else 1)
