import os
import json
import logging
import discord
import random
import string
from discord.ext import commands, tasks
from dotenv import load_dotenv
import aiohttp
from bs4 import BeautifulSoup

# Charger les variables d'environnement
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

if not TOKEN:
    print("Erreur : Le token Discord n'a pas été trouvé dans le fichier .env")
    exit(1)

# Configuration des logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration des intents
intents = discord.Intents.default()
intents.message_content = True

# Créer une instance du bot avec le préfixe "!"
bot = commands.Bot(command_prefix='!', intents=intents, description="Bot Discord simplifié")

# Charger ou initialiser les tickets
TICKETS_FILE = "tickets.json"
WARNINGS_FILE = "warnings.json"

def load_warnings():
    try:
        with open(WARNINGS_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_warnings(warnings):
    with open(WARNINGS_FILE, "w") as file:
        json.dump(warnings, file, indent=4)

warnings = load_warnings()

# Charger les mots interdits depuis un fichier JSON
BANNED_WORDS_FILE = "banned_words.json"

def load_banned_words():
    try:
        with open(BANNED_WORDS_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []

BANNED_WORDS = load_banned_words()

# Fonction pour vérifier les mots interdits
def contains_banned_words(message):
    for word in BANNED_WORDS:
        if word.lower() in message.lower():
            return True
    return False

def load_tickets():
    try:
        with open(TICKETS_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_tickets(tickets):
    with open(TICKETS_FILE, "w") as file:
        json.dump(tickets, file, indent=4)

tickets = load_tickets()

# Fonction pour générer un ID aléatoire de 6 caractères
def generate_ticket_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))

# Événement : le bot est prêt
@bot.event
async def on_ready():
    logger.info(f"Bot connecté en tant que {bot.user.name} (ID: {bot.user.id})")
    await bot.change_presence(activity=discord.Game(name="!help"))
    check_server_status.start()  # Démarrer la tâche de vérification du serveur

# Commande : Soumettre un avis anonyme
@bot.command(name='avis', help="Soumettez un avis anonyme.")
async def avis(ctx, *, message: str):
    try:
        # Vérifier si le message contient des mots interdits
        if contains_banned_words(message):
            user_id = str(ctx.author.id)
            warnings[user_id] = warnings.get(user_id, 0) + 1
            save_warnings(warnings)

            # Avertir l'utilisateur
            if warnings[user_id] < 3:
                await ctx.author.send(
                    f"Votre message contient des mots interdits et n'a pas été envoyé. "
                    f"Attention, vous avez déjà {warnings[user_id]} avertissement(s). "
                    f"Au bout de 3, vous serez expulsé du serveur."
                )
            else:
                # Expulser l'utilisateur après 3 récidives
                guild = ctx.guild
                await guild.kick(ctx.author, reason="Utilisation répétée de mots interdits.")
                await ctx.author.send("Vous avez été expulsé du serveur pour utilisation répétée de mots interdits.")
                return

            return  # Ne pas continuer si le message contient des mots interdits

        # Supprimer le message de l'utilisateur dans le canal
        await ctx.message.delete()

        # Générer un ID unique pour le ticket
        ticket_id = generate_ticket_id()
        tickets[ticket_id] = {"message": message, "author_id": ctx.author.id, "response": None}
        save_tickets(tickets)

        # Envoyer un message privé à l'utilisateur
        await ctx.author.send("Merci de soumettre votre avis. Votre message a bien été pris en compte.")
    except discord.Forbidden:
        logger.warning(f"Impossible d'envoyer un MP à {ctx.author}.")
    except Exception as e:
        logger.error(f"Erreur lors de la commande !avis : {e}")

# Commande : Réinitialiser les avertissements (Admin uniquement)
@bot.command(name='reset_warnings', help="Réinitialise les avertissements d'un utilisateur. (Admin uniquement)")
@commands.has_permissions(administrator=True)
async def reset_warnings(ctx, member: discord.Member):
    try:
        user_id = str(member.id)
        if user_id in warnings:
            del warnings[user_id]
            save_warnings(warnings)
            await ctx.send(f"Les avertissements de {member.mention} ont été réinitialisés.")
        else:
            await ctx.send(f"{member.mention} n'a aucun avertissement.")
    except Exception as e:
        logger.error(f"Erreur lors de la commande !reset_warnings : {e}")

# Commande : Afficher les avertissements (Admin uniquement)
@bot.command(name='warnings', help="Affiche les avertissements d'un utilisateur. (Admin uniquement)")
@commands.has_permissions(administrator=True)
async def show_warnings(ctx, member: discord.Member):
    try:
        user_id = str(member.id)
        count = warnings.get(user_id, 0)
        await ctx.send(f"{member.mention} a {count} avertissement(s).")
    except Exception as e:
        logger.error(f"Erreur lors de la commande !warnings : {e}")

# Commande : Afficher tous les avis (Admin/Modo uniquement)
@bot.command(name='tickets', help="Afficher tous les avis anonymes. (Admin/Modo uniquement)")
@commands.has_permissions(manage_messages=True)
async def tickets_list(ctx):
    if not tickets:
        await ctx.send("Aucun avis n'a été soumis.")
        return

    embed = discord.Embed(title="Liste des avis anonymes", color=discord.Color.blue())
    for ticket_id, ticket in tickets.items():
        message = ticket.get("message", "Message non disponible")
        status = "Répondu" if ticket.get("response") else "En attente"
        embed.add_field(
            name=f"ID : {ticket_id} | Statut : {status}",
            value=f"Message : {message}",
            inline=False
        )
    await ctx.send(embed=embed)

# Commande : Historique des avis (Admin/Modo uniquement)
@bot.command(name='historique', help="Afficher l'historique des avis anonymes. (Admin/Modo uniquement)")
@commands.has_permissions(manage_messages=True)
async def historique(ctx):
    if not tickets:
        await ctx.send("Aucun avis n'a été soumis.")
        return

    embed = discord.Embed(title="Historique des avis anonymes", color=discord.Color.green())
    for ticket_id, ticket in tickets.items():
        message = ticket.get("message", "Message non disponible")
        response = ticket.get("response", "Pas de réponse")
        embed.add_field(
            name=f"ID : {ticket_id}",
            value=f"Message : {message}\nRéponse : {response}",
            inline=False
        )
    await ctx.send(embed=embed)

# Commande : Supprimer un ticket spécifique (Admin/Modo uniquement)
@bot.command(name='supprimer', help="Supprime un ticket spécifique en utilisant son ID. (Admin/Modo uniquement)")
@commands.has_permissions(manage_messages=True)
async def supprimer(ctx, ticket_id: str):
    if ticket_id not in tickets:
        await ctx.send(f"Le ticket avec l'ID {ticket_id} n'existe pas.")
        return

    del tickets[ticket_id]
    save_tickets(tickets)
    await ctx.send(f"Le ticket avec l'ID {ticket_id} a été supprimé.")

# Commande : Supprimer tous les tickets (Admin/Modo uniquement)
@bot.command(name='supprimer_tous', help="Supprime tous les tickets en cours. (Admin/Modo uniquement)")
@commands.has_permissions(manage_messages=True)
async def supprimer_tous(ctx):
    global tickets
    if not tickets:
        await ctx.send("Aucun ticket à supprimer.")
        return

    tickets.clear()
    save_tickets(tickets)
    await ctx.send("Tous les tickets ont été supprimés.")

# ID des serveurs
SERVER_ID_BATTLEMETRICS = "32646652"
BATTLEMETRICS_URL = f"https://api.battlemetrics.com/servers/{SERVER_ID_BATTLEMETRICS}"
ECO_SERVER_URL = "https://eco-servers.org/server/4923/"
CHANNEL_ID = 1359762431324196894  # Remplacez par l'ID de votre canal Discord

# Variable pour stocker le message Discord à mettre à jour
status_message = None

@tasks.loop(minutes=1)
async def check_server_status():
    global status_message

    async with aiohttp.ClientSession() as session:
        try:
            # Vérification du serveur BattleMetrics
            async with session.get(BATTLEMETRICS_URL) as response_battlemetrics:
                if response_battlemetrics.status == 200:
                    data_battlemetrics = await response_battlemetrics.json()
                    server_name_battlemetrics = data_battlemetrics["data"]["attributes"]["name"]
                    server_status_battlemetrics = data_battlemetrics["data"]["attributes"]["status"]
                    player_count_battlemetrics = data_battlemetrics["data"]["attributes"]["players"]
                    max_players_battlemetrics = data_battlemetrics["data"]["attributes"]["maxPlayers"]

                    embed = discord.Embed(
                        title=f"Statut des serveurs",
                        color=discord.Color.green() if server_status_battlemetrics == "online" else discord.Color.red()
                    )
                    embed.add_field(
                        name=f"BattleMetrics - {server_name_battlemetrics}",
                        value=f"Statut : {'🟢 En ligne' if server_status_battlemetrics == 'online' else '🔴 Hors ligne'}\n"
                              f"Joueurs : {player_count_battlemetrics}/{max_players_battlemetrics}\n"
                              f"[Voir sur BattleMetrics]({BATTLEMETRICS_URL})",
                        inline=False
                    )

            # Vérification du serveur Eco
            async with session.get(ECO_SERVER_URL) as response_eco:
                if response_eco.status == 200:
                    html = await response_eco.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    # Extraction des informations du serveur Eco
                    server_name_eco = soup.find('h1').text.strip() if soup.find('h1') else "Serveur Eco"

                    # Recherche de la ligne contenant "Players" et extraction du nombre de joueurs
                    players_row = soup.find('td', text=lambda x: x and 'Players' in x)
                    if players_row:
                        player_count_eco = players_row.find_next_sibling('td').text.strip()  # Trouver la cellule suivante
                    else:
                        player_count_eco = "0"  # Valeur par défaut si l'élément n'est pas trouvé

                    max_players_eco = "N/A"  # Si le max n'est pas disponible, utilisez "N/A"
                    server_status_eco = "En ligne" if int(player_count_eco) > 0 else "Hors ligne"

                    embed.add_field(
                        name=f"Eco - {server_name_eco}",
                        value=f"Statut : {'🟢 En ligne' if server_status_eco == 'En ligne' else '🔴 Hors ligne'}\n"
                              f"Joueurs : {player_count_eco}/{max_players_eco}\n"
                              f"[Voir sur Eco-Servers]({ECO_SERVER_URL})",
                        inline=False
                    )

            # Envoyer ou mettre à jour le message dans le canal
            channel = bot.get_channel(CHANNEL_ID)
            if not status_message:
                status_message = await channel.send(embed=embed)
            else:
                await status_message.edit(embed=embed)

        except Exception as e:
            logger.error(f"Erreur lors de la connexion aux serveurs : {e}")

# Commande personnalisée pour !help
class CustomHelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__()

    async def send_bot_help(self, mapping):
        
        embed = discord.Embed(
            title="Commandes disponibles",
            description="Voici la liste des commandes disponibles et leur utilisation :",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="!avis <message>",
            value="Soumettez un avis anonyme.\n**Exemple :** `!avis J'aime ce serveur !`",
            inline=False
        )
        embed.add_field(
            name="!reset_warnings <@membre>",
            value="Réinitialise les avertissements d'un utilisateur. (Admin uniquement)",
            inline=False
        )
        embed.add_field(
            name="!warnings <@membre>",
            value="Affiche les avertissements d'un utilisateur. (Admin uniquement)",
            inline=False
        )
        embed.add_field(
            name="!avis <message>",
            value="Soumettez un avis anonyme.\n**Exemple :** `!avis J'aime ce serveur !`",
            inline=False
        )
        embed.add_field(
            name="!repondre <ID> <message>",
            value="Répondez à un avis anonyme en utilisant son ID.\n**Exemple :** `!repondre a1B2c3 Merci pour votre retour !`",
            inline=False
        )
        embed.add_field(
            name="!tickets",
            value="Affiche tous les avis anonymes en cours.\n**Exemple :** `!tickets`",
            inline=False
        )
        embed.add_field(
            name="!historique",
            value="Affiche l'historique des avis anonymes avec leurs réponses.\n**Exemple :** `!historique`",
            inline=False
        )
        embed.add_field(
            name="!supprimer <ID>",
            value="Supprime un ticket spécifique en utilisant son ID.\n**Exemple :** `!supprimer a1B2c3`",
            inline=False
        )
        embed.add_field(
            name="!supprimer_tous",
            value="Supprime tous les tickets en cours.\n**Exemple :** `!supprimer_tous`",
            inline=False
        )
        embed.add_field(
            name="Statut du serveur",
            value="Le bot met automatiquement à jour le statut du serveur toutes les minutes dans le canal configuré.",
            inline=False
        )

        embed.set_footer(text="Bot Discord By Zeussh")
        await self.get_destination().send(embed=embed)

bot.help_command = CustomHelpCommand()

# Lancer le bot
if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except Exception as e:
        logger.error(f"Erreur lors de la connexion au bot : {e}")