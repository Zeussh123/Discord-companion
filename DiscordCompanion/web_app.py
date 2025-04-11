#!/usr/bin/env python3
"""
Point d'entrée pour l'application web Flask.
Démarre également le bot Discord en arrière-plan.
"""
import logging
import os
import threading
from main import app, start_bot

# Configuration du logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def main():
    """
    Point d'entrée principal pour l'application web.
    Démarre le bot Discord en arrière-plan puis lance l'application Flask.
    """
    logging.info("Démarrage de l'application web avec bot Discord en arrière-plan...")
    
    # Démarrer le bot Discord dans un thread séparé
    bot_thread = threading.Thread(target=start_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Démarrer l'application Flask sur le port 5000
    app.run(host="0.0.0.0", port=5000)

if __name__ == "__main__":
    main()