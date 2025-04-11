"""
Génère un lien d'invitation pour le bot Discord.
Exécutez ce script pour obtenir un lien d'invitation URL que vous pourrez utiliser 
pour ajouter le bot à votre serveur Discord.
"""
import os
import discord
from discord.ext import commands

def generate_invite_link():
    # Récupération du CLIENT_ID depuis les variables d'environnement ou depuis le token
    token = os.getenv("DISCORD_TOKEN")
    client_id = os.getenv("CLIENT_ID")  # Idéalement, vous devriez avoir un CLIENT_ID séparé
    
    if not token:
        print("❌ Erreur: Token Discord introuvable dans les variables d'environnement.")
        print("Veuillez configurer la variable DISCORD_TOKEN.")
        return
    
    try:
        # Si nous n'avons pas de CLIENT_ID, on peut essayer de l'extraire du token
        # Note: ceci est une approche simplifiée, il est préférable d'avoir un CLIENT_ID séparé
        if not client_id and "." in token:
            try:
                # Le CLIENT_ID est généralement la première partie du token avant le premier point
                import base64
                first_part = token.split('.')[0]
                padding = '=' * (4 - len(first_part) % 4)
                client_id = base64.b64decode(first_part + padding).decode('utf-8')
                print(f"ID extrait du token: {client_id}")
            except Exception as e:
                print(f"❌ Impossible d'extraire le client ID du token: {e}")
        
        # Définir les permissions dont le bot a besoin
        permissions = discord.Permissions(
            send_messages=True,
            read_messages=True,
            read_message_history=True,
            embed_links=True,
            attach_files=True,
            use_external_emojis=True,
            add_reactions=True
        )
        
        # S'il y a un CLIENT_ID défini ou extrait, générer le lien d'invitation
        if client_id:
            # Méthode directe utilisant l'ID client
            invite_url = discord.utils.oauth_url(
                client_id, 
                permissions=permissions,
                scopes=("bot", "applications.commands")
            )
            
            print("\n✅ Voici le lien d'invitation pour votre bot:")
            print(invite_url)
            print("\nUtilisez ce lien pour ajouter le bot à votre serveur Discord.")
            print("Assurez-vous d'être connecté à Discord dans votre navigateur avant d'ouvrir ce lien.")
        else:
            print("❌ Impossible de générer un lien d'invitation sans CLIENT_ID.")
            print("Veuillez obtenir votre CLIENT_ID depuis le portail développeur Discord:")
            print("https://discord.com/developers/applications")
            
    except Exception as e:
        print(f"❌ Erreur lors de la génération du lien d'invitation: {e}")
        print("Veuillez vérifier votre connexion internet et les permissions du bot.")

if __name__ == "__main__":
    generate_invite_link()