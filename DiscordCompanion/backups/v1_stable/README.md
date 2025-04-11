# Bot Discord de Programmation de Messages

## Version stable du 19 mars 2025

Ce bot Discord permet de programmer des messages pour qu'ils soient envoyés automatiquement à des heures précises dans des canaux spécifiques.

## Fonctionnalités

- ✅ Programmation de messages à des heures précises
- ✅ Envoi dans le canal actuel ou un canal spécifié
- ✅ Support complet des messages avec sauts de ligne
- ✅ Affichage correct du nom de l'utilisateur qui a programmé le message
- ✅ Listage des messages programmés
- ✅ Annulation de messages programmés
- ✅ Interface web de gestion (Flask)

## Commandes

- `!schedule <heure> [#canal] <message>` - Programme un message
  - Format d'heure : `HH:MM` (aujourd'hui/demain) ou `YYYY-MM-DD HH:MM`
  - Exemple : `!schedule 15:30 Bonjour tout le monde !`
  - Exemple avec canal : `!schedule 15:30 #général Bonjour tout le monde !`

- `!list` - Liste tous vos messages programmés

- `!cancel <id>` - Annule un message programmé spécifique
  - Exemple : `!cancel abc123`

- `!cancel all` - Annule tous vos messages programmés

- `!testmsg <message>` - Teste l'envoi d'un message immédiat (après 5 secondes)

## Configuration

Assurez-vous d'activer l'intent `message_content` dans le portail développeur Discord.

## Notes de développement

- Le bot utilise discord.py v2.5+
- Gestion des timezones avec pytz (Europe/Paris)
- Système de vérification périodique avec asyncio
- Architecture modulaire avec classe MessageScheduler