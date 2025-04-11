"""
Vérifie si le token Discord est valide et affiche des informations utiles sur le bot.
"""
import os
import sys
import requests
import json

def check_discord_token():
    token = os.getenv("DISCORD_TOKEN")
    
    if not token:
        print("❌ Erreur: Aucun token Discord trouvé dans les variables d'environnement.")
        print("Veuillez configurer la variable DISCORD_TOKEN.")
        return False
    
    # Afficher une version tronquée du token pour vérification
    token_prefix = token[:4]
    token_suffix = token[-4:]
    token_length = len(token)
    print(f"Token trouvé: {token_prefix}...{token_suffix} (longueur: {token_length})")
    
    # Tester le token avec l'API Discord
    headers = {"Authorization": f"Bot {token}"}
    
    try:
        # Récupérer les informations du bot
        response = requests.get("https://discord.com/api/v10/users/@me", headers=headers)
        
        if response.status_code == 200:
            bot_info = response.json()
            print(f"\n✅ Token valide! Connecté en tant que: {bot_info['username']}#{bot_info.get('discriminator', 'XXXX')}")
            print(f"ID du bot: {bot_info['id']}")
            
            # Récupérer la liste des serveurs où le bot est présent
            guilds_response = requests.get("https://discord.com/api/v10/users/@me/guilds", headers=headers)
            
            if guilds_response.status_code == 200:
                guilds = guilds_response.json()
                print(f"\nLe bot est présent sur {len(guilds)} serveur(s):")
                
                for guild in guilds:
                    print(f"- {guild['name']} (ID: {guild['id']})")
                
                if not guilds:
                    print("\n⚠️ Le bot n'est présent sur aucun serveur!")
                    print("Utilisez le script generate_invite_link.py pour obtenir un lien d'invitation.")
                
                return True
            else:
                print(f"\n⚠️ Impossible de récupérer la liste des serveurs. Code: {guilds_response.status_code}")
                print(f"Réponse: {guilds_response.text}")
                return False
                
        else:
            print(f"\n❌ Token invalide ou expiré. Code: {response.status_code}")
            print(f"Réponse: {response.text}")
            
            if response.status_code == 401:
                print("\nLe token pourrait être invalide ou mal formaté.")
                print("Vérifiez que vous avez copié le token correct depuis le portail développeur Discord.")
            
            return False
            
    except Exception as e:
        print(f"\n❌ Erreur lors de la vérification du token: {e}")
        print("Vérifiez votre connexion internet et réessayez.")
        return False

if __name__ == "__main__":
    print("Vérification du token Discord...")
    success = check_discord_token()
    
    if not success:
        print("\nPour obtenir un nouveau token Discord:")
        print("1. Allez sur https://discord.com/developers/applications")
        print("2. Sélectionnez votre application ou créez-en une nouvelle")
        print("3. Dans l'onglet 'Bot', cliquez sur 'Reset Token'")
        print("4. Copiez le nouveau token et configurez-le dans les variables d'environnement")
        sys.exit(1)