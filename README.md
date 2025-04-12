Bot Discord Companion
Description
Bot Discord Companion est un bot Discord conçu pour gérer des avis anonymes, surveiller les serveurs, et modérer les utilisateurs en appliquant des restrictions sur les messages contenant des mots interdits. Il inclut des fonctionnalités de gestion des avertissements et d'expulsion automatique après plusieurs récidives.

Fonctionnalités
Commandes principales
!avis <message>
Soumettez un avis anonyme.
Exemple : !avis J'aime ce serveur !

!repondre <ID> <message>
Répondez à un avis anonyme en utilisant son ID.
Exemple : !repondre a1B2c3 Merci pour votre retour !

!tickets
Affiche tous les avis anonymes en cours.
Exemple : !tickets

!historique
Affiche l'historique des avis anonymes avec leurs réponses.
Exemple : !historique

!supprimer <ID>
Supprime un ticket spécifique en utilisant son ID.
Exemple : !supprimer a1B2c3

!supprimer_tous
Supprime tous les tickets en cours.
Exemple : !supprimer_tous

!warnings <@membre>
Affiche le nombre d'avertissements d'un utilisateur. (Admin uniquement)
Exemple : !warnings @Utilisateur

!reset_warnings <@membre>
Réinitialise les avertissements d'un utilisateur. (Admin uniquement)
Exemple : !reset_warnings @Utilisateur

!version
Affiche la version actuelle du bot.
Exemple : !version

Fonctionnalités supplémentaires
Modération automatique :

Bloque les messages contenant des mots interdits définis dans le fichier banned_words.json.
Avertit les utilisateurs en cas de récidive.
Expulse automatiquement les utilisateurs après 3 avertissements.
Surveillance des serveurs :

Vérifie le statut des serveurs configurés (BattleMetrics et Eco-Servers) et met à jour un message dans un canal Discord.
Installation
Prérequis
Python 3.10 ou supérieur
Les bibliothèques Python suivantes :
discord.py
python-dotenv
aiohttp
beautifulsoup4
Étapes d'installation
Clonez ou téléchargez ce projet dans un dossier local.

Installez les dépendances nécessaires :
pip install -r requirements.txt
Créez un fichier .env dans le dossier principal et ajoutez votre token Discord :
DISCORD_TOKEN=VotreTokenDiscordIci
Assurez-vous que les fichiers suivants sont présents :

bot.py : Le fichier principal du bot.
banned_words.json : Contient la liste des mots interdits.
warnings.json : Stocke les avertissements des utilisateurs (généré automatiquement si absent).
tickets.json : Stocke les tickets anonymes (généré automatiquement si absent).
Lancez le bot :
python bot.py

Configuration

Liste des mots interdits
La liste des mots interdits est stockée dans le fichier banned_words.json.
Exemple de contenu :
[
    "insulte1",
    "insulte2",
    "insulte3"
]
Ajoutez ou modifiez les mots selon vos besoins.
Gestion des avertissements
Les avertissements sont stockés dans le fichier warnings.json.
Les utilisateurs reçoivent un avertissement lorsqu'ils envoient un message contenant un mot interdit.
Après 3 avertissements, l'utilisateur est automatiquement expulsé du serveur.

Structure du projet
DiscordCompanion/
├── bot.py               # Fichier principal du bot
├── banned_words.json    # Liste des mots interdits
├── warnings.json        # Fichier généré pour stocker les avertissements
├── tickets.json         # Fichier généré pour stocker les tickets anonymes
├── .env                 # Contient le token Discord
├── requirements.txt     # Liste des dépendances Python

Contribution
Si vous souhaitez contribuer à ce projet, vous pouvez :

Forker ce dépôt.
Créer une branche pour vos modifications :
git checkout -b ma-branche

Soumettre une pull request.

Licence
Ce projet est sous licence MIT. Vous êtes libre de l'utiliser, de le modifier et de le distribuer.

Si vous avez des questions ou des suggestions, n'hésitez pas à me contacter ! 😊
