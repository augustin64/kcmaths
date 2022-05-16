# Kcmaths

Collection de scripts pour interagir avec [kcmaths](https://www.kcmaths.com)

## kcmaths.py

Module python pour interagir avec kcmaths  
Utilisable sous forme de module ou via la ligne de commande.  

Dépendances:
```bash
pip install -r requirements.txt
```

```bash
Usage: kcmaths.py (download | get-race | set-race) [options]

Options:
  -h, --help            show this help message and exit
  -u USERNAME, --username=USERNAME
                        Nom d'utilisateur
  -p PASSWORD, --password=PASSWORD
                        Mot de passe
  -P PATH, --path=PATH  chemin où stocker les fichiers téléchargés
  -s SCORE, --score=SCORE
                        Nombres de points à la race
  -c, --clear-cache     Supprimer le cache déjà téléchargé
  -f FORMAT, --format=FORMAT
                        Format du classement à la race (json|text)
```

## quiz.py

Module python pour s'entraîner aux questions de cours et Vrai/Faux  

Dépendances:
```bash
pip install -r quiz-requirements.txt
```

```bash
Usage: quiz.py (vof | qdc)
```

Les questions de cours sont sélectionnées par défaut. De plus, ce script n'est configuré que pour le lecteur de PDFs `zathura`, il est nécessaire de réécrire en partie le script pour faire usage d'un autre lecteur, bien qu'il ait été conçu de manière à être configurable là dessus.  


## bot.py

Bot discord pour interagir avec kcmaths.  
Il enverra automatiquement une notification x aux utilisateurs connectés à chaque nouveau ds corrigé.


Dépendances:
```bash
pip install -r bot-requirements.txt
```

Commandes disponibles:
```bash
%help
%ds <numéro du ds> (detailed)
%lb <nom (optionnel)>           pour afficher le classement à la race (ou %leaderboard)
%p <points>                     pour mettre ses points à la race (ou %points)
%login <username> <password>    pour se connecter
```

Il est nécessaire de créer un fichier `auth.py` avant de lancer le bot contenant:
```
TOKEN="VOTRE.TOKEN.DISCORD"
```
Avec `VOTRE.TOKEN.DISCORD` étant un TOKEN de bot discord pouvant s'obtenir sur le [portail développeur de Discord](https://discord.com/developers/applications/).  