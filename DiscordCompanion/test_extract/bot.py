"""
Discord bot implementation for scheduling messages.
"""
import logging
import asyncio
import discord
from discord.ext import commands
from datetime import datetime, timedelta  # Importer timedelta explicitement
import re
import pytz  # Pour gérer les fuseaux horaires

from scheduler import MessageScheduler
from ticket_manager import TicketManager

# Définir le fuseau horaire à utiliser (Europe/Paris pour la France)
TIMEZONE = pytz.timezone('Europe/Paris')

# Configure logging
logger = logging.getLogger(__name__)

# Create an instance of the bot with command prefix !
intents = discord.Intents.default()

# Message Content Intent est nécessaire pour lire les commandes avec préfixe
# Cet intent doit être explicitement activé dans le portail développeur Discord
intents.message_content = True
# logger.warning("IMPORTANT: L'intent 'message_content' est activé dans le code.")
# logger.warning("IMPORTANT: Vous devez également l'activer dans le portail développeur Discord:")
# logger.warning("IMPORTANT: 1. Allez sur https://discord.com/developers/applications")
# logger.warning("IMPORTANT: 2. Sélectionnez votre application bot")
# logger.warning("IMPORTANT: 3. Dans 'Bot', activez 'Message Content Intent'")
# logger.warning("IMPORTANT: 4. Sauvegardez les changements")
# logger.warning("IMPORTANT: Si cette étape n'est pas effectuée, le bot ne pourra pas lire les commandes.")

# Configuration pour Discord.py v2.5.2
bot = commands.Bot(
    command_prefix='!', 
    intents=intents,
    description="Bot de programmation de messages automatisés",
    help_command=commands.DefaultHelpCommand(),  # Utilisation de la commande d'aide par défaut
)

# Initialize the message scheduler
scheduler = MessageScheduler(bot)

# Initialize the ticket manager
ticket_manager = TicketManager(bot)

# Rendre les commandes insensibles à la casse
bot.case_insensitive = True

