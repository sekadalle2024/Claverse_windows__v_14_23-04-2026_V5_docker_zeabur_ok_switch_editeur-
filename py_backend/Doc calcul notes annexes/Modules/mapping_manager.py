"""
Module de gestion des correspondances SYSCOHADA.

Ce module gère le mapping entre les postes des états financiers et les comptes comptables.
"""

import json
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class InvalidJSONException(Exception):
    """Exception levée quand le fichier JSON est invalide."""
    pass


class MappingManager:
    """Gestionnaire des correspondances SYSCOHADA."""
    
    def __init__(self, fichier_json: str = None):
        """
        Charge le fichier de correspondances.
        
        Args:
            fichier_json: Chemin vers le fichier JSON (optionnel)
        """
        if fichier_json is None:
            # Chemin par défaut vers le fichier dans Ressources
            fichier_json = "../Ressources/correspondances_syscohada.json"
        
        self.fichier_json = fichier_json
        self.correspondances = self.charger_correspondances()
        logger.info(f"MappingManager initialisé avec {fichier_json}")
    
    def charger_correspondances(self) -> Dict:
        """
        Charge le fichier JSON.
        
        Returns:
            Dict avec les 4 sections: bilan_actif, bilan_passif, charges, produits
            
        Raises:
            InvalidJSONException: Si le JSON est invalide
        """
        try:
            with open(self.fichier_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Vérifier la structure
            sections_requises = ['bilan_actif', 'bilan_passif', 'charges', 'produits']
            for section in sections_requises:
                if section not in data:
                    logger.warning(f"Section '{section}' manquante dans le JSON")
            
            logger.info(f"✓ Correspondances chargées: {len(data)} sections")
            return data
            
        except FileNotFoundError:
            logger.error(f"Fichier JSON introuvable: {self.fichier_json}")
            raise InvalidJSONException(f"Fichier introuvable: {self.fichier_json}")
        except json.JSONDecodeError as e:
            logger.error(f"Erreur de syntaxe JSON: {e}")
            raise InvalidJSONException(f"JSON invalide: {e}")
    
    def obtenir_racines_compte(self, poste: str, section: str) -> List[str]:
        """
        Retourne les racines de comptes pour un poste.
        
        Si plusieurs entrées ont le même libellé, retourne toutes les racines combinées.
        
        Args:
            poste: Nom du poste (ex: "Immobilisations incorporelles")
            section: Section (bilan_actif, bilan_passif, charges, produits)
            
        Returns:
            Liste des racines de comptes (dédupliquée)
        """
        if section not in self.correspondances:
            logger.warning(f"Section '{section}' introuvable")
            return []
        
        section_data = self.correspondances[section]
        
        # Gérer le format liste (nouveau format)
        if isinstance(section_data, list):
            racines_trouvees = []
            for item in section_data:
                if isinstance(item, dict) and item.get('libelle') == poste:
                    racines_trouvees.extend(item.get('racines', []))
            
            if not racines_trouvees:
                logger.warning(f"Poste '{poste}' introuvable dans la section '{section}'")
                return []
            
            # Dédupliquer tout en préservant l'ordre
            seen = set()
            result = []
            for racine in racines_trouvees:
                if racine not in seen:
                    seen.add(racine)
                    result.append(racine)
            return result
        
        # Gérer le format dict (ancien format)
        if poste not in section_data:
            logger.warning(f"Poste '{poste}' introuvable dans la section '{section}'")
            return []
        
        poste_data = section_data[poste]
        
        # Gérer les structures avec 'brut' et 'amort' ou directement une liste
        if isinstance(poste_data, dict):
            if 'brut' in poste_data:
                return poste_data['brut']
            elif 'amort' in poste_data:
                return poste_data['amort']
        elif isinstance(poste_data, list):
            return poste_data
        
        return []
    
    def obtenir_comptes_brut_amort(self, poste: str, section: str) -> Tuple[List[str], List[str]]:
        """
        Retourne les comptes brut et amortissement pour un poste.
        
        Args:
            poste: Nom du poste
            section: Section
            
        Returns:
            Tuple (comptes_brut, comptes_amort)
        """
        if section not in self.correspondances:
            return [], []
        
        section_data = self.correspondances[section]
        
        # Gérer le format liste (nouveau format)
        if isinstance(section_data, list):
            for item in section_data:
                if isinstance(item, dict) and item.get('libelle') == poste:
                    # Dans le nouveau format, on ne distingue pas brut/amort
                    # On retourne les racines comme brut, et liste vide pour amort
                    return item.get('racines', []), []
            return [], []
        
        # Gérer le format dict (ancien format)
        if poste not in section_data:
            return [], []
        
        poste_data = section_data[poste]
        
        if isinstance(poste_data, dict):
            comptes_brut = poste_data.get('brut', [])
            comptes_amort = poste_data.get('amort', [])
            return comptes_brut, comptes_amort
        
        return [], []
    
    def valider_racines(self, racines: List[str]) -> Tuple[bool, List[str]]:
        """
        Valide que les racines sont des chaînes numériques valides.
        
        Args:
            racines: Liste de racines à valider
            
        Returns:
            Tuple (valide: bool, racines_invalides: List[str])
        """
        racines_invalides = []
        
        for racine in racines:
            if not isinstance(racine, str):
                racines_invalides.append(str(racine))
            elif not racine.isdigit():
                racines_invalides.append(racine)
        
        if racines_invalides:
            logger.warning(f"Racines invalides détectées: {racines_invalides}")
            return False, racines_invalides
        
        return True, []
    
    def ajouter_correspondance(self, poste: str, section: str, racines: List[str]):
        """
        Ajoute une nouvelle correspondance au mapping.
        
        Args:
            poste: Nom du poste
            section: Section
            racines: Liste des racines de comptes
        """
        if section not in self.correspondances:
            self.correspondances[section] = []
        
        section_data = self.correspondances[section]
        
        # Gérer le format liste (nouveau format)
        if isinstance(section_data, list):
            # Vérifier si le poste existe déjà
            for item in section_data:
                if isinstance(item, dict) and item.get('libelle') == poste:
                    # Mettre à jour les racines existantes
                    item['racines'] = racines
                    logger.info(f"✓ Correspondance mise à jour: {section}.{poste}")
                    return
            
            # Ajouter un nouveau poste
            ref = f"Z{len(section_data)}"  # Générer une référence automatique
            section_data.append({
                "ref": ref,
                "libelle": poste,
                "racines": racines
            })
            logger.info(f"✓ Correspondance ajoutée: {section}.{poste}")
        else:
            # Gérer le format dict (ancien format)
            section_data[poste] = racines
            logger.info(f"✓ Correspondance ajoutée: {section}.{poste}")
    
    def sauvegarder(self):
        """Sauvegarde les correspondances dans le fichier JSON."""
        try:
            with open(self.fichier_json, 'w', encoding='utf-8') as f:
                json.dump(self.correspondances, f, indent=2, ensure_ascii=False)
            logger.info(f"✓ Correspondances sauvegardées: {self.fichier_json}")
            return True
        except Exception as e:
            logger.error(f"✗ Erreur lors de la sauvegarde: {e}")
            return False
