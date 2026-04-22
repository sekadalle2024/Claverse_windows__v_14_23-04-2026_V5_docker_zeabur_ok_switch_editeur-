"""
Module de calcul des valeurs nettes comptables (VNC).

Ce module calcule les VNC en soustrayant les amortissements des valeurs brutes,
extrait les dotations et reprises d'amortissements, et valide que les VNC sont positives.
"""

import logging
from typing import Tuple, List
import pandas as pd

logger = logging.getLogger(__name__)


class VNCCalculator:
    """Calculateur de valeurs nettes comptables."""
    
    @staticmethod
    def calculer_vnc_ouverture(brut_ouverture: float, amort_ouverture: float) -> float:
        """
        Calcule VNC Ouverture = Brut Ouverture - Amortissement Ouverture.
        
        Args:
            brut_ouverture: Valeur brute d'ouverture
            amort_ouverture: Amortissement d'ouverture
            
        Returns:
            VNC d'ouverture
        """
        return brut_ouverture - amort_ouverture
    
    @staticmethod
    def calculer_vnc_cloture(brut_cloture: float, amort_cloture: float) -> float:
        """
        Calcule VNC Clôture = Brut Clôture - Amortissement Clôture.
        
        Args:
            brut_cloture: Valeur brute de clôture
            amort_cloture: Amortissement de clôture
            
        Returns:
            VNC de clôture
        """
        return brut_cloture - amort_cloture
    
    @staticmethod
    def extraire_dotations(comptes_amort: List[str], balance_n: pd.DataFrame) -> float:
        """
        Extrait les dotations aux amortissements (mouvements crédit 28X/29X).
        
        Les dotations correspondent aux mouvements crédit des comptes d'amortissement,
        car ils augmentent le montant des amortissements cumulés.
        
        Args:
            comptes_amort: Liste des racines de comptes d'amortissement
            balance_n: Balance de l'exercice N
            
        Returns:
            Total des dotations aux amortissements
        """
        from .account_extractor import AccountExtractor
        
        extractor = AccountExtractor(balance_n)
        total_dotations = 0.0
        
        for compte in comptes_amort:
            soldes = extractor.extraire_solde_compte(compte)
            # Dotations = mouvements crédit (augmentation de l'amortissement)
            total_dotations += soldes['mvt_credit']
        
        logger.debug(
            f"Dotations extraites pour comptes {comptes_amort}: {total_dotations:.2f}"
        )
        
        return total_dotations
    
    @staticmethod
    def extraire_reprises(comptes_amort: List[str], balance_n: pd.DataFrame) -> float:
        """
        Extrait les reprises d'amortissements (mouvements débit 28X/29X).
        
        Les reprises correspondent aux mouvements débit des comptes d'amortissement,
        car ils diminuent le montant des amortissements cumulés (lors de cessions).
        
        Args:
            comptes_amort: Liste des racines de comptes d'amortissement
            balance_n: Balance de l'exercice N
            
        Returns:
            Total des reprises d'amortissements
        """
        from .account_extractor import AccountExtractor
        
        extractor = AccountExtractor(balance_n)
        total_reprises = 0.0
        
        for compte in comptes_amort:
            soldes = extractor.extraire_solde_compte(compte)
            # Reprises = mouvements débit (diminution de l'amortissement)
            total_reprises += soldes['mvt_debit']
        
        logger.debug(
            f"Reprises extraites pour comptes {comptes_amort}: {total_reprises:.2f}"
        )
        
        return total_reprises
    
    @staticmethod
    def valider_vnc(vnc: float, libelle: str = "") -> Tuple[bool, str]:
        """
        Valide que VNC >= 0.
        
        Une VNC négative indique une anomalie comptable (amortissement supérieur
        à la valeur brute), ce qui nécessite un avertissement.
        
        Args:
            vnc: Valeur nette comptable à valider
            libelle: Libellé de la ligne (pour le message d'avertissement)
            
        Returns:
            Tuple (valide: bool, message_avertissement: str)
        """
        if vnc < 0:
            message = (
                f"VNC négative détectée pour '{libelle}': {vnc:.2f}. "
                f"L'amortissement dépasse la valeur brute."
            )
            logger.warning(message)
            return False, message
        
        return True, ""
