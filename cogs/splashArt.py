import discord
from discord.ext import commands
import random
import requests
from io import BytesIO
from dotenv import load_dotenv
import os

load_dotenv()

class SplashArt(commands.Cog):
    def __init__(self, client: commands.Bot) -> None:
        self.client = client
        self.patch = '13.18.1'
        self.cdn_endpoint = os.getenv('CDN_API_BASE')
        self.header = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
                    'Referer': 'https://developer.riotgames.com/'
        }

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{self.__class__.__name__} cog is ready')

    def get_random_champion(self) -> dict:
        champions_url = f'{self.cdn_endpoint}/{self.patch}/data/en_US/championFull.json'
        response = requests.get(champions_url, headers=self.header).json()
        champions = list(response['data'].values())
        champion = random.choice(champions)
        # champion = response['data'].get('TwistedFate')
        # print(f"{champion['name']}, {champion['title']}")
        return champion

    @staticmethod
    def get_random_skin(champion: dict) -> dict:
        skins = champion['skins']
        skin = random.choice(skins)
        skin_name = f"{skin['name']}" if skin['num'] != 0 else f"Default {champion['name']}"
        print(f"{skin_name} | skin ID: {skin['num']}")
        return skin
    
    def get_splash_art(self, champion: dict, skin: dict) -> bytes:
        splash_art_url = f"{self.cdn_endpoint}/img/champion/splash/{champion['id']}_{skin['num']}.jpg"
        response = requests.get(splash_art_url, headers=self.header)
        if response.status_code == 200:
            return response.content
        else:
            print(f'Error: {response.status_code}')
            return None

    # splash art command with alias 'skin'
    @commands.command(name='splash', aliases=['skin'], help='Sends a random splash art from League of Legends')
    async def splash(self, ctx: commands.Context):
        async with ctx.typing():
            champion = self.get_random_champion()
            skin = self.get_random_skin(champion)
            splash_art = self.get_splash_art(champion, skin)
            if splash_art:
                # if the skin number is 0, then the skin is the default skin, use the champion name + skin number
                filename = f"{skin['name']}_{skin['num']}.jpg" if skin['num'] != 0 else f"{champion['name']}_{skin['num']}.jpg"
                await ctx.send(f"You got the **{skin['name']}** skin for **{champion['name']}**!", 
                                file=discord.File(BytesIO(splash_art), filename=filename))
            else:
                await ctx.send('Error: splash art not found')

    # a surprise command that sends 4 random splash arts, alias 'sp'
    @commands.command(name='surprise', aliases=['sp'], help='Sends 4 random splash arts from League of Legends')
    async def surprise(self, ctx: commands.Context):
        embeds = []
        images = []
        skin_list = [] # list of skin names for the message
        async with ctx.typing():
            champions = [self.get_random_champion() for _ in range(4)]  # create a list of 4 random champions
            skins = [self.get_random_skin(champion) for champion in champions]  # create a list of 4 random skins
            
            # create a list of 4 embeds and set url to https://universe.leagueoflegends.com/
            for champion, skin in zip(champions, skins):
                splash_art = self.get_splash_art(champion, skin)
                if splash_art:
                    # if the skin number is 0, then the skin is the default skin, use the champion name + skin number (weird bug where the filename has to have a space in it)
                    filename = f"{skin['name']}_{skin['num']}.jpg" if skin['num'] != 0 else f"Default {champion['name']}_{skin['num']}.jpg" 
                    skin_list.append(f"{skin['name']}" if skin['num'] != 0 else f"Default {champion['name']}") 
                    embeds.append(discord.Embed(url="https://universe.leagueoflegends.com/").set_image(url=f"attachment://{filename}"))
                    images.append(discord.File(BytesIO(splash_art), filename=filename))
                else:
                    await ctx.send('Error: splash art not found')
            # a title as a placeholder for the embeds
            embeds[0].title = f"Generating art..."
            await ctx.send(f"🎉🎉 Wooho! You got **{', '.join(skin_list)}**! 🎊🎁", 
                embeds=embeds, 
                files=images, 
                reference=ctx.message, 
                mention_author=True, 
                suppress_embeds=True)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(SplashArt(client))