"""
Module autonome pour maintenir le bot Discord en ligne sur Replit.
Fournit un serveur web qui peut être pingé par des services externes.

Pour utilisation avec UpTimeRobot ou services similaires:
1. Ouvrir https://uptimerobot.com/ et créer un compte gratuit
2. Ajouter un nouveau moniteur de type "HTTP(s)"
3. Entrer l'URL de votre serveur web local (par exemple http://localhost:8080)
4. Configurer pour vérifier toutes les 5 minutes
"""

import logging
import os
import threading
from flask import Flask, jsonify

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route("/")
def home():
    """Page d'accueil simple pour le ping."""
    return "Bot Discord en cours d'exécution"


@app.route("/status")
def status():
    """Endpoint JSON pour vérifier le statut du bot."""
    return jsonify({"status": "online", "uptime": "active"})


@app.route("/ping")
def ping():
    """Endpoint simple pour les services de ping."""
    return "pong"


def run():
    """Démarre le serveur Flask."""
    try:
        port = 8080  # Port par défaut
        app.run(host="0.0.0.0", port=port)
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du serveur web: {str(e)}")


def keep_alive():
    """
    Crée un serveur web simple qui peut être pingé 
    régulièrement pour garder le bot en vie plus longtemps.
    """
    logger.info(f"Démarrage du serveur keep-alive sur le port 8080")
    server_thread = threading.Thread(target=run)
    server_thread.daemon = True
    server_thread.start()
    logger.info("Serveur keep-alive démarré en arrière-plan")