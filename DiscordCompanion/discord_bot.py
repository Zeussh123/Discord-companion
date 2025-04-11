#!/usr/bin/env python3
"""
Point d'entrée spécifique pour le bot Discord.
Ce fichier évite les conflits avec l'application web Flask.
Inclut un serveur web simple pour aider à maintenir le bot en ligne sur Replit.
"""
import logging
import os
from bot import run_bot
from keep_alive import keep_alive

# Configuration du logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def main():
    """
    Point d'entrée principal pour le bot Discord.
    Initialise et démarre le bot avec le token d'authentification.
    """
    logging.info("Démarrage du bot Discord en mode autonome...")
    
    # Démarrer le serveur web pour aider à maintenir le bot en vie
    logging.info("Démarrage du serveur web keep-alive...")
    keep_alive()
    logging.info("Serveur keep-alive démarré sur le port 8080.")
    
    # Récupération du token depuis les variables d'environnement
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logging.error("Aucun token Discord trouvé dans les variables d'environnement.")
        logging.error("Veuillez définir la variable DISCORD_TOKEN.")
        return
    
    # Démarrage du bot
    try:
        run_bot(token)
    except Exception as e:
        logging.error(f"Erreur lors du démarrage du bot: {e}")

if __name__ == "__main__":
    import sys
    
    # Ajouter un argument pour indiquer que nous sommes en mode bot Discord
    sys.argv.append("discord_mode") 
    main()