# Ajouter un checker de messages en attente avec debug supplémentaire
async def check_pending_messages():
    """
    Fonction qui vérifie périodiquement s'il y a des messages à envoyer
    """
    await bot.wait_until_ready()
    logger.info("Démarrage du vérificateur de messages en attente")
    while not bot.is_closed():
        try:
            now = datetime.now(TIMEZONE)
            jobs_to_execute = []
            
            # Afficher tous les jobs actuellement programmés
            logger.info(f"VERIFICATION - {len(scheduler.jobs)} messages programmés au total")
            for job_id, details in list(scheduler.jobs.items()):
                scheduled_time = details['time']
                channel_id = details['channel_id']
                msg_preview = details['message'][:30] + "..." if len(details['message']) > 30 else details['message']
                logger.info(f"DEBUG - Job {job_id}: prévu pour {scheduled_time}, canal {channel_id}, message: {msg_preview}")
                
                # Ajouter +01:00 à l'heure programmée si elle n'a pas de timezone
                if scheduled_time.tzinfo is None:
                    scheduled_time = TIMEZONE.localize(scheduled_time)
                    logger.info(f"DEBUG - Conversion timezone: {scheduled_time}")
                
                # Calculer si le message doit être envoyé maintenant
                send_now = False
                time_diff = (scheduled_time - now).total_seconds()
                logger.info(f"DEBUG - Différence de temps: {time_diff} secondes")
                
                # Considérer comme "à envoyer" si la différence est de moins de 10 secondes
                # ou si le message est en retard (différence négative)
                if time_diff <= 10:
                    send_now = True
                    logger.info(f"🔍 MESSAGE À ENVOYER DÉTECTÉ: Job {job_id} prévu pour {scheduled_time} (maintenant: {now})")
                    jobs_to_execute.append((job_id, details))
            
            # Exécuter les jobs trouvés
            for job_id, details in jobs_to_execute:
                channel_id = details['channel_id']
                message = details['message']
                author_id = details['author_id']
                
                logger.info(f"⚡ EXÉCUTION DIRECTE du job {job_id}")
                try:
                    # Essayer d'obtenir le canal directement
                    channel = bot.get_channel(channel_id)
                    if not channel:
                        logger.error(f"❌ Canal {channel_id} introuvable")
                        continue
                    
                    # Envoyer le message directement
                    logger.info(f"📨 Envoi du message dans le canal {channel.name} ({channel_id})")
                    sent_message = await channel.send(message)
                    logger.info(f"✅ Message envoyé avec succès: {sent_message.id}")
                    
                    # Ajouter les informations de programmation avec le nom d'utilisateur stocké
                    # Récupérer le nom d'auteur depuis les détails du job
                    if 'author_name' in details and details['author_name']:
                        username = details['author_name']
                        logger.info(f"Utilisation du nom d'auteur stocké: {username}")
                    else:
                        # Fallback au cas où le nom n'a pas été stocké
                        user = bot.get_user(author_id)
                        username = user.name if user else "Utilisateur inconnu"
                        logger.info(f"Fallback vers le nom d'auteur récupéré via API: {username}")
                    
                    # Envoyer un embed comme réponse avec le nom en gras pour plus de visibilité
                    await channel.send(
                        embed=discord.Embed(
                            description=f"📅 Ce message a été programmé par **{username}**",
                            color=discord.Color.green()
                        ),
                        reference=sent_message
                    )
                    logger.info(f"✅ Informations de programmation ajoutées")
                    
                    # Supprimer le job après exécution réussie
                    if job_id in scheduler.jobs:
                        del scheduler.jobs[job_id]
                        logger.info(f"✓ Job {job_id} supprimé de la liste des jobs")
                    
                    # Supprimer également du scheduler APScheduler
                    try:
                        scheduler.scheduler.remove_job(job_id)
                        logger.info(f"✓ Job {job_id} supprimé du scheduler APScheduler")
                    except Exception as e:
                        logger.warning(f"⚠️ Erreur lors de la suppression du job {job_id} du scheduler: {e}")
                except Exception as e:
                    logger.error(f"❌ Erreur lors de l'exécution directe du job {job_id}: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
            
            # Attendre 5 secondes avant la prochaine vérification
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"Erreur dans la boucle de vérification: {e}")
            import traceback
            logger.error(f"Stack trace: {traceback.format_exc()}")
            await asyncio.sleep(10)  # Attendre plus longtemps en cas d'erreur

# Dans Discord.py v2.5+, nous définissons setup_hook comme une fonction asynchrone
async def setup_hook():
    """Fonction appelée au démarrage du bot, avant on_ready"""
    logger.info("Bot setup_hook called")
    
    # Démarrer la tâche de vérification des messages en arrière-plan après un court délai
    # pour s'assurer que tout est initialisé
    await asyncio.sleep(2)
    bot.loop.create_task(check_pending_messages())
    
# Assignation de la méthode setup_hook
bot.setup_hook = setup_hook

@bot.event
async def on_ready():
    """Called when the bot is ready and connected to Discord."""
    logger.info(f'Bot connected as {bot.user.name} (ID: {bot.user.id})')
    logger.info(f'Connected to {len(bot.guilds)} servers')
    
    # Définir l'activité du bot
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, 
        name="for scheduled messages | !help"
    ))
    
    # Start the scheduler once the bot is ready
    scheduler.start()
    logger.info("Scheduler started after bot is ready")
    
    # Log pour indiquer que les commandes sont disponibles
    logger.info(f"Bot ready with {len(bot.commands)} commands loaded: {[cmd.name for cmd in bot.commands]}")

