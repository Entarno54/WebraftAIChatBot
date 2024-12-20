import nextcord as disnake
from nextcord.ext import commands
import json
import asyncio
import requests

bot = disnake.Client(intents=disnake.Intents.all())

curfile = open('./data.json', "r")
data = json.loads(curfile.read())
curfile.close()
userpreset = {"id": 'none', "api-key": 'none', "model": "gpt-3.5-turbo",
                     "chat": [{"role": "system", "content": "You are helpful assistant"}], "endpoint": "freeapi"}

async def find(list: list, param: str, value: any):
    found = None
    for g in list:
        print(g)
        if g[param] == value:
            found = g
    return found


async def flush(filepath, dataflushing):
    with open(filepath, "w") as curfile:
        curfile.write(json.dumps(dataflushing))
        curfile.flush()
        curfile.close()


async def check_mod(prompt):
    mod = requests.post('https://api.sightengine.com/1.0/text/check.json',
                        data={
                            "text": prompt,
                            "lang": "en",
                            "mode": "rules",
                            "api_user": "255972626",
                            "api_secret": "yFfqLEJ6dfHiFvcdWHwX7JTqhR"})
    mod = mod.json()
    result: list = mod['profanity']['matches']
    if result.__len__() > 0:
        return True
    else:
        return False


@bot.slash_command()
async def help(ctx):
    await ctx.response.send_message(
        "Set your API key through /api_key [key] and @ping bot or reply to already existing message of bot to start chatting. \nOther commands: /clear [system message], /model [model] (default model is gpt-3.5-turbo)",
        ephemeral=True)


@bot.slash_command()
async def api_key(ctx: disnake.Interaction, key: str):
    user = await find(data, "id", ctx.user.id)
    if not user:
        grr = userpreset.copy()
        grr['id'] = ctx.user.id
        data.append(grr)
        user = await find(data, "id", ctx.user.id)
    user["api-key"] = key
    await flush("./data.json", data)
    await ctx.response.send_message(f"Successfully set {key} as your api key.", ephemeral=True)


@bot.slash_command()
async def clear(ctx, system_message: str):
    user = await find(data, "id", ctx.user.id)
    if not user:
        grr = userpreset.copy()
        grr['id'] = ctx.user.id
        data.append(grr)
        user = await find(data, "id", ctx.user.id)
    user["chat"] = [{"role": "system", "content": system_message}]
    await flush("./data.json", data)
    await ctx.response.send_message(f"Successfully cleared chat and set system message to {system_message}",
                                    ephemeral=True)


@bot.slash_command(guild_ids=[1106816467074297866])
async def set_model(ctx, model: str):
    user = await find(data, "id", ctx.user.id)
    if not user:
        grr = userpreset.copy()
        grr['id'] = ctx.user.id
        data.append(grr)
        user = await find(data, "id", ctx.user.id)
    user["model"] = model
    await flush("./data.json", data)
    await ctx.response.send_message(f"Successfully set your model to {model}", ephemeral=True)


@bot.slash_command(guild_ids=[1106816467074297866])
async def api_endpoint(ctx: disnake.Interaction, endpoint: str = disnake.SlashOption(name="type", choices={"Free": "freeapi", "Paid": "v1"})):
    user = await find(data, "id", ctx.user.id)
    if not user:
        grr = userpreset.copy()
        grr['id'] = ctx.user.id
        data.append(grr)
        user = await find(data, "id", ctx.user.id)
    user["endpoint"] = endpoint
    await flush("./data.json", data)
    await ctx.response.send_message(f"Successfully set your endpoint to {endpoint}", ephemeral=True)

@bot.event
async def on_message(ctx: disnake.Message):
    for m in ctx.mentions:
        if m.id == bot.user.id:
            user = await find(data, "id", ctx.author.id)
            if not user:
                return await ctx.reply("Set your api key through /api_key [key].")
            msg = await ctx.reply("Generating answer...")
            if await check_mod(ctx.content):
                return await msg.edit(content="Your request got moderated.")
            print("Passed moderation")
            user['chat'].append({"role": "user", "content": ctx.content})
            print("Requesting")
            try:
                request = requests.post(f"https://api.webraft.in/{user['endpoint']}/chat/completions", headers={
                "Authorization": f"Bearer {user['api-key']}", "Content-type": "application/json"
            }, json={
                "model": user['model'], "messages": user['chat'], "max_tokens": 2000
            })
                print("Got answer")
                js = request.json()
                await msg.edit(content=js['choices'][0]['message']['content'])
                user['chat'].append({"role": "assistant", "content": js['choices'][0]['message']['content']})
                await flush("./data.json", data)
            except requests.JSONDecodeError:
                await msg.edit(content=f"Error: {request.content}")
            except KeyError:
                js = request.json()
                await msg.edit(content=f"Got an error: {js}")
            except requests.Timeout:
                await msg.edit(content=f"API didn't reply.")


@bot.event
async def on_ready():
    print(f"Ready as {bot.user}")


bot.run("")
