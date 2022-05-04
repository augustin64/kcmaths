#!/usr/bin/python3
"""
Script pour faire les qdc (Questions de cours) et vof (Vrai ou Faux) plus simplement.
"""
import sys
import random
import subprocess

from bs4 import BeautifulSoup
import enquiries

import kcmaths
from credentials import USERNAME, PASSWORD

session_ = kcmaths.Session(USERNAME, PASSWORD)

def get_liste(self, mode="qdc"):
    """Renvoie la liste des documents disponibles dans kcmaths/commun/{mode} """
    r = self.session.get(f"http://kcmaths.com/commun/{mode}/", auth=self.auth)
    soup = BeautifulSoup(r.content, "html.parser")
    liste = []
    for a in soup.find_all("a"):
        if ".pdf" in a["href"]:
            liste.append(a["href"])
    return liste

def quiz(session, mode="qdc"):
    """Fonction principale gérant le quiz"""
    liste = get_liste(session, mode=mode)
    # On crée un set contenant les titres de chapitres
    liste_chapitres = { i.split("_")[1] for i in liste if "sol" not in i }

    # Choix du ou des chapitres à réviser
    conditions = enquiries.choose(
        "Quels chapitres souhaites-tu réviser ?",
        liste_chapitres,
        multi=True
    )
    liste_questions = []
    for i in liste:
        if True in [cond == i.split("_")[1] for cond in conditions] and not "sol" in i:
            liste_questions.append(i)

    base = f"http://kcmaths.com/commun/{mode}/"
    nb_questions = len(liste_questions)

    while len(liste_questions) != 0:
        question = random.choice(liste_questions)
        liste_questions.remove(question)

        session.download_file(base+question, ".cache.pdf")
        # Ouvre le pdf téléchargé avec Zathura en plein écran. Peut-être remplacé par
        # un autre lecteur pdf supportant un interface en ligne de commande
        # qui maintient le même thread
        # (Afin d'attendre qu'un pdf soit fermé pour afficher le suivant.)
        subprocess.call(["zathura", "--page", "0", ".cache.pdf", "--mode", "presentation"])

        solution = question.split("_")[0]+"_sol_"+"_".join(question.split("_")[1:])

        session.download_file(base+solution, ".cache.pdf")
        subprocess.call(["zathura", "--page", "0", ".cache.pdf", "--mode", "presentation"])
        print(f"[{nb_questions-len(liste_questions)}/{nb_questions}]")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        MODE = sys.argv[1]
    else:
        MODE = "qdc"
    quiz(session_, mode=MODE)