# Commande pour tester l'envoi immédiat d'un message
@bot.command(name='testmsg', help='Teste l\'envoi immédiat d\'un message. Usage: !testmsg <message>')
async def test_message(ctx, *, message: str):
    """
    Teste l'envoi immédiat d'un message.
    
    Args:
        ctx: Le contexte de la commande
        message: Le message à envoyer
    """
    try:
        logger.info(f"Test d'envoi immédiat demandé par {ctx.author.name}")
        await ctx.send(f"⏱️ Test d'envoi immédiat en cours...")
        
        # Ajouter le message dans le scheduler pour exécution immédiate (dans 5 secondes)
        now = datetime.now()
        target_time = now + timedelta(seconds=5)
        
        # Récupérer le nom d'utilisateur pour le stocker avec le message
        author_name = ctx.author.name
        author_display_name = getattr(ctx.author, 'display_name', None) or author_name
        logger.info(f"Test programmé par {author_display_name} (ID: {ctx.author.id})")
        
        job_id = scheduler.schedule_message(
            channel_id=ctx.channel.id,
            message=f"🧪 TEST MESSAGE: {message}",
            time=target_time,
            author_id=ctx.author.id,
            author_name=author_display_name
        )
        
        logger.info(f"Message de test programmé avec ID {job_id} pour {target_time}")
        await ctx.send(f"✅ Message de test programmé pour dans 5 secondes avec ID: `{job_id}`")
        
    except Exception as e:
        logger.error(f"Erreur lors du test d'envoi: {e}")
        await ctx.send(f"❌ Erreur lors du test: {str(e)}")

