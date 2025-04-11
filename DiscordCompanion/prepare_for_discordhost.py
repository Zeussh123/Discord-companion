"""
Script utilitaire pour préparer les fichiers à uploader vers DiscordHost.
"""
import os
import shutil
import sys

# Liste des fichiers requis pour DiscordHost
REQUIRED_FILES = [
    'bot.py',
    'scheduler.py',
    'ticket_manager.py',
    'discord_host_main.py',
    'discordhost_requirements.txt',
    '.env.example',
    'README_DISCORDHOST.md',
]

# Liste des fichiers optionnels
OPTIONAL_FILES = [
    'tickets.json',
]

def check_files():
    """Vérifie si tous les fichiers requis sont présents."""
    missing_files = []
    for file in REQUIRED_FILES:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Fichiers requis manquants: {', '.join(missing_files)}")
        return False
    
    print("✅ Tous les fichiers requis sont présents.")
    
    # Vérifier les fichiers optionnels
    missing_optional = []
    for file in OPTIONAL_FILES:
        if not os.path.exists(file):
            missing_optional.append(file)
    
    if missing_optional:
        print(f"⚠️ Fichiers optionnels manquants: {', '.join(missing_optional)}")
    
    return True

def prepare_package():
    """Prépare un package avec tous les fichiers nécessaires pour DiscordHost."""
    try:
        # Créer un dossier pour le package
        package_dir = "discordhost_package"
        if os.path.exists(package_dir):
            shutil.rmtree(package_dir)
        os.makedirs(package_dir)
        
        # Copier les fichiers requis
        for file in REQUIRED_FILES:
            shutil.copy2(file, package_dir)
        
        # Renommer les fichiers comme nécessaire
        os.rename(
            os.path.join(package_dir, "discord_host_main.py"),
            os.path.join(package_dir, "main.py")
        )
        os.rename(
            os.path.join(package_dir, "discordhost_requirements.txt"),
            os.path.join(package_dir, "requirements.txt")
        )
        
        # Copier les fichiers optionnels s'ils existent
        for file in OPTIONAL_FILES:
            if os.path.exists(file):
                shutil.copy2(file, package_dir)
        
        print(f"✅ Package créé dans le dossier '{package_dir}'")
        print("✅ Fichiers prêts pour l'upload vers DiscordHost")
        
        print("\nInstructions:")
        print("1. Uploadez tous les fichiers du dossier 'discordhost_package' vers DiscordHost")
        print("2. Définissez la variable d'environnement DISCORD_TOKEN dans les paramètres de DiscordHost")
        print("3. Redémarrez votre bot sur DiscordHost")
        
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la préparation du package: {e}")
        return False

def main():
    """Point d'entrée principal."""
    print("=== Préparation des fichiers pour DiscordHost ===")
    
    if check_files():
        print("\nTous les fichiers nécessaires sont présents.")
        print("Création automatique du package...")
        prepare_package()
    else:
        print("\nIl manque des fichiers requis. Veuillez les créer avant de continuer.")

if __name__ == "__main__":
    main()