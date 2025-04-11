"""
Module autonome pour maintenir le bot Discord en ligne sur Replit.
Fournit un serveur web qui peut être pingé par des services externes.

Pour utilisation avec UpTimeRobot ou services similaires:
1. Ouvrir https://uptimerobot.com/ et créer un compte gratuit
2. Ajouter un nouveau moniteur de type "HTTP(s)"
3. Entrer l'URL de votre replit: https://[votre-replit].replit.app
4. Configurer pour vérifier toutes les 5 minutes
"""

import os
import logging
import time
from flask import Flask, jsonify
from threading import Thread

# Configuration du logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Application Flask pour le ping
app = Flask(__name__)
START_TIME = time.time()

@app.route('/')
def home():
    """Page d'accueil simple pour le ping."""
    uptime_seconds = int(time.time() - START_TIME)
    uptime_hours = uptime_seconds // 3600
    uptime_minutes = (uptime_seconds % 3600) // 60
    uptime_seconds = uptime_seconds % 60
    
    uptime_text = f"{uptime_hours}h {uptime_minutes}m {uptime_seconds}s"
    
    return f"""
    <html>
    <head>
        <title>Bot Discord - Administration</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
            .status {{ padding: 10px; border-radius: 5px; margin: 10px 0; }}
            .online {{ background-color: #d4edda; color: #155724; }}
            h1, h2 {{ color: #333; }}
            .uptime {{ font-weight: bold; }}
            .footer {{ margin-top: 30px; font-size: 0.8em; color: #777; }}
        </style>
    </head>
    <body>
        <h1>Bot Discord - Service de Messages Programmés</h1>
        <div class="status online">
            <h2>✅ Bot en ligne</h2>
            <p>Le bot Discord est actuellement en fonctionnement.</p>
            <p>Temps de fonctionnement: <span class="uptime">{uptime_text}</span></p>
        </div>
        <div class="footer">
            <p>Pour maintenir ce bot en ligne 24/7, configurez un service comme 
            <a href="https://uptimerobot.com/" target="_blank">UptimeRobot</a> pour ping cette URL toutes les 5 minutes.</p>
        </div>
    </body>
    </html>
    """

@app.route('/api/status')
def status():
    """Endpoint JSON pour vérifier le statut du bot."""
    return jsonify({
        "status": "online",
        "uptime_seconds": int(time.time() - START_TIME),
        "service": "Discord Bot - Message Scheduling Service"
    })

@app.route('/ping')
def ping():
    """Endpoint simple pour les services de ping."""
    return "pong"

def run():
    """Démarre le serveur Flask."""
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Démarrage du serveur keep-alive sur le port {port}")
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    """
    Crée un serveur web simple qui peut être pingé 
    régulièrement pour garder le bot en vie plus longtemps.
    """
    server_thread = Thread(target=run)
    server_thread.daemon = True  # Le thread s'arrêtera quand le programme principal s'arrête
    server_thread.start()
    logger.info("Serveur keep-alive démarré en arrière-plan")
    return server_thread

# Pour exécution directe (tests)
if __name__ == "__main__":
    keep_alive()
    logger.info("Serveur keep-alive démarré en mode test")
    # Maintenir le script en vie pour les tests
    try:
        while True:
            time.sleep(600)
    except KeyboardInterrupt:
        logger.info("Arrêt du serveur keep-alive")