#!/usr/bin/python3
"""Little bot to interact with kcmaths.com"""
import asyncio
import json
import os
import random

import discord
import requests
from discord.ext import commands

import kcmaths
from auth import TOKEN

if not os.path.exists("accounts.json"):
    with open("accounts.json", "w", encoding="utf8") as file:
        file.write("{}")

with open("accounts.json", "r", encoding="utf8") as file:
    accounts = json.load(file)


bot = commands.Bot(command_prefix="%")



def login_required(fn):
    async def decorated_fn(ctx, *args):
        if str(ctx.author.id) not in accounts:
            await ctx.reply(
f"""Votre compte n'est pas inscrit.
Utilisez `{bot.command_prefix}login <username> <password>`
ou `{bot.command_prefix}cookie <username> <cookie>` pour vous authentifier.
Pour récupérer le cookie:
    Se connecter sur kcmaths dans une fenêtre de navigation privée/ un navigateur temporaire
    ouvrir la console Javascript (Ctrl+Maj+K)
    Taper `document.cookie`
    Cela renvoie `> "PHPSESSID=<cookie>"`
    Après avoir copié le cookie, la fenêtre peut être fermée (sans se déconnecter de kcmaths évidemment)
    
Attention ! La connexion par cookie semble ne pas fonctionner sur tout le site"""
            )
            return None
        return await fn(ctx, *args)

    return decorated_fn


def write_accounts():
    """
    Sauvegarde dans un fichier json
    """
    acc = {}
    for account in accounts.keys():
        acc[account] = {
            "username": accounts[account]["username"],
            "password": accounts[account]["password"],
            "cookie": accounts[account]["cookie"],
            "dernierDS": accounts[account]["dernierDS"],
        }
    with open("accounts.json", "w") as file:
        json.dump(acc, file)


def fix_account(discord_id, accounts_dict=accounts):
    """
    Vérifie que tous les comptes ont bien un accès
    """
    text = "Unauthorized"
    accounts_keys = [key for key in accounts_dict.keys() if key != str(discord_id)]
    while "Unauthorized" in text:
        r = requests.get(
            "http://kcmaths.com/docs", auth=accounts_dict[str(discord_id)]["session"].auth
        )
        text = r.text
        if "401" in text:
            if len(accounts_keys) == 0:
                break
            acc = random.choice(accounts_keys)
            accounts_keys.remove(acc)
            # Certains comptes ne peuvent plus utiliser leur mot de passe
            # pour accéder aux documents une fois changé,
            # on leur donne donc une clé d'authentification
            # différente de la leur, qui ne leur donnera pas
            # le compte de cette autre personne pour autant.
            accounts_dict[str(discord_id)]["session"].auth = (
                accounts_dict[acc]["username"],
                accounts_dict[acc]["password"],
            )


