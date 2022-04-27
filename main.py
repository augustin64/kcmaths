#!/usr/bin/python3
"""Little bot to interact with kcmaths.com"""
from discord.ext import commands
import asyncio
import discord
import requests
import json

import kcmaths
from auth import TOKEN

with open("accounts.json", "r") as file:
    accounts = json.load(file)

valid_author = lambda ctx : str(ctx.author.id) in accounts


bot = commands.Bot(command_prefix='%')

def write_accounts():
    acc = {}
    for account in accounts.keys():
        acc[account] = {
            "username": accounts[account]["username"],
            "password": accounts[account]["password"],
            "dernierDS": accounts[account]["dernierDS"]
        }
    with open("accounts.json", "w") as file:
        json.dump(acc, file)


@bot.event
async def on_ready():
    """On ready"""
    print('Connecté en tant que:')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

    game = discord.Game("Disponible ✅ | %help")
    await bot.change_presence(status=discord.Status.idle, activity=game)

    for discord_id in accounts.keys():
        accounts[discord_id]["session"] = kcmaths.Session(accounts[discord_id]["username"], accounts[discord_id]["password"])
        accounts[discord_id]["session"].login()

    while True:
        for discord_id in accounts.keys():
            comment = accounts[discord_id]["session"].get_commentaire_ds(accounts[discord_id]["dernierDS"]+1)
            if comment != " Commentaire : ":
                accounts[discord_id]["dernierDS"] += 1
                user = await bot.fetch_user(discord_id)
                await user.send(f"Commentaire du DS {accounts[discord_id]['dernierDS']} disponible.")
        write_accounts()
        await asyncio.sleep(3600)


@bot.command()
async def leaderboard(ctx, *args):
    """Returns the leaderboard state"""
    if valid_author(ctx):
        classement = accounts[str(ctx.author.id)]["session"].get_race_classement()
        if len(args) == 0:
            text = ""
            for key, value in classement.items():
                text+="\t"+key+"\n"+"\n".join([f"{value[i]}\t{i}" for i in value.keys()])+"\n"
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
            text = "\n".join([ f"{i[0]}\t{i[1]}" for i in match ])
            await ctx.send(f"Voici les élèves correspondant au filtre: ```{text}```")
    else:
        await ctx.reply(f"Votre compte n'est pas inscrit. Utilisez `{bot.command_prefix}login <username> <password>` pour vous authentifier.")

@bot.command()
async def lb(ctx, *args):
    """Returns the leaderboard state"""
    return await leaderboard(ctx, *args)

@bot.command()
async def info(ctx):
    """Renvoie l'état du compte"""
    if valid_author(ctx):
        await ctx.reply(f"Connecté dans {accounts[str(ctx.author.id)]['session'].get_prenom_nom()}")
    else:
        await ctx.reply(f"Votre compte n'est pas inscrit. Utilisez `{bot.command_prefix}login <username> <password>` pour vous authentifier.")


@bot.command()
async def login(ctx, *args):
    if len(args) != 2:
        await ctx.reply(f"Utilisez `{bot.command_prefix}login <username> <password>` pour vous authentifier.")
    else:
        if valid_author(ctx):
            await ctx.reply("Vous êtes déjà authentifié.")
        else:
            session = kcmaths.Session(args[0], args[1])
            session.login()
            if session.get_prenom_nom() != None:
                accounts[str(ctx.author.id)] = {
                    "username": args[0],
                    "password": args[1],
                    "dernierDS": session.get_dernier_ds_public(),
                    "session": session
                }
                write_accounts()
                await ctx.reply(f"Connecté dans {session.get_prenom_nom()}")
            else:
                await ctx.reply("Échec de la connexion, veuillez vérifier vos identifiants.")


@bot.command()
async def ds(ctx, *args):
    """Renvoie le commentaire du DS spécifié"""
    if len(args) == 0:
        await ctx.reply(f"`{bot.command_prefix}ds <numero>`")
    else:
        if valid_author(ctx):
            comment = accounts[str(ctx.author.id)]['session'].get_commentaire_ds(args[0])
            if comment != " Commentaire : ":
                await ctx.reply(comment)
            else:
                await ctx.reply("Pas de commentaire disponible")
        else:
            await ctx.reply(f"Votre compte n'est pas inscrit. Utilisez `{bot.command_prefix}login <username> <password>` pour vous authentifier.")

@bot.command()
async def ip(ctx):
    """Return the bot's IP"""
    if valid_author(ctx):
        await ctx.reply(f"http://{requests.get('https://api.ipify.org/').text}/")
        return
    await ctx.reply(f"Votre compte n'est pas inscrit. Utilisez `{bot.command_prefix}login <username> <password>` pour vous authentifier.")

@bot.command()
async def points(ctx, *args):
    """Changes the number of points"""
    if valid_author(ctx):
        if len(*args) == 0:
            await ctx.reply("Merci de préciser le nombre de points à rajouter")
            return
        accounts[str(ctx.author.id)]["session"].set_race_points(args[0])
        checkmark = "✅"
        await ctx.message.add_reaction(checkmark)
        return
    await ctx.reply(f"Votre compte n'est pas inscrit. Utilisez `{bot.command_prefix}login <username> <password>` pour vous authentifier.")
    return

@bot.command()
async def p(ctx, *args):
    """Changes the number of points"""
    return await points(ctx, *args)

bot.run(TOKEN)