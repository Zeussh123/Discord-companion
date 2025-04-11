# Bot Discord de Messages Programmés et Tickets

Ce bot Discord propose deux fonctionnalités principales :
1. **Programmation de messages** - Permet aux utilisateurs de programmer l'envoi automatique de messages à des dates et heures précises
2. **Système de tickets anonymes** - Permet aux utilisateurs d'envoyer des feedbacks anonymes aux administrateurs

## Configuration pour DiscordHost

### Prérequis
- Un token de bot Discord (disponible sur le [Portail développeur Discord](https://discord.com/developers/applications))
- Les intents `message_content` activés dans le portail développeur Discord

### Installation
1. Uploadez les fichiers suivants sur DiscordHost :
   - `bot.py`
   - `scheduler.py`
   - `ticket_manager.py`
   - `discord_host_main.py` (renommez-le en `main.py` sur DiscordHost)
   - `discordhost_requirements.txt` (renommez-le en `requirements.txt` sur DiscordHost)
   - `tickets.json` (si vous avez déjà des tickets)

2. Configurez les variables d'environnement :
   - `DISCORD_TOKEN` : Votre token de bot Discord

3. Vérifiez que l'intent Message Content est activé :
   - Allez sur https://discord.com/developers/applications
   - Sélectionnez votre application bot
   - Dans 'Bot', activez 'Message Content Intent'
   - Sauvegardez les changements

### Commandes disponibles

#### Messages programmés
- `!schedule HH:MM [#canal] message` - Programme un message
- `!schedule YYYY-MM-DD HH:MM [#canal] message` - Programme un message à une date précise
- `!list` - Liste tous vos messages programmés
- `!cancel ID` ou `!cancel all` - Annule un ou tous vos messages programmés
- `!testmsg message` - Teste l'envoi immédiat d'un message (après 5 secondes)

#### Système de tickets
- `!feedback message` - Envoie un feedback anonyme
- `!reply ID message` - Répond à un ticket (admin uniquement)
- `!tickets` - Liste tous les tickets ouverts (admin uniquement)
- `!close ID` - Ferme un ticket (admin uniquement)
- `!setticketschannel` - Définit le canal actuel comme canal de tickets (admin uniquement)

## Dépannage
- Si le bot ne répond pas aux commandes, vérifiez que l'intent Message Content est activé
- Si les messages programmés ne s'envoient pas, vérifiez que le bot a les permissions nécessaires dans les canaux
- Pour tout autre problème, consultez les logs sur DiscordHost

## Notes supplémentaires
- Le fuseau horaire configuré est `Europe/Paris` (France)
- Les tickets sont sauvegardés dans `tickets.json`
- Toutes les commandes sont insensibles à la casse