# Définition de la commande schedule avec préfixe et gestion améliorée des messages
@bot.command(name='schedule', help='Programme un message à envoyer ultérieurement. Format: !schedule <heure> [#canal] <message> ou !schedule <heure> <#canal> <message>')
async def schedule_message(ctx, time_str: str, *, rest: str = None):
    """
    Schedule a message to be sent at a specified time, with optional channel specification.
    
    Args:
        ctx: The command context
        time_str: The time to send the message in format "YYYY-MM-DD HH:MM" or "HH:MM"
        rest: The rest of the command (channel mention + message or just message)
    """
    try:
        # Vérifier que le reste de la commande est fourni
        if rest is None:
            await ctx.send("❌ Message manquant. Format: `!schedule <heure> [#canal] <message>`")
            return
        
        logger.info(f"Commande schedule reçue: heure={time_str}, reste={rest}")
        
        # Parse the time string
        # Utiliser le fuseau horaire Europe/Paris
        now = datetime.now(TIMEZONE)
        logger.info(f"Heure actuelle avec timezone: {now}")
        
        # Check if the time string includes a date
        if re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$', time_str):
            # Format: YYYY-MM-DD HH:MM
            try:
                # Créer un datetime naïf (sans timezone)
                naive_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M')
                logger.info(f"Date parsée (naïve): {naive_time}")
                
                # Garder le datetime naïf pour APScheduler
                target_time = naive_time
                logger.info(f"Date cible finale (naïve): {target_time}")
            except ValueError as e:
                logger.error(f"Erreur lors du parsing de la date: {e}")
                await ctx.send(f"❌ Format de date invalide: {e}")
                return
                
        elif re.match(r'^\d{2}:\d{2}$', time_str):
            # Format: HH:MM (today)
            try:
                hour, minute = map(int, time_str.split(':'))
                
                # Créer un datetime naïf basé sur aujourd'hui
                naive_now = datetime.now()  # Sans timezone
                naive_time = naive_now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                logger.info(f"Heure aujourd'hui (naïve): {naive_time}")
                
                # Si l'heure est dans le passé par rapport à l'heure actuelle, programmer pour demain
                if naive_time.hour < naive_now.hour or (naive_time.hour == naive_now.hour and naive_time.minute <= naive_now.minute):
                    naive_time = naive_time.replace(day=naive_now.day+1)
                    logger.info(f"Heure ajustée pour demain (naïve): {naive_time}")
                
                # Garder le datetime naïf pour APScheduler
                target_time = naive_time
                logger.info(f"Date cible finale (naïve): {target_time}")
            except ValueError as e:
                logger.error(f"Erreur lors du parsing de l'heure: {e}")
                await ctx.send(f"❌ Format d'heure invalide: {e}")
                return
        else:
            await ctx.send("❌ Format d'heure invalide. Utilisez 'YYYY-MM-DD HH:MM' ou 'HH:MM'.")
            return
        
        # Check if the target time is in the past
        # Convertir target_time en datetime avec timezone pour comparaison avec now
        target_time_tz = TIMEZONE.localize(target_time)
        if target_time_tz < now:
            await ctx.send("❌ Impossible de programmer des messages dans le passé.")
            logger.info(f"Message rejeté: date dans le passé. Cible: {target_time_tz}, Maintenant: {now}")
            return
        
        logger.info(f"Date cible valide (future): {target_time_tz} > {now}")
        
        # Traiter le reste de la commande (message et éventuellement canal)
        # On cherche d'abord s'il y a une mention de canal au format <#ID>
        logger.info(f"Contenu brut de la commande: '{rest.strip()}'")
        
        # Nouvelles options de commande supportées:
        # 1. !schedule HH:MM <#canal_id> message
        # 2. !schedule HH:MM message (utilise le canal actuel)
        
        # On commence par analyser si un canal est spécifié
        # Format attendu: <#NUMBERS> suivie du message (peut contenir des sauts de ligne)
        
        # Rechercher le motif <#NUMBERS> au début du message avec re.DOTALL pour capturer les sauts de ligne
        channel_match = re.match(r'^<#(\d+)>\s+(.+)', rest.strip(), re.DOTALL)
        if channel_match:
            # Si trouvé: prendre le canal spécifié et le message après
            channel_id_str = channel_match.group(1)
            channel_id = int(channel_id_str)
            # Préserver les sauts de ligne dans le message
            message = channel_match.group(2)
            
            # Log détaillé des sauts de ligne dans le message
            newline_count = message.count('\n')
            logger.info(f"Message avec canal contient {newline_count} sauts de ligne")
            
            logger.info(f"Canal trouvé dans la commande (format: <#id>): ID={channel_id}")
            logger.info(f"Message extrait: '{message}'")
            
            # Récupérer le canal
            channel = bot.get_channel(channel_id)
            if not channel:
                await ctx.send(f"❌ Canal introuvable: <#{channel_id}>")
                return
                
            # Vérifier les permissions
            permissions = channel.permissions_for(ctx.guild.me)
            if not permissions.send_messages:
                await ctx.send(f"❌ Je n'ai pas la permission d'envoyer des messages dans <#{channel_id}>")
                return
                
            logger.info(f"Canal spécifié trouvé: {channel.name} (ID: {channel_id})")
        else:
            # Si pas trouvé: utiliser le canal actuel
            channel = ctx.channel
            channel_id = ctx.channel.id
            # Préserver les sauts de ligne dans le message sans strip() excessif
            message = rest
            
            # Log détaillé des sauts de ligne dans le message
            newline_count = message.count('\n')
            logger.info(f"Message sans canal contient {newline_count} sauts de ligne")
            
            logger.info(f"Pas de canal spécifié dans la commande, utilisation du canal actuel: {channel.name} (ID: {channel_id})")
            # Attention: on utilise repr() pour voir les caractères spéciaux dans les logs
            logger.info(f"Message complet (repr): {repr(message)}")
        
        # Vérifier que le message n'est pas vide
        if not message:
            await ctx.send("❌ Message vide. Veuillez spécifier un message à envoyer.")
            return
            
        logger.info(f"Message à programmer: '{message}'")
        
        # Récupérer le nom d'utilisateur complet 
        author_name = ctx.author.name
        author_display_name = getattr(ctx.author, 'display_name', None) or author_name
        
        # Log des informations de l'auteur
        logger.info(f"Auteur de la commande: {author_name} (affichage: {author_display_name}, ID: {ctx.author.id})")
        
        # Schedule the message avec le nom de l'auteur
        job_id = scheduler.schedule_message(
            channel_id=channel_id,
            message=message,
            time=target_time,
            author_id=ctx.author.id,
            author_name=author_display_name  # Utiliser le nom d'affichage plutôt que le nom d'utilisateur
        )
        
        # Send confirmation
        if channel.id != ctx.channel.id:
            channel_mention = f"<#{channel.id}>"
            await ctx.send(f"✅ Message programmé pour le {target_time.strftime('%Y-%m-%d %H:%M')} dans {channel_mention}. ID de tâche: `{job_id}`")
        else:
            await ctx.send(f"✅ Message programmé pour le {target_time.strftime('%Y-%m-%d %H:%M')}. ID de tâche: `{job_id}`")
    
    except ValueError as e:
        await ctx.send(f"❌ Erreur: {str(e)}")
    except Exception as e:
        logger.error(f"Erreur lors de la programmation du message: {e}")
        await ctx.send("❌ Une erreur s'est produite lors de la programmation de votre message.")