def ds_embed(account, numero, detailed=False):
    """
    Renvoie un embed contenant le ds spécifié
    """
    data = account["session"].get_ds(numero)
    embed = discord.Embed(colour=discord.Colour.blue())
    embed.set_author(name=data["nom"])
    if data["commentaire"] is not None and data["commentaire"] != "Commentaire : ":
        embed.add_field(
            name="Commentaire", value=data["commentaire"][14:], inline=False
        )
    else:
        embed.add_field(
            name="Commentaire", value="Pas de commentaire disponible", inline=False
        )

    if data["note"] is not None:
        embed.add_field(name="Note", value=f'{data["note"]}/20', inline=True)
    if data["note_brute"] is not None:
        embed.add_field(
            name="Note brute",
            value=f'{data["note_brute"]}/{data["coeff_brut"]}',
            inline=True,
        )

    if data["rang"] is not None:
        embed.add_field(name="Rang", value=str(data["rang"]), inline=False)

    if data["moyenne"] is not None:
        embed.add_field(name="Moyenne", value=str(data["moyenne"]), inline=False)

    if data["points_engages"] is not None:
        embed.add_field(
            name="Points engagés dans le sujet",
            value=str(data["points_engages"]),
            inline=False,
        )

    if data["questions_sujet"] is not None:
        embed.add_field(
            name="Nombre de questions du sujet",
            value=str(data["questions_sujet"]),
            inline=False,
        )

    if data["meilleure_note"] is not None:
        embed.add_field(
            name="Meilleure note", value=f'{data["meilleure_note"]}/20', inline=False
        )

    if detailed:
        if data["reussies"] is not None:
            embed.add_field(
                name="Questions réussies", value=str(data["reussies"]), inline=True
            )
        if data["tx_reussies"] is not None:
            embed.add_field(
                name="Taux de réussite", value=str(data["tx_reussies"]), inline=True
            )

        if data["traitees"] is not None:
            embed.add_field(
                name="Questions traitées", value=str(data["traitees"]), inline=True
            )
        if data["tx_reussies"] is not None:
            embed.add_field(
                name="Taux de questions traitées",
                value=str(data["tx_traitees"]),
                inline=True,
            )

        if data["incompletes"] is not None:
            embed.add_field(
                name="Questions incomplètes",
                value=str(data["incompletes"]),
                inline=True,
            )
        if data["tx_incompletes"] is not None:
            embed.add_field(
                name="Taux de questions incomplètes",
                value=str(data["tx_incompletes"]),
                inline=True,
            )

        if data["fausses"] is not None:
            embed.add_field(
                name="Questions fausses", value=str(data["fausses"]), inline=True
            )
        if data["tx_fausses"] is not None:
            embed.add_field(
                name="Taux de questions fausses",
                value=str(data["tx_fausses"]),
                inline=True,
            )
    return embed


@bot.event
async def on_ready():
    """On ready"""
    print("Connecté en tant que:")
    print(bot.user.name)
    print(bot.user.id)
    print("------")

    game = discord.Game("Disponible ✅ | %help")
    await bot.change_presence(status=discord.Status.idle, activity=game)

    for discord_id in accounts.keys():
        accounts[discord_id]["session"] = kcmaths.Session(
            accounts[discord_id]["username"], accounts[discord_id]["password"]
        )
        if accounts[discord_id]["password"] is not None:
            accounts[discord_id]["session"].login()
        else:
            # La connexion peut uniquement se faire par mot de passe ou cookie
            accounts[discord_id]["session"].cookie_login(accounts[discord_id]["cookie"])
        fix_account(discord_id)

    while True:
        for discord_id in accounts.keys():
            data = accounts[discord_id]["session"].get_ds(
                accounts[discord_id]["dernierDS"] + 1
            )
            if data["commentaire"] != " Commentaire : ":
                accounts[discord_id]["dernierDS"] += 1
                user = await bot.fetch_user(discord_id)
                await user.send(
                    f"Commentaire du DS {accounts[discord_id]['dernierDS']} disponible."
                )
        write_accounts()
        await asyncio.sleep(3600)


@bot.command(name="leaderboard")
@login_required
async def leaderboard(ctx, *args):
    """Returns the leaderboard state"""
    classement = accounts[str(ctx.author.id)]["session"].get_race_classement()
    if len(args) == 0:
        text = ""
        for key, value in classement.items():
            text += (
                "\t"
                + key
                + "\n"
                + "\n".join([f"{value[i]}\t{i}" for i in value.keys()])
                + "\n"
            )
        await ctx.reply(f"Classement actuel:```{text}```")
    else:
        classement_noms = {}
        for groupe in classement.keys():
            for eleve in classement[groupe].keys():
                classement_noms[eleve] = classement[groupe][eleve]
        match = []
        for eleve in classement_noms.keys():
            if args[0].lower() in eleve.lower():
                match.append((eleve, classement_noms[eleve]))
        text = "\n".join([f"{i[0]}\t{i[1]}" for i in match])
        await ctx.send(f"Voici les élèves correspondant au filtre: ```{text}```")


@bot.command(name="lb")
async def lb(ctx, *args):
    """Returns the leaderboard state"""
    return await leaderboard(ctx, *args)


@bot.command(name="info")
@login_required
async def info(ctx):
    """Renvoie l'état du compte"""
    await ctx.reply(
        f"Connecté dans {accounts[str(ctx.author.id)]['session'].get_prenom_nom()}"
    )


