# Guide d'installation locale du bot Discord

Ce guide vous explique comment installer et exécuter le bot sur votre ordinateur local ou PC virtuel.

## Prérequis

1. **Python 3.8+** installé sur votre machine
2. **Pip** (gestionnaire de paquets Python)
3. **Un token Discord valide** (obtenu sur [Discord Developer Portal](https://discord.com/developers/applications))

## Étapes d'installation

### 1. Préparer l'environnement

1. Créez un dossier pour votre bot
2. Téléchargez les fichiers suivants depuis Replit :
   - `bot.py`
   - `scheduler.py`
   - `ticket_manager.py`
   - `discord_bot.py` (pour exécuter le bot seul)
   - `tickets.json` (si vous avez déjà des tickets)

### 2. Installer les dépendances

Ouvrez un terminal (cmd, PowerShell, ou Terminal) dans le dossier du bot et exécutez :

```bash
pip install discord.py apscheduler pytz python-dotenv requests
```

### 3. Configurer le token Discord

Créez un fichier `.env` dans le dossier du bot avec le contenu suivant :

```
DISCORD_TOKEN=votre_token_discord_ici
```

Remplacez `votre_token_discord_ici` par votre vrai token Discord.

### 4. Vérifier l'activation des intents

Assurez-vous que l'intent "Message Content" est activé dans votre portail développeur Discord :
1. Allez sur https://discord.com/developers/applications
2. Sélectionnez votre application bot
3. Dans 'Bot', activez 'Message Content Intent'
4. Sauvegardez les changements

### 5. Démarrer le bot

Pour exécuter le bot en mode autonome (sans interface web), ouvrez un terminal dans le dossier du bot et exécutez :

```bash
python discord_bot.py
```

Vous devriez voir des logs indiquant que le bot se connecte à Discord, et finalement un message indiquant que le bot est prêt.

## Maintenance et exécution continue

### Pour Windows

Créez un fichier batch `start_bot.bat` avec le contenu suivant :

```bat
@echo off
echo Démarrage du bot Discord...
python discord_bot.py
pause
```

Double-cliquez sur ce fichier pour lancer le bot.

### Pour Linux/macOS

Créez un fichier shell `start_bot.sh` avec le contenu suivant :

```bash
#!/bin/bash
echo "Démarrage du bot Discord..."
python3 discord_bot.py
```

Rendez-le exécutable et lancez-le :

```bash
chmod +x start_bot.sh
./start_bot.sh
```

## Résolution des problèmes courants

### Le bot ne démarre pas

- Vérifiez que toutes les dépendances sont installées
- Assurez-vous que le fichier `.env` existe et contient le bon token
- Vérifiez que vous utilisez la bonne version de Python (3.8+)

### Le bot se connecte mais ne répond pas aux commandes

- Vérifiez que l'intent "Message Content" est activé dans le portail développeur Discord
- Assurez-vous que le bot a les permissions nécessaires dans votre serveur

### Les messages programmés ne s'envoient pas

- Vérifiez que le bot a la permission d'envoyer des messages dans les canaux concernés
- Assurez-vous que l'heure de votre PC est correctement synchronisée

## Notes importantes

- Ce bot utilise le fuseau horaire `Europe/Paris` par défaut
- Les tickets sont sauvegardés dans le fichier `tickets.json`
- Pour garder votre bot en ligne 24/7, vous devez maintenir votre PC allumé ou utiliser un service d'hébergement