# Définition de la commande list avec préfixe
@bot.command(name='list', help='Liste tous vos messages programmés')
async def list_scheduled(ctx):
    """Liste tous les messages programmés pour l'utilisateur qui fait la demande."""
    jobs = scheduler.get_jobs_for_user(ctx.author.id)
    
    if not jobs:
        await ctx.send("Vous n'avez aucun message programmé.")
        return
    
    embed = discord.Embed(
        title="Vos Messages Programmés",
        color=discord.Color.blue()
    )
    
    for job_id, job_info in jobs.items():
        channel = bot.get_channel(job_info['channel_id'])
        channel_name = channel.name if channel else "Canal inconnu"
        channel_mention = f"<#{job_info['channel_id']}>" if channel else "Canal inconnu"
        
        # Truncate message if too long
        message = job_info['message']
        if len(message) > 100:
            message = message[:97] + "..."
            
        embed.add_field(
            name=f"ID: {job_id} | {job_info['time'].strftime('%Y-%m-%d %H:%M')}",
            value=f"**Canal:** {channel_mention}\n**Message:** {message}",
            inline=False
        )
    
    await ctx.send(embed=embed)

# Définition de la commande cancel avec préfixe
@bot.command(name='cancel', help='Annule un message programmé. Usage: !cancel <job_id> ou !cancel all')
async def cancel_scheduled(ctx, job_id: str):
    """
    Annule un message programmé.
    
    Args:
        ctx: Le contexte de la commande
        job_id: L'ID de la tâche à annuler ou "all" pour annuler tous les messages
    """
    try:
        # Cas spécial: annuler tous les messages
        if job_id.lower() == 'all':
            count, cancelled_ids = scheduler.cancel_all_jobs(ctx.author.id)
            
            if count > 0:
                # Créer un message de confirmation
                if count == 1:
                    await ctx.send(f"✅ Votre message programmé a été annulé. ID: `{cancelled_ids[0]}`")
                else:
                    ids_text = ", ".join([f"`{job_id}`" for job_id in cancelled_ids[:5]])
                    if len(cancelled_ids) > 5:
                        ids_text += f" et {len(cancelled_ids) - 5} autres..."
                    
                    await ctx.send(f"✅ Vos {count} messages programmés ont été annulés.\nIDs annulés: {ids_text}")
            else:
                await ctx.send("ℹ️ Vous n'avez aucun message programmé à annuler.")
            return
            
        # Cas normal: annuler un message spécifique
        result = scheduler.cancel_job(job_id, ctx.author.id)
        
        if result:
            await ctx.send(f"✅ Message programmé avec l'ID `{job_id}` a été annulé.")
        else:
            await ctx.send(f"❌ Impossible de trouver un message programmé avec l'ID `{job_id}` qui vous appartient.")
    
    except Exception as e:
        logger.error(f"Erreur lors de l'annulation de la tâche: {e}")
        await ctx.send("❌ Une erreur s'est produite lors de l'annulation du message programmé.")

@bot.event
async def on_command_error(ctx, error):
    """Gérer les erreurs de commande."""
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Argument requis manquant: {error.param.name}")
    elif isinstance(error, commands.CommandNotFound):
        # Ignorer les erreurs de commande introuvable
        pass
    else:
        logger.error(f"Erreur de commande: {error}")
        await ctx.send(f"❌ Une erreur s'est produite: {str(error)}")

