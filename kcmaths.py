#!/usr/bin/python3
import os
from optparse import OptionParser
import json
import requests
from bs4 import BeautifulSoup


class Session():
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.auth = (username, password)
        self.session = requests.Session()

    def login(self):
        """Se connecte dans la session kcmaths"""
        r = self.session.post("http://kcmaths.com/index.php", {
            "nom_session":self.username,
            "mot_de_passe":self.password
        })
        return r

    def get_docs(self):
        "Renvoie l'adresse des URLs des documents disponibles"
        r = self.session.get("http://kcmaths.com/documents_sommaire.php")
        soup = BeautifulSoup(r.content, "html.parser")
        a = soup.find("div", {"class": "accueil"}).find_all("a")
        file_list = []
        for i in a :
            file_category = i.find_previous('h1').text
            if file_category is None:
                file_category = "None"
            file_name = i.find_next('td').text + '.' + i["href"].split('.')[-1]
            file_url = i["href"]
            if file_name is None:
                file_name = file_url.split("/")[-1]
            file_list.append( (file_category, file_name, file_url) )
        return file_list

    def get_prenom_nom(self):
        """Renvoie le nom prénom apparaissant sur la page d'accueil de kcmaths"""
        r = self.session.get("http://kcmaths.com/index.php")
        soup = BeautifulSoup(r.content, "html.parser")
        h1 = soup.find("h1")
        if h1 is not None:
            return h1.text
        return None

    def get_commentaire_ds(self, numero):
        """Renvoie le commentaire du ds numéro 'numero'"""
        r = self.session.post(
            "http://kcmaths.com/commun/devoir_consultation_eleve_1.php", 
            {"numero_ds": str(numero)},
            auth = self.auth
        )
        soup = BeautifulSoup(r.content, "html.parser")
        for i in soup.find_all("p"):
            if "Commentaire :" in i.text:
                return i.text
        return "Pas de commentaire"

    def get_dernier_ds_public(self):
        """Renvoie le numero du dernier ds public"""
        r = self.session.get("http://kcmaths.com/devoir_sommaire.php")
        soup = BeautifulSoup(r.content, "html.parser")
        select = soup.find("select", {"name": "numero_ds"})
        return max([ int(i.text) for i in select.find_all("option") ])


    def download_file(self, url, path):
        """Télécharge le fichier associé"""
        # NOTE the stream=True parameter below
        with self.session.get(url, stream=True, auth=self.auth) as r:
            r.raise_for_status()
            with open(path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    # If you have chunk encoded response uncomment if
                    # and set chunk_size parameter to None.
                    #if chunk:
                    f.write(chunk)

    def set_race_points(self, points):
        """Change le nombre de points à la race"""
        r = self.session.post("http://kcmaths.com/commun/race_post.php", {"points_race": points}, auth=self.auth)
        if "fa-check-circle" in r.text and "le score ne convient pas." not in r.text:
            return True
        return False

    def get_race_classement(self, format="json"):
        """Renvoie la liste des groupes de la race."""
        r = self.session.get("http://kcmaths.com/race_sommaire.php", auth=self.auth)
        soup = BeautifulSoup(r.content, "html.parser")
        classement = {}
        table = soup.find("table")
        tr = table.find_all("tr")
        name = ""
        for i in tr:
            groupe, nom, score = [ j.text for j in i.find_all("td") ]
            if groupe != "":
                name = groupe[1:]
                classement[name] = {}
            else:
                classement[name][nom] = int(score.split(" ")[2])
        if format == "json":
            return classement
        text = ""
        for key, value in classement.items():
            text+="\t"+key+"\n"+"\n".join([f"{value[i]}\t{i}" for i in value.keys()])+"\n"
        return text

    def login_and_download(self, cookie=None, path="./files/kcmaths", keep_cache=True):
        """se connecte et télécharge les documents avec les informations de connexion données"""
        if cookie is None:
            self.login()
        else:
            self.session.cookies.set("PHPSESSID", cookie, domain='.kcmaths.com', path='/')
        files = self.get_docs()
        cache = os.listdir(path)
        for i in cache :
            if os.path.isdir(f"{path}/{i}"):
                for j in os.listdir(f"{path}/{i}"):
                    cache.append(f"{i}/{j}")
        unmodified_files = 0
        if not keep_cache :
            print("Removed cache")
        for file in files:
            file_category = file[0]
            filename = file[1]
            file_url = file[2]
            if f"{file_category}/{filename}" in cache and keep_cache:
                unmodified_files += 1
            else:
                print(f"[ x ] {filename} not in cache, downloading")
                if not os.path.exists(f"{path}/{file_category}"):
                    os.mkdir(f"{path}/{file_category}")
                self.download_file(f"http://kcmaths.com/{file_url}", f"{path}/{file_category}/{filename}")
        if keep_cache:
            print(f"[ > ] {unmodified_files} already in cache")

def __main__(options, args):
    """fonction principale si le programme n'est pas exécuté en tant que module"""
    if options.username == "":
        print("Un nom d'utilisateur doit être spécifié")
        return
    if options.password == "":
        print("Un mot de passe doit être spécifié")
        return
    if len(args) == 0:
        print("Une action doit être spécifiée")
        return

    if args[0] == "download":
        session = Session(options.username, options.password)
        session.login_and_download(
            path=options.path,
            keep_cache=not options.clear_cache
        )
        result=1
    elif args[0] == "set-race":
        session = Session(options.username, options.password)
        session.login()
        session.set_race_points(options.score)
        result=1
    elif args[0] == "get-race":
        session = Session(options.username, options.password)
        session.login()
        session.result = get_race_classement(format=options.format)
    else:
        print(f"Invalid action {args[0]}")
        result=0
    return result

USAGE = "usage: %prog (download|get-race|set-race) [options]"
parser = OptionParser(usage=USAGE)
parser.add_option(
    "-u",
    "--username",
    dest="username",
    help="Nom d'utilisateur",
    action="store",
    default=""
)

parser.add_option(
    "-p",
    "--password",
    dest="password",
    help="Mot de passe",
    action="store",
    default=""
)

parser.add_option(
    "-P",
    "--path",
    dest="path",
    help="chemin où stocker les fichiers téléchargés",
    action="store",
    default="./files/kcmaths"
)

parser.add_option(
    "-s",
    "--score",
    dest="score",
    help="Nombres de points à la race",
    action="store",
    default=0,
    type="int"
)

parser.add_option(
    "-c",
    "--clear-cache",
    dest="clear_cache",
    help="Supprimer le cache déjà téléchargé",
    action="store_true",
    default=False
)

parser.add_option(
    "-f",
    "--format",
    dest="format",
    help="Format du classement à la race (json|text)",
    action="store",
    default="text"
)

if __name__ == "__main__" :
    (OPTIONS, args) = parser.parse_args()
    print(__main__(OPTIONS, args))
