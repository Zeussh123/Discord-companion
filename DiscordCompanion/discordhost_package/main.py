"""
Point d'entrée principal pour DiscordHost - Bot Discord de messages programmés et tickets
"""
import os
import logging
import discord
from dotenv import load_dotenv

# Importation de nos modules
from bot import run_bot

# Configuration de la journalisation
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

def main():
    """
    Point d'entrée principal pour le bot Discord sur DiscordHost.
    Initialise et démarre le bot avec le token d'authentification.
    """
    load_dotenv()  # Charge les variables d'environnement depuis .env si présent
    
    # Récupération du token Discord (priorité à la variable d'environnement)
    token = os.environ.get("DISCORD_TOKEN")
    
    if not token:
        logging.error("Token Discord non trouvé. Définissez DISCORD_TOKEN dans les variables d'environnement.")
        return

    # Démarrage du bot Discord
    logging.info("Démarrage du bot Discord...")
    run_bot(token)

if __name__ == "__main__":
    main()