# Commandes pour le système de tickets de feedback anonyme
@bot.command(name='feedback', help='Envoie un feedback anonyme aux administrateurs. Usage: !feedback <message>')
async def send_feedback(ctx, *, message: str):
    """
    Envoie un feedback anonyme qui sera visible uniquement par les administrateurs.
    Le message original est supprimé immédiatement pour préserver l'anonymat.
    
    Args:
        ctx: Le contexte de la commande
        message: Le contenu du feedback
    """
    try:
        # Supprimer le message original pour l'anonymat
        await ctx.message.delete()
        logger.info(f"Message de feedback reçu (auteur original: {ctx.author.name}, ID: {ctx.author.id})")
        
        # Vérifier que le gestionnaire de tickets a un canal configuré
        if not ticket_manager.ticket_channel_id:
            # Si pas de canal configuré, envoyer un message en DM à l'utilisateur
            await ctx.author.send("⚠️ Aucun canal de tickets n'a été configuré. Votre feedback n'a pas pu être envoyé.")
            logger.warning(f"Tentative d'envoi de feedback sans canal configuré par {ctx.author.name}")
            return
            
        # Créer un ticket
        ticket_id = ticket_manager.create_ticket(
            author_id=ctx.author.id,
            content=message,
            guild_id=ctx.guild.id if ctx.guild else None
        )
        
        # Envoyer le ticket dans le canal approprié
        sent = await ticket_manager.send_ticket_to_channel(ticket_id)
        
        if sent:
            # Envoyer une confirmation en message privé à l'utilisateur
            await ctx.author.send(
                embed=discord.Embed(
                    title="✅ Feedback envoyé",
                    description=f"Votre feedback anonyme a été envoyé avec succès.\n\nID de référence: `{ticket_id}`\n\nConservez cet ID pour référence future.",
                    color=discord.Color.green()
                )
            )
            logger.info(f"Ticket {ticket_id} envoyé avec succès")
        else:
            await ctx.author.send("❌ Une erreur s'est produite lors de l'envoi de votre feedback. Veuillez réessayer plus tard.")
            logger.error(f"Échec de l'envoi du ticket {ticket_id}")
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi du feedback: {e}")
        try:
            await ctx.author.send(f"❌ Une erreur s'est produite: {str(e)}")
        except:
            pass

@bot.command(name='reply', help='Répond à un ticket de feedback. Usage: !reply <ticket_id> <message>')
@commands.has_permissions(administrator=True)
async def reply_to_ticket(ctx, ticket_id: str, *, message: str):
    """
    Répond à un ticket de feedback.
    Réservé aux administrateurs.
    
    Args:
        ctx: Le contexte de la commande
        ticket_id: L'ID du ticket auquel répondre
        message: Le message de réponse
    """
    try:
        # Vérifier que le ticket existe
        ticket = ticket_manager.get_ticket(ticket_id)
        if not ticket:
            await ctx.send(f"❌ Ticket `{ticket_id}` introuvable.")
            return
            
        # Envoyer la réponse
        sent = await ticket_manager.reply_to_ticket(ticket_id, message, ctx.author.id)
        
        if sent:
            await ctx.send(f"✅ Réponse envoyée au ticket `{ticket_id}`.")
            logger.info(f"Réponse au ticket {ticket_id} envoyée par {ctx.author.name}")
        else:
            await ctx.send(f"❌ Impossible d'envoyer la réponse au ticket `{ticket_id}`.")
            logger.error(f"Échec de l'envoi de la réponse au ticket {ticket_id}")
    except Exception as e:
        logger.error(f"Erreur lors de la réponse au ticket: {e}")
        await ctx.send(f"❌ Une erreur s'est produite: {str(e)}")

