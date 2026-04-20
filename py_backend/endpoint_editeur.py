"""
Endpoint Editeur - Test de Switch Backend
==========================================

Endpoint simple pour tester le switch entre localhost et serveurs cloud.
Retourne simplement le message reçu pour valider la communication.

Version: 1.0.0
Date: 20 Avril 2026
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

# Configuration du logger
logger = logging.getLogger(__name__)

# Créer le router
router = APIRouter(prefix="/editeur", tags=["editeur"])


class EditeurRequest(BaseModel):
    """Modèle de requête pour l'endpoint éditeur"""
    command: str
    message: Optional[str] = None


class EditeurResponse(BaseModel):
    """Modèle de réponse pour l'endpoint éditeur"""
    success: bool
    command: str
    message: str
    server_info: dict


@router.post("/process", response_model=EditeurResponse)
async def process_editeur(request: EditeurRequest):
    """
    Endpoint de test qui retourne le message reçu.
    
    Args:
        request: Requête contenant la commande et le message
        
    Returns:
        EditeurResponse avec le message reçu et les infos serveur
    """
    try:
        logger.info(f"📝 Endpoint Editeur - Commande reçue: {request.command}")
        
        # Construire la réponse
        response = EditeurResponse(
            success=True,
            command=request.command,
            message=request.message or request.command,
            server_info={
                "endpoint": "/editeur/process",
                "status": "operational",
                "version": "1.0.0"
            }
        )
        
        logger.info(f"✅ Réponse envoyée: {response.message}")
        return response
        
    except Exception as e:
        logger.error(f"❌ Erreur dans endpoint_editeur: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur de traitement: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Endpoint de santé pour vérifier que le service est opérationnel"""
    return {
        "status": "healthy",
        "endpoint": "editeur",
        "version": "1.0.0"
    }
