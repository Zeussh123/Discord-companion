"""
Gestionnaire de tickets pour les feedbacks anonymes.
"""
import os
import json
import uuid
import logging
from datetime import datetime

import discord

# Configurer le logging
logger = logging.getLogger('ticket_manager')
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

class TicketManager:
    """
    Gère les tickets de feedback anonymes envoyés par les membres.
    Les tickets sont stockés avec un identifiant unique, et peuvent être lus
    et répondus uniquement par les administrateurs.
    """
    def __init__(self, bot):
        """
        Initialise le gestionnaire de tickets.
        
        Args:
            bot: L'instance du bot Discord
        """
        self.bot = bot
        self.tickets = {}  # {ticket_id: ticket_data}
        self.tickets_file = "tickets.json"
        self.load_tickets()
        
        # Canal par défaut pour les tickets (peut être modifié avec set_ticket_channel)
        self.ticket_channel_id = None
        
        logger.info("Gestionnaire de tickets initialisé")
    
    def load_tickets(self):
        """Charge les tickets depuis le fichier JSON."""
        try:
            if os.path.exists(self.tickets_file):
                with open(self.tickets_file, 'r', encoding='utf-8') as f:
                    self.tickets = json.load(f)
                logger.info(f"Tickets chargés depuis {self.tickets_file}: {len(self.tickets)} tickets")
            else:
                logger.info(f"Aucun fichier de tickets trouvé ({self.tickets_file})")
        except Exception as e:
            logger.error(f"Erreur lors du chargement des tickets: {e}")
            self.tickets = {}
    
    def save_tickets(self):
        """Sauvegarde les tickets dans le fichier JSON."""
        try:
            with open(self.tickets_file, 'w', encoding='utf-8') as f:
                json.dump(self.tickets, f, ensure_ascii=False, indent=2)
            logger.info(f"Tickets sauvegardés dans {self.tickets_file}")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des tickets: {e}")
    
    def set_ticket_channel(self, channel_id):
        """
        Définit le canal où les tickets seront envoyés.
        
        Args:
            channel_id: L'ID du canal Discord
            
        Returns:
            bool: True si le canal a été défini avec succès
        """
        # Vérifier que le canal existe
        channel = self.bot.get_channel(channel_id)
        if not channel:
            logger.warning(f"Canal de tickets {channel_id} introuvable")
            return False
            
        self.ticket_channel_id = channel_id
        logger.info(f"Canal de tickets défini: {channel.name} (ID: {channel_id})")
        return True
    
    def create_ticket(self, author_id, content, guild_id=None):
        """
        Crée un nouveau ticket avec un message de feedback.
        
        Args:
            author_id: L'ID Discord de l'auteur
            content: Le contenu du feedback
            guild_id: L'ID du serveur Discord (optionnel)
            
        Returns:
            str: L'ID du ticket créé
        """
        # Générer un ID unique pour le ticket (6 premiers caractères de l'UUID)
        ticket_id = str(uuid.uuid4())[:6].upper()
        
        # Créer le ticket
        ticket = {
            'id': ticket_id,
            'author_id': author_id,
            'content': content,
            'created_at': datetime.now().isoformat(),
            'status': 'open',
            'guild_id': guild_id,
            'responses': []
        }
        
        # Stocker le ticket
        self.tickets[ticket_id] = ticket
        self.save_tickets()
        
        logger.info(f"Ticket {ticket_id} créé par l'utilisateur {author_id}")
        return ticket_id
    
    async def send_ticket_to_channel(self, ticket_id):
        """
        Envoie le ticket dans le canal des administrateurs.
        
        Args:
            ticket_id: L'ID du ticket à envoyer
            
        Returns:
            bool: True si le ticket a été envoyé avec succès
        """
        if not self.ticket_channel_id:
            logger.warning("Aucun canal de tickets défini")
            return False
            
        ticket = self.tickets.get(ticket_id)
        if not ticket:
            logger.warning(f"Ticket {ticket_id} introuvable")
            return False
            
        channel = self.bot.get_channel(self.ticket_channel_id)
        if not channel:
            logger.warning(f"Canal de tickets {self.ticket_channel_id} introuvable")
            return False
            
        # Créer un embed pour le ticket
        embed = discord.Embed(
            title=f"Nouveau Feedback (ID: {ticket_id})",
            description=ticket['content'],
            color=discord.Color.blue(),
            timestamp=datetime.fromisoformat(ticket['created_at'])
        )
        embed.set_footer(text="Feedback anonyme | Pour répondre: !reply {} <message>".format(ticket_id))
        
        try:
            await channel.send(embed=embed)
            logger.info(f"Ticket {ticket_id} envoyé dans le canal {channel.name}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du ticket {ticket_id}: {e}")
            return False
    
    async def reply_to_ticket(self, ticket_id, response_content, responder_id):
        """
        Répond à un ticket et envoie la réponse à l'auteur original.
        
        Args:
            ticket_id: L'ID du ticket auquel répondre
            response_content: Le contenu de la réponse
            responder_id: L'ID Discord de la personne qui répond
            
        Returns:
            bool: True si la réponse a été envoyée avec succès
        """
        ticket = self.tickets.get(ticket_id)
        if not ticket:
            logger.warning(f"Ticket {ticket_id} introuvable")
            return False
            
        # Ajouter la réponse au ticket
        response = {
            'content': response_content,
            'responder_id': responder_id,
            'created_at': datetime.now().isoformat()
        }
        
        ticket['responses'].append(response)
        self.save_tickets()
        
        # Envoyer la réponse en message privé à l'auteur original
        try:
            author = await self.bot.fetch_user(int(ticket['author_id']))
            if author:
                embed = discord.Embed(
                    title=f"Réponse à votre feedback (ID: {ticket_id})",
                    description=response_content,
                    color=discord.Color.green()
                )
                
                # Ajouter le message original comme référence
                embed.add_field(
                    name="Votre message original",
                    value=ticket['content'][:1024],  # Limite Discord pour les champs
                    inline=False
                )
                
                await author.send(embed=embed)
                logger.info(f"Réponse au ticket {ticket_id} envoyée à l'utilisateur {author.name}")
                return True
            else:
                logger.warning(f"Utilisateur {ticket['author_id']} introuvable pour le ticket {ticket_id}")
                return False
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de la réponse au ticket {ticket_id}: {e}")
            return False
    
    def close_ticket(self, ticket_id):
        """
        Ferme un ticket.
        
        Args:
            ticket_id: L'ID du ticket à fermer
            
        Returns:
            bool: True si le ticket a été fermé avec succès
        """
        ticket = self.tickets.get(ticket_id)
        if not ticket:
            logger.warning(f"Ticket {ticket_id} introuvable")
            return False
            
        ticket['status'] = 'closed'
        self.save_tickets()
        
        logger.info(f"Ticket {ticket_id} fermé")
        return True
    
    def get_ticket(self, ticket_id):
        """
        Récupère un ticket spécifique.
        
        Args:
            ticket_id: L'ID du ticket à récupérer
            
        Returns:
            dict: Les données du ticket, ou None si introuvable
        """
        return self.tickets.get(ticket_id)
    
    def get_open_tickets(self):
        """
        Récupère tous les tickets ouverts.
        
        Returns:
            list: Liste des tickets ouverts
        """
        return {tid: ticket for tid, ticket in self.tickets.items() 
                if ticket['status'] == 'open'}
    
    def get_user_tickets(self, author_id):
        """
        Récupère tous les tickets d'un utilisateur spécifique.
        
        Args:
            author_id: L'ID Discord de l'auteur
            
        Returns:
            list: Liste des tickets de l'utilisateur
        """
        return {tid: ticket for tid, ticket in self.tickets.items() 
                if ticket['author_id'] == author_id}