@bot.command(name='tickets', help='Liste les tickets de feedback ouverts. Usage: !tickets')
@commands.has_permissions(administrator=True)
async def list_tickets(ctx):
    """
    Liste tous les tickets de feedback ouverts.
    Réservé aux administrateurs.
    
    Args:
        ctx: Le contexte de la commande
    """
    try:
        # Récupérer tous les tickets ouverts
        open_tickets = ticket_manager.get_open_tickets()
        
        if not open_tickets:
            await ctx.send("📭 Aucun ticket ouvert.")
            return
            
        # Créer un embed pour la liste des tickets
        embed = discord.Embed(
            title="📋 Tickets de feedback ouverts",
            description=f"Il y a {len(open_tickets)} ticket(s) ouvert(s).",
            color=discord.Color.blue()
        )
        
        # Ajouter chaque ticket à l'embed
        for ticket_id, ticket in open_tickets.items():
            # Tronquer le contenu s'il est trop long
            content = ticket['content']
            if len(content) > 100:
                content = content[:97] + "..."
                
            # Obtenir la date de création
            created_at = datetime.fromisoformat(ticket['created_at'])
            
            embed.add_field(
                name=f"ID: {ticket_id}",
                value=f"📝 **Message:** {content}\n📅 **Date:** {created_at.strftime('%Y-%m-%d %H:%M')}\n⚙️ **Commande:** `!reply {ticket_id} <message>`",
                inline=False
            )
        
        await ctx.send(embed=embed)
        logger.info(f"Liste des tickets affichée pour {ctx.author.name}")
    except Exception as e:
        logger.error(f"Erreur lors de l'affichage des tickets: {e}")
        await ctx.send(f"❌ Une erreur s'est produite: {str(e)}")

@bot.command(name='close', help='Ferme un ticket de feedback. Usage: !close <ticket_id>')
@commands.has_permissions(administrator=True)
async def close_ticket(ctx, ticket_id: str):
    """
    Ferme un ticket de feedback.
    Réservé aux administrateurs.
    
    Args:
        ctx: Le contexte de la commande
        ticket_id: L'ID du ticket à fermer
    """
    try:
        # Fermer le ticket
        closed = ticket_manager.close_ticket(ticket_id)
        
        if closed:
            await ctx.send(f"✅ Ticket `{ticket_id}` fermé avec succès.")
            logger.info(f"Ticket {ticket_id} fermé par {ctx.author.name}")
        else:
            await ctx.send(f"❌ Ticket `{ticket_id}` introuvable.")
            logger.error(f"Ticket {ticket_id} introuvable pour fermeture")
    except Exception as e:
        logger.error(f"Erreur lors de la fermeture du ticket: {e}")
        await ctx.send(f"❌ Une erreur s'est produite: {str(e)}")

@bot.command(name='setticketschannel', help='Définit le canal où les tickets seront envoyés. Usage: !setticketschannel')
@commands.has_permissions(administrator=True)
async def set_tickets_channel(ctx):
    """
    Définit le canal actuel comme canal de destination pour les tickets.
    Réservé aux administrateurs.
    
    Args:
        ctx: Le contexte de la commande
    """
    try:
        # Définir le canal actuel comme canal de tickets
        channel_id = ctx.channel.id
        success = ticket_manager.set_ticket_channel(channel_id)
        
        if success:
            await ctx.send(f"✅ Canal <#{channel_id}> défini comme canal de tickets.")
            logger.info(f"Canal de tickets défini sur {ctx.channel.name} (ID: {channel_id}) par {ctx.author.name}")
        else:
            await ctx.send("❌ Impossible de définir ce canal comme canal de tickets.")
            logger.error(f"Échec de la définition du canal de tickets")
    except Exception as e:
        logger.error(f"Erreur lors de la définition du canal de tickets: {e}")
        await ctx.send(f"❌ Une erreur s'est produite: {str(e)}")

def run_bot(token):
    """
    Run the Discord bot.
    
    Args:
        token: The Discord bot token
    """
    logging.info("Tentative de connexion avec le token Discord...")
    # Pour éviter les problèmes potentiels avec le token,
    # utilisons le mécanisme de connexion directement
    try:
        bot.run(token, log_handler=None)
    except Exception as e:
        logging.error(f"Erreur lors de la connexion à Discord: {e}")
        # Imprimer plus de détails sur le token (sans révéler le token complet)
        if token:
            token_prefix = token[:4]
            token_suffix = token[-4:]
            token_length = len(token)
            logging.debug(f"Format du token: {token_prefix}...{token_suffix} (longueur: {token_length})")
