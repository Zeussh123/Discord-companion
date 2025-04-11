"""
Scheduler for handling message scheduling.
"""
import logging
import uuid
import discord
from datetime import datetime, timedelta
import pytz
import asyncio
# Utilisons le BackgroundScheduler au lieu de AsyncIOScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.jobstores.memory import MemoryJobStore

# Définir le fuseau horaire à utiliser (Europe/Paris pour la France)
TIMEZONE = pytz.timezone('Europe/Paris')

# Configure logging
logger = logging.getLogger(__name__)

class MessageScheduler:
    """
    Handles scheduling and sending of messages.
    """
    
    def __init__(self, bot):
        """
        Initialize the scheduler.
        
        Args:
            bot: The Discord bot instance
        """
        self.bot = bot
        # Configurer le scheduler avec le fuseau horaire Europe/Paris
        # Utiliser BackgroundScheduler au lieu de AsyncIOScheduler
        jobstores = {
            'default': MemoryJobStore()
        }
        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            timezone=TIMEZONE
        )
        self.jobs = {}  # Dictionary to store job details
        logger.info("Message scheduler initialized with timezone: Europe/Paris using BackgroundScheduler")
    
    def start(self):
        """
        Start the scheduler. This should be called after the bot is ready.
        """
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")
    
    def schedule_message(self, channel_id, message, time, author_id, author_name=None):
        """
        Schedule a message to be sent at a specific time.
        
        Args:
            channel_id: The Discord channel ID to send the message to
            message: The message content
            time: The datetime to send the message
            author_id: The Discord user ID of the person scheduling the message
            author_name: The Discord username of the person scheduling the message
            
        Returns:
            str: The job ID
        """
        # Generate a unique job ID
        job_id = str(uuid.uuid4())[:8]
        
        # Store job details with author name
        self.jobs[job_id] = {
            'channel_id': channel_id,
            'message': message,
            'time': time,
            'author_id': author_id,
            'author_name': author_name  # Stocker le nom d'utilisateur pour l'afficher plus tard
        }
        
        # Log des informations utilisateur
        if author_name:
            logger.info(f"Message programmé par {author_name} (ID: {author_id})")
        else:
            logger.info(f"Message programmé par auteur ID: {author_id} (nom non fourni)")
        
        # Conversion en datetime naïf si nécessaire
        # APScheduler avec timezone=TIMEZONE convertira automatiquement
        # les datetimes naïfs vers le bon fuseau horaire
        if time.tzinfo is not None:
            # On garde la date/heure mais on supprime l'info de timezone
            naive_time = time.replace(tzinfo=None)
            logger.info(f"Convertir datetime avec timezone en datetime naïf pour scheduler: {time} -> {naive_time}")
            run_date = naive_time
        else:
            run_date = time
            
        # Schedule the job
        # Pour les fonctions asynchrones, nous devons utiliser un wrapper qui appellera la fonction async
        # dans la boucle d'événements asyncio
        import asyncio
        from datetime import timedelta
        
        # Ajouter 10 secondes au temps d'exécution pour éviter les problèmes de timing précis
        # APScheduler peut parfois manquer un job s'il tombe exactement à la seconde près
        # Ce buffer garantit que le job sera exécuté même si le timing n'est pas exact
        execution_time = run_date - timedelta(seconds=10)
        logger.info(f"Ajustement du temps d'exécution avec buffer: {run_date} → {execution_time} (-10s)")
        
        # Créer une fonction de proxy qui appellera la fonction async et inclut une vérification de temps
        def async_proxy(func, job_id, channel_id, message, author_id, target_time):
            """Wrapper pour exécuter une fonction async depuis un contexte non-async avec vérification d'heure"""
            logger.info(f"⏱️ EXÉCUTION DU PROXY ASYNCHRONE - Job ID: {job_id}")
            logger.info(f"Heure actuelle: {datetime.now()} | Heure cible: {target_time}")
            
            try:
                # Obtenir la boucle d'événements actuelle ou créer une nouvelle boucle si aucune n'existe
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    # Si "There is no current event loop in thread", on en crée un nouveau
                    logger.info("Aucune boucle d'événements trouvée, création d'une nouvelle boucle")
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                # Une erreur peut se produire ici car l'exécuteur APScheduler utilise des threads
                # où la boucle asyncio n'est pas configurée
                logger.info(f"Boucle asyncio obtenue ou créée, exécution de la tâche pour job {job_id}")
                
                # Nous devons stopper l'exécution ici et déléguer à la boucle principale du bot
                # Le vérificateur périodique dans check_pending_messages s'occupera d'exécuter le message
                # C'est une solution plus sûre que d'essayer d'exécuter le message depuis un thread secondaire
                logger.info(f"Job {job_id} sera exécuté par le vérificateur périodique")
                return True
                
            except Exception as e:
                logger.error(f"Erreur dans async_proxy pour job {job_id}: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                return False
        
        # Schedule le job avec le proxy et le temps buffer
        # Nous ne passons pas l'exécution directe au scheduler car
        # cela pose problème avec la boucle d'événements asyncio
        # Le vérificateur périodique s'en occupera
        self.scheduler.add_job(
            async_proxy,
            DateTrigger(run_date=execution_time),
            args=[self._send_scheduled_message, job_id, channel_id, message, author_id, run_date],
            id=job_id,
            misfire_grace_time=120  # Permettre jusqu'à 2 minutes de retard dans l'exécution
        )
        logger.info(f"Job {job_id} programmé avec proxy asynchrone pour {execution_time} (heure cible: {run_date})")
        
        logger.info(f"Scheduled message with ID {job_id} for {time}")
        return job_id
    
    async def _send_scheduled_message(self, job_id, channel_id, message, author_id):
        """
        Send a scheduled message and clean up the job.
        
        Args:
            job_id: The ID of the job
            channel_id: The Discord channel ID to send the message to
            message: The message content
            author_id: The Discord user ID of the person who scheduled the message
        """
        logger.info(f"✅ EXÉCUTION DU MESSAGE PROGRAMMÉ - Début - Job ID: {job_id}")
        try:
            # Get the channel
            logger.info(f"Récupération du canal Discord {channel_id}")
            channel = self.bot.get_channel(channel_id)
            if not channel:
                logger.error(f"❌ Canal {channel_id} introuvable pour job {job_id}")
                return
            
            logger.info(f"Canal trouvé: {channel.name} (ID: {channel.id})")
            
            # Process the message to ensure proper handling of newlines
            # Make sure all types of newlines are properly converted to Discord's format
            # The \n in text strings from Discord should be sent as literal \n
            if message:
                processed_message = message.replace('\r\n', '\n').replace('\r', '\n')
                logger.info(f"Message traité pour les sauts de ligne. Longueur: {len(processed_message)}")
                # Compter les sauts de ligne en échappant correctement dans la f-string
                newline_count = processed_message.count('\n')
                logger.info(f"Message contient {newline_count} sauts de ligne")
            else:
                processed_message = ""
                logger.info("Message vide reçu")
            
            # Send the message
            logger.info(f"Envoi du message: {processed_message[:50]}...")
            sent_message = await channel.send(processed_message)
            logger.info(f"Message envoyé avec succès, ID: {sent_message.id}")
            
            # Add scheduled info as a reply
            # Récupérer les informations de l'auteur à partir de la liste des jobs
            job_info = self.jobs.get(job_id, {})
            
            # Récupération du nom d'utilisateur depuis les informations enregistrées
            if 'author_name' in job_info and job_info['author_name']:
                username = job_info['author_name']
                logger.info(f"Nom d'auteur trouvé dans les informations de job: {username}")
            else:
                # Fallback: essayer de récupérer le nom directement via l'API Discord
                user = self.bot.get_user(author_id)
                username = user.name if user else "Utilisateur inconnu"
                logger.info(f"Nom d'auteur récupéré via l'API Discord: {username}")
            
            logger.info(f"Ajout des informations de programmation (par {username})")
            
            try:
                # Créer un embed plus détaillé avec le nom de l'auteur
                embed = await channel.send(
                    embed=discord.Embed(
                        description=f"📅 Ce message a été programmé par **{username}**",
                        color=discord.Color.green()
                    ),
                    reference=sent_message
                )
                logger.info("Informations de programmation ajoutées avec succès")
            except Exception as embed_error:
                logger.error(f"Erreur lors de l'ajout de l'embed: {embed_error}")
                # Continuer même en cas d'erreur avec l'embed
            
            logger.info(f"✅ Message programmé envoyé avec succès pour job {job_id}")
        
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'envoi du message programmé pour job {job_id}: {e}")
            import traceback
            logger.error(f"Détails de l'erreur: {traceback.format_exc()}")
        
        finally:
            logger.info(f"Nettoyage du job {job_id}")
            # Remove the job from our records
            if job_id in self.jobs:
                del self.jobs[job_id]
                logger.info(f"Job {job_id} supprimé de nos enregistrements")
            else:
                logger.warning(f"Job {job_id} non trouvé dans nos enregistrements pour le nettoyage")
            logger.info(f"✅ EXÉCUTION DU MESSAGE PROGRAMMÉ - Fin - Job ID: {job_id}")
    
    def get_jobs_for_user(self, author_id):
        """
        Get all scheduled jobs for a specific user.
        
        Args:
            author_id: The Discord user ID
            
        Returns:
            dict: A dictionary of job IDs and details belonging to the user
        """
        return {job_id: details for job_id, details in self.jobs.items() 
                if details['author_id'] == author_id}
    
    def cancel_job(self, job_id, author_id):
        """
        Cancel a scheduled job.
        
        Args:
            job_id: The job ID to cancel
            author_id: The Discord user ID requesting the cancellation
            
        Returns:
            bool: Whether the job was successfully cancelled
        """
        # Check if job exists and belongs to the user
        if job_id in self.jobs and self.jobs[job_id]['author_id'] == author_id:
            # Remove from scheduler
            self.scheduler.remove_job(job_id)
            # Remove from our records
            del self.jobs[job_id]
            logger.info(f"Cancelled job {job_id}")
            return True
        
        return False
        
    def cancel_all_jobs(self, author_id):
        """
        Cancel all scheduled jobs for a specific user.
        
        Args:
            author_id: The Discord user ID requesting the cancellation
            
        Returns:
            tuple: (count, job_ids) - Number of jobs cancelled and list of their IDs
        """
        # Get all jobs for this user
        user_jobs = self.get_jobs_for_user(author_id)
        
        if not user_jobs:
            logger.info(f"No jobs found to cancel for user {author_id}")
            return 0, []
        
        cancelled_ids = []
        
        # Cancel each job
        for job_id in user_jobs.keys():
            # Remove from scheduler
            try:
                self.scheduler.remove_job(job_id)
                # Remove from our records
                del self.jobs[job_id]
                cancelled_ids.append(job_id)
                logger.info(f"Cancelled job {job_id} during cancel_all operation")
            except Exception as e:
                logger.error(f"Error cancelling job {job_id}: {e}")
        
        logger.info(f"Cancelled {len(cancelled_ids)} jobs for user {author_id}")
        return len(cancelled_ids), cancelled_ids