@bot.command()
async def login(ctx, *args):
    """
    Connexion d'un nouvel utilisateur
    """
    if len(args) != 2:
        await ctx.reply(
            f"Utilisez `{bot.command_prefix}login <username> <password>` pour vous authentifier."
        )
    else:
        if str(ctx.author.id) in accounts:
            await ctx.reply("Vous êtes déjà authentifié.")
        else:
            session = kcmaths.Session(args[0], args[1])
            if session.login():
                accounts[str(ctx.author.id)] = {
                    "username": args[0],
                    "password": args[1],
                    "dernierDS": session.get_dernier_ds_public(),
                    "cookie": None,
                    "session": session,
                }
                write_accounts()
                fix_account(ctx.author.id)
                await ctx.reply(f"Connecté dans {session.get_prenom_nom()}")
            else:
                await ctx.reply(
                    "Échec de la connexion, veuillez vérifier vos identifiants."
                )


@bot.command()
async def cookie(ctx, *args):
    """
    Connexion d'un nouvel utilisateur avec l'utilisation d'un cookie
    """
    if len(args) != 2:
        await ctx.reply(
f"""Utilisez `{bot.command_prefix}cookie <username> <cookie>` pour vous authentifier.
Pour récupérer le cookie:
    Se connecter sur kcmaths dans une fenêtre de navigation privée/ un navigateur temporaire
    ouvrir la console Javascript (Ctrl+Maj+K)
    Taper `document.cookie`
    Cela renvoie `> "PHPSESSID=<cookie>"`
    Après avoir copié le cookie, la fenêtre peut être fermée (sans se déconnecter de kcmaths évidemment)"""
        )
    else:
        if str(ctx.author.id) in accounts:
            await ctx.reply("Vous êtes déjà authentifié.")
        else:
            session = kcmaths.Session(args[0], None)
            session.cookie_login(str(args[1]))
            if session.get_prenom_nom() is not None:
                accounts[str(ctx.author.id)] = {
                    "username": args[0],
                    "password": None,
                    "dernierDS": session.get_dernier_ds_public(),
                    "cookie": args[1],
                    "session": session,
                }
                # On donne un autre couple (identifiant, mot de passe) à l'utilisateur
                fix_account(ctx.author.id)
                write_accounts()
                await ctx.reply(f"Connecté dans {session.get_prenom_nom()}")
            else:
                await ctx.reply(
                    "Échec de la connexion, veuillez vérifier vos identifiants."
                )


@bot.command(name="ds")
@login_required
async def ds(ctx, *args):
    """Renvoie le commentaire du DS spécifié"""
    if len(args) == 0:
        await ctx.reply(f"`{bot.command_prefix}ds <numero>`")
    else:
        detailed = False
        if len(args) >= 2 and args[1] == "detailed":
            detailed = True
        await ctx.reply(
            embed=ds_embed(accounts[str(ctx.author.id)], args[0], detailed=detailed)
        )


@bot.command(name="points")
@login_required
async def points(ctx, *args):
    """Changes the number of points"""
    if len(*args) == 0:
        await ctx.reply("Merci de préciser le nombre de points à rajouter")
        return
    if accounts[str(ctx.author.id)]["session"].set_race_points(args[0]):
        emote = "✅"
    else:
        emote = "❌"
    await ctx.message.add_reaction(emote)
    return


@bot.command(name="stats")
@login_required
async def stats(ctx, *args):
    """Affiche les statistiques de correction"""
    data = {}
    for key in accounts.keys():
        if accounts[key]["dernierDS"] in data.keys():
            data[accounts[key]["dernierDS"]] += 1
        else:
            data[accounts[key]["dernierDS"]] = 1

    text = "Statistiques de correction :"

    for key in data.keys():
        if data[key] > 1:
            text += f"\n{data[key]}/{len(accounts)} DS n°{key} corrigés."
        else:
            text += f"\n{data[key]}/{len(accounts)} DS n°{key} corrigé."

    await ctx.reply(text)
    return


@bot.command()
async def p(ctx, *args):
    """Changes the number of points"""
    return await points(ctx, *args)


bot.run(TOKEN)
