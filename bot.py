import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import asyncio

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
load_dotenv()

DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DISCORD_GUILD_ID = os.getenv('ALLOWED_SERVER_IDS')
MY_GUILD = discord.Object(id=DISCORD_GUILD_ID)  # replace with your guild id
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
DISCORD_BOT_PREFIX = ';'
bot = commands.Bot(command_prefix=commands.when_mentioned_or(DISCORD_BOT_PREFIX),
                    description='A LoL Esports Assistant Bot',
                    intents=intents)

async def load_cogs():
    for file in os.listdir('./cogs'):
        if file.endswith('.py'):
            await bot.load_extension(f'cogs.{file[:-3]}')

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id}) -  Discord version: {discord.__version__}')
    activity = discord.Activity(name='/schedule', type=discord.ActivityType.watching)
    bot.tree.copy_global_to(guild=MY_GUILD)
    await bot.tree.sync(guild=MY_GUILD)
    await bot.change_presence(activity=activity)

async def main():
    async with bot:
        await load_cogs()
        await bot.start(DISCORD_BOT_TOKEN)

if __name__ == '__main__':
    asyncio.run(main())
