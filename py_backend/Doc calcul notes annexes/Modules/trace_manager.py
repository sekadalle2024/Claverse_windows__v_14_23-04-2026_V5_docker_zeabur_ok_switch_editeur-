"""
Module: Trace_Manager
Responsabilité: Traçabilité et audit des calculs des notes annexes

Ce module gère l'enregistrement complet de tous les calculs effectués pour chaque note annexe,
permettant une traçabilité complète et un audit des montants générés.

Author: Claraverse
Date: 2026-04-23
"""

import json
import csv
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


class TraceManager:
    """
    Gestionnaire de traces pour l'audit et la traçabilité des calculs.
    
    Cette classe enregistre tous les calculs effectués pour une note annexe,
    incluant les comptes sources, les montants calculés, et les métadonnées
    de génération. Elle permet l'export en JSON et CSV, et gère l'historique
    des 10 dernières générations.
    
    Attributes:
        numero_note (str): Numéro de la note (ex: "3A", "3B", etc.)
        trace_data (Dict): Données de trace accumulées
        traces_dir (Path): Répertoire de stockage des traces
    """
    
    def __init__(self, numero_note: str):
        """
        Initialise le gestionnaire de traces pour une note spécifique.
        
        Args:
            numero_note: Numéro de la note annexe (ex: "3A", "3B", "4", etc.)
        
        Example:
            >>> trace_mgr = TraceManager("3A")
            >>> trace_mgr.numero_note
            '3A'
        """
        self.numero_note = numero_note
        self.trace_data: Dict[str, Any] = {
            "note": numero_note,
            "titre": "",
            "date_generation": None,
            "fichier_balance": "",
            "hash_md5_balance": "",
            "lignes": [],
            "total": {}
        }
        
        # Créer le répertoire de traces s'il n'existe pas
        self.traces_dir = Path("py_backend/Doc calcul notes annexes/Traces")
        self.traces_dir.mkdir(parents=True, exist_ok=True)
    
    def enregistrer_calcul(
        self,
        libelle: str,
        montant: float,
        comptes_sources: List[Dict[str, Any]]
    ) -> None:
        """
        Enregistre un calcul avec ses sources pour traçabilité.
        
        Cette méthode enregistre une ligne de calcul avec tous les comptes sources
        qui ont contribué au montant calculé. Chaque compte source inclut son numéro,
        son intitulé, et les valeurs extraites.
        
        Args:
            libelle: Libellé de la ligne calculée (ex: "Frais de recherche et de développement")
            montant: Montant calculé pour cette ligne
            comptes_sources: Liste des comptes sources avec leurs détails
                Chaque dict doit contenir:
                - compte (str): Numéro du compte
                - intitule (str): Libellé du compte
                - valeur (float): Valeur extraite du compte
                - type_valeur (str): Type de valeur (ex: "brut_ouverture", "dotations")
        
        Example:
            >>> trace_mgr = TraceManager("3A")
            >>> comptes = [
            ...     {
            ...         "compte": "211",
            ...         "intitule": "Frais de recherche et de développement",
            ...         "valeur": 1500000.0,
            ...         "type_valeur": "brut_ouverture"
            ...     }
            ... ]
            >>> trace_mgr.enregistrer_calcul("Frais R&D", 1500000.0, comptes)
            >>> len(trace_mgr.trace_data["lignes"])
            1
        """
        ligne_trace = {
            "libelle": libelle,
            "montant": montant,
            "comptes_sources": comptes_sources,
            "timestamp": datetime.now().isoformat()
        }
        
        self.trace_data["lignes"].append(ligne_trace)
    
    def enregistrer_metadata(
        self,
        fichier_balance: str,
        hash_md5: Optional[str] = None,
        titre_note: Optional[str] = None
    ) -> None:
        """
        Enregistre les métadonnées de génération de la note.
        
        Cette méthode enregistre les informations contextuelles sur la génération
        de la note: fichier source, hash MD5 pour vérification d'intégrité,
        titre de la note, et horodatage.
        
        Args:
            fichier_balance: Chemin du fichier de balance utilisé
            hash_md5: Hash MD5 du fichier de balance (calculé automatiquement si None)
            titre_note: Titre complet de la note (ex: "Immobilisations incorporelles")
        
        Example:
            >>> trace_mgr = TraceManager("3A")
            >>> trace_mgr.enregistrer_metadata(
            ...     "P000 -BALANCE DEMO N_N-1_N-2.xlsx",
            ...     titre_note="Immobilisations incorporelles"
            ... )
            >>> trace_mgr.trace_data["fichier_balance"]
            'P000 -BALANCE DEMO N_N-1_N-2.xlsx'
        """
        self.trace_data["fichier_balance"] = fichier_balance
        self.trace_data["date_generation"] = datetime.now().isoformat()
        
        if titre_note:
            self.trace_data["titre"] = titre_note
        
        # Calculer le hash MD5 si non fourni
        if hash_md5 is None and Path(fichier_balance).exists():
            hash_md5 = self._calculer_md5(fichier_balance)
        
        self.trace_data["hash_md5_balance"] = hash_md5 or ""
    
    def _calculer_md5(self, fichier: str) -> str:
        """
        Calcule le hash MD5 d'un fichier.
        
        Args:
            fichier: Chemin du fichier
        
        Returns:
            Hash MD5 en hexadécimal
        """
        hash_md5 = hashlib.md5()
        
        try:
            with open(fichier, "rb") as f:
                # Lire par blocs pour gérer les gros fichiers
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            print(f"⚠️  Erreur lors du calcul MD5: {e}")
            return ""
    
    def sauvegarder_trace(self, fichier_sortie: Optional[str] = None) -> str:
        """
        Sauvegarde la trace en format JSON.
        
        Cette méthode génère un fichier JSON contenant toutes les traces de calcul
        avec un nom de fichier horodaté. Le fichier est sauvegardé dans le répertoire
        de traces.
        
        Args:
            fichier_sortie: Nom du fichier de sortie (généré automatiquement si None)
                Format par défaut: trace_note_XX_AAAAMMJJ_HHMMSS.json
        
        Returns:
            Chemin complet du fichier de trace sauvegardé
        
        Example:
            >>> trace_mgr = TraceManager("3A")
            >>> trace_mgr.enregistrer_metadata("balance.xlsx")
            >>> fichier = trace_mgr.sauvegarder_trace()
            >>> Path(fichier).exists()
            True
        """
        # Générer le nom de fichier si non fourni
        if fichier_sortie is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            fichier_sortie = f"trace_note_{self.numero_note}_{timestamp}.json"
        
        # Chemin complet
        chemin_complet = self.traces_dir / fichier_sortie
        
        # Sauvegarder en JSON avec indentation pour lisibilité
        try:
            with open(chemin_complet, 'w', encoding='utf-8') as f:
                json.dump(self.trace_data, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Trace sauvegardée: {chemin_complet}")
            return str(chemin_complet)
        
        except Exception as e:
            print(f"✗ Erreur lors de la sauvegarde de la trace: {e}")
            raise
    
    def exporter_csv(self, fichier_sortie: Optional[str] = None) -> str:
        """
        Exporte la trace en format CSV pour analyse dans Excel.
        
        Cette méthode convertit les données de trace JSON en format CSV tabulaire,
        facilitant l'analyse dans Excel. Chaque ligne de calcul devient une ligne CSV
        avec les comptes sources dénormalisés.
        
        Args:
            fichier_sortie: Nom du fichier CSV de sortie (généré automatiquement si None)
                Format par défaut: trace_note_XX_AAAAMMJJ_HHMMSS.csv
        
        Returns:
            Chemin complet du fichier CSV exporté
        
        Example:
            >>> trace_mgr = TraceManager("3A")
            >>> trace_mgr.enregistrer_metadata("balance.xlsx")
            >>> comptes = [{"compte": "211", "intitule": "Frais R&D", "valeur": 1500000.0, "type_valeur": "brut"}]
            >>> trace_mgr.enregistrer_calcul("Frais R&D", 1500000.0, comptes)
            >>> fichier = trace_mgr.exporter_csv()
            >>> Path(fichier).exists()
            True
        """
        # Générer le nom de fichier si non fourni
        if fichier_sortie is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            fichier_sortie = f"trace_note_{self.numero_note}_{timestamp}.csv"
        
        # Chemin complet
        chemin_complet = self.traces_dir / fichier_sortie
        
        try:
            with open(chemin_complet, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                
                # En-têtes
                writer.writerow([
                    'Note',
                    'Titre',
                    'Date Génération',
                    'Fichier Balance',
                    'Hash MD5',
                    'Libellé Ligne',
                    'Montant',
                    'Compte Source',
                    'Intitulé Compte',
                    'Valeur Compte',
                    'Type Valeur'
                ])
                
                # Métadonnées communes
                note = self.trace_data.get("note", "")
                titre = self.trace_data.get("titre", "")
                date_gen = self.trace_data.get("date_generation", "")
                fichier_bal = self.trace_data.get("fichier_balance", "")
                hash_md5 = self.trace_data.get("hash_md5_balance", "")
                
                # Lignes de calcul
                for ligne in self.trace_data.get("lignes", []):
                    libelle = ligne.get("libelle", "")
                    montant = ligne.get("montant", 0.0)
                    comptes_sources = ligne.get("comptes_sources", [])
                    
                    # Si pas de comptes sources, écrire une ligne avec le montant
                    if not comptes_sources:
                        writer.writerow([
                            note, titre, date_gen, fichier_bal, hash_md5,
                            libelle, montant, "", "", "", ""
                        ])
                    else:
                        # Une ligne par compte source
                        for compte in comptes_sources:
                            writer.writerow([
                                note,
                                titre,
                                date_gen,
                                fichier_bal,
                                hash_md5,
                                libelle,
                                montant,
                                compte.get("compte", ""),
                                compte.get("intitule", ""),
                                compte.get("valeur", 0.0),
                                compte.get("type_valeur", "")
                            ])
            
            print(f"✓ Trace exportée en CSV: {chemin_complet}")
            return str(chemin_complet)
        
        except Exception as e:
            print(f"✗ Erreur lors de l'export CSV: {e}")
            raise
    
    def gerer_historique(self, max_historique: int = 10) -> None:
        """
        Conserve uniquement les N dernières générations de traces.
        
        Cette méthode nettoie automatiquement les anciennes traces pour éviter
        l'accumulation de fichiers. Elle conserve les max_historique fichiers
        les plus récents et supprime les plus anciens.
        
        Args:
            max_historique: Nombre maximum de traces à conserver (défaut: 10)
        
        Example:
            >>> trace_mgr = TraceManager("3A")
            >>> trace_mgr.gerer_historique(max_historique=5)
            >>> # Conserve uniquement les 5 traces les plus récentes
        """
        # Lister tous les fichiers de trace pour cette note
        pattern = f"trace_note_{self.numero_note}_*.json"
        fichiers_trace = sorted(
            self.traces_dir.glob(pattern),
            key=lambda p: p.stat().st_mtime,
            reverse=True  # Plus récent en premier
        )
        
        # Supprimer les fichiers au-delà de max_historique
        fichiers_a_supprimer = fichiers_trace[max_historique:]
        
        for fichier in fichiers_a_supprimer:
            try:
                fichier.unlink()
                print(f"✓ Trace ancienne supprimée: {fichier.name}")
            except Exception as e:
                print(f"⚠️  Erreur lors de la suppression de {fichier.name}: {e}")
        
        if fichiers_a_supprimer:
            print(f"✓ Historique nettoyé: {len(fichiers_a_supprimer)} trace(s) supprimée(s)")
        else:
            print(f"✓ Historique OK: {len(fichiers_trace)} trace(s) conservée(s)")
    
    def ajouter_total(self, total_data: Dict[str, float]) -> None:
        """
        Ajoute les totaux calculés à la trace.
        
        Args:
            total_data: Dictionnaire des totaux (brut_ouverture, vnc_cloture, etc.)
        
        Example:
            >>> trace_mgr = TraceManager("3A")
            >>> trace_mgr.ajouter_total({
            ...     "brut_ouverture": 5000000.0,
            ...     "vnc_cloture": 3500000.0
            ... })
            >>> trace_mgr.trace_data["total"]["brut_ouverture"]
            5000000.0
        """
        self.trace_data["total"] = total_data
    
    def obtenir_trace(self) -> Dict[str, Any]:
        """
        Retourne les données de trace actuelles.
        
        Returns:
            Dictionnaire contenant toutes les données de trace
        
        Example:
            >>> trace_mgr = TraceManager("3A")
            >>> trace = trace_mgr.obtenir_trace()
            >>> trace["note"]
            '3A'
        """
        return self.trace_data.copy()


# Exemple d'utilisation
if __name__ == "__main__":
    print("=== Test du TraceManager ===\n")
    
    # Créer un gestionnaire de traces
    trace_mgr = TraceManager("3A")
    
    # Enregistrer les métadonnées
    trace_mgr.enregistrer_metadata(
        fichier_balance="P000 -BALANCE DEMO N_N-1_N-2.xlsx",
        titre_note="Immobilisations incorporelles"
    )
    
    # Enregistrer quelques calculs
    comptes_sources_1 = [
        {
            "compte": "211",
            "intitule": "Frais de recherche et de développement",
            "valeur": 1500000.0,
            "type_valeur": "brut_ouverture"
        }
    ]
    trace_mgr.enregistrer_calcul(
        "Frais de recherche et de développement",
        1500000.0,
        comptes_sources_1
    )
    
    comptes_sources_2 = [
        {
            "compte": "2811",
            "intitule": "Amortissements frais de recherche",
            "valeur": 300000.0,
            "type_valeur": "amort_ouverture"
        }
    ]
    trace_mgr.enregistrer_calcul(
        "Amortissements frais R&D",
        300000.0,
        comptes_sources_2
    )
    
    # Ajouter les totaux
    trace_mgr.ajouter_total({
        "brut_ouverture": 5000000.0,
        "brut_cloture": 5500000.0,
        "vnc_ouverture": 4000000.0,
        "vnc_cloture": 4200000.0
    })
    
    # Sauvegarder en JSON
    fichier_json = trace_mgr.sauvegarder_trace()
    print(f"\n✓ Fichier JSON créé: {fichier_json}")
    
    # Exporter en CSV
    fichier_csv = trace_mgr.exporter_csv()
    print(f"✓ Fichier CSV créé: {fichier_csv}")
    
    # Gérer l'historique
    print("\n--- Gestion de l'historique ---")
    trace_mgr.gerer_historique(max_historique=10)
    
    print("\n=== Test terminé avec succès ===")
