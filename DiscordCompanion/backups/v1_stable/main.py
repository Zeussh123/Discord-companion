"""
Entry point for the Discord scheduled message bot.
This file supports both running the Discord bot directly and 
providing a simple web interface via Flask.
"""
import os
import logging
import threading
from flask import Flask, render_template_string, request
from bot import run_bot

# Set up logging for debugging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")

@app.route('/')
def index():
    """Simple status page."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Programmateur de messages Discord</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
    </head>
    <body>
        <div class="container mt-5">
            <div class="row">
                <div class="col-md-8 mx-auto">
                    <div class="card">
                        <div class="card-header">
                            <h2>Programmateur de messages Discord</h2>
                        </div>
                        <div class="card-body">
                            <h5>Statut du Bot</h5>
                            <p>Le bot Discord est actuellement <span class="badge bg-{{ 'success' if has_token else 'danger' }}">{{ "en ligne" if has_token else "hors ligne" }}</span></p>
                            
                            <h5>Commandes disponibles</h5>
                            <ul class="list-group mb-3">
                                <li class="list-group-item"><code>!schedule &lt;time&gt; &lt;message&gt;</code> - Programmer un message</li>
                                <li class="list-group-item"><code>!list</code> - Lister vos messages programmés</li>
                                <li class="list-group-item"><code>!cancel &lt;job_id&gt;</code> - Annuler un message programmé</li>
                            </ul>
                            
                            <h5>Format de l'heure</h5>
                            <ul class="list-group">
                                <li class="list-group-item"><code>YYYY-MM-DD HH:MM</code> - Date et heure complètes</li>
                                <li class="list-group-item"><code>HH:MM</code> - Heure aujourd'hui (ou demain si l'heure est déjà passée)</li>
                            </ul>
                            
                            <h5 class="mt-3">Fuseau horaire</h5>
                            <div class="alert alert-info">
                                <i class="bi bi-info-circle"></i> Toutes les heures sont en <strong>Europe/Paris (CET/CEST)</strong>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    token_available = os.getenv("DISCORD_TOKEN") is not None
    return render_template_string(html, has_token=token_available)

def start_bot():
    """Start the Discord bot in a separate thread."""
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logging.warning("Discord token not found. Bot will not start.")
        return
    
    try:
        logging.info("Starting Discord bot...")
        run_bot(token)
    except Exception as e:
        logging.error(f"Error starting bot: {e}")

if __name__ == "__main__":
    import subprocess
    import sys
    
    # Détection plus robuste du workflow
    try:
        # Vérifier le nom du processus parent (permettra d'identifier discord_bot workflow)
        ps_output = subprocess.check_output(['ps', '-p', str(os.getppid()), '-o', 'cmd'], text=True)
        logging.info(f"Parent process: {ps_output.strip()}")
        
        # Vérifier si le processus parent contient "discord_bot"
        is_discord_bot_workflow = "discord_bot" in ps_output
        
        # Récupérer le nom du workflow depuis l'environnement (pas toujours défini)
        workflow_name = os.environ.get("WORKFLOW_NAME", "")
        logging.info(f"WORKFLOW_NAME: {workflow_name}")
        
        # Si le nom du workflow contient "discord", nous sommes aussi en mode bot Discord
        is_discord_bot = is_discord_bot_workflow or workflow_name == "discord_bot"
        
        logging.info(f"Détection finale - Bot Discord uniquement: {is_discord_bot}")
        
        if is_discord_bot:
            logging.info("====== DÉMARRAGE EN MODE BOT DISCORD UNIQUEMENT ======")
            # Exécuter uniquement le bot Discord sans Flask
            start_bot()
        else:
            # En mode application web avec bot Discord en arrière-plan
            logging.info("====== DÉMARRAGE EN MODE APPLICATION WEB ======")
            
            # Vérifier si le port 5000 est déjà utilisé 
            # Si c'est le cas, nous utiliserons le port 5001
            port_to_use = 5001  # Toujours utiliser 5001 pour éviter les conflits
            try:
                # Même avec port_to_use=5001, nous vérifions si 5000 est utilisé
                # uniquement pour le logging
                import socket
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.bind(('0.0.0.0', 5000))
                s.close()
                logging.info("Port 5000 est libre, mais nous utiliserons 5001 par précaution")
                port_in_use = False
            except socket.error:
                logging.info("Port 5000 est déjà utilisé, utilisation de 5001")
                port_in_use = True
            
            # Toujours exécuter la partie web et bot, mais sur le port 5001
            logging.info(f"Démarrage en mode application web avec bot Discord en arrière-plan sur port {port_to_use}")
            
            # Démarrer le bot Discord dans un thread séparé
            bot_thread = threading.Thread(target=start_bot)
            bot_thread.daemon = True
            bot_thread.start()
            
            # Démarrer l'application Flask sur le port spécifié
            app.run(host="0.0.0.0", port=port_to_use)
    except Exception as e:
        logging.error(f"Erreur lors de la détection du mode: {e}")
        # En cas d'erreur, démarrer uniquement le bot Discord
        logging.info("Mode par défaut: démarrage du bot Discord uniquement")
        start_bot()
