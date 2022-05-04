#!/usr/bin/python3
from bs4 import BeautifulSoup
import subprocess
import enquiries
import random

import kcmaths
from credentials import USERNAME, PASSWORD

session = kcmaths.Session(USERNAME, PASSWORD)

def get_liste(self, mode="qdc"):
    r = self.session.get(f"http://kcmaths.com/commun/{mode}/", auth=self.auth)
    soup = BeautifulSoup(r.content, "html.parser")
    liste = []
    for a in soup.find_all("a"):
        if ".pdf" in a["href"]:
            liste.append(a["href"])
    return liste

def quiz(session, mode="qdc"):
    liste = get_liste(session, mode=mode)
    liste_chapitres = { i.split("_")[1] for i in liste if "sol" not in i }

    conditions = enquiries.choose("Quels chapitres souhaites-tu réviser ?", liste_chapitres, multi=True)
    liste_questions = [i for i in liste if True in [cond in i for cond in conditions] and not "sol" in i]

    base = f"http://kcmaths.com/commun/{mode}/"
    nb_questions = len(liste_questions)

    while len(liste_questions) != 0:
        question = random.choice(liste_questions)
        liste_questions.remove(question)

        session.download_file(base+question, ".cache.pdf")
        subprocess.call(["zathura", "--page", "0", ".cache.pdf", "--mode", "presentation"])

        solution = question.split("_")[0]+"_sol_"+"_".join(question.split("_")[1:])

        session.download_file(base+solution, ".cache.pdf")
        subprocess.call(["zathura", "--page", "0", ".cache.pdf", "--mode", "presentation"])
        print(f"[{nb_questions-len(liste_questions)}/{nb_questions}]")

if __name__ == "__main__":
    quiz(session)
