import discord
from discord.ext import commands
from discord import app_commands
import utils.lolesports as lol
import pandas as pd
from datetime import datetime, timezone, timedelta
import pytz
from reactionmenu import ViewMenu, ViewButton

class Query(commands.Cog):
    def __init__(self, client: commands.Bot) -> None:
        self.client = client
        self.TIMEZONE = 'US/Pacific'
        self.lolesports = lol.LolEsports(region=lol.Region.LCS)

    @commands.Cog.listener()
    async def on_ready(self):
        print('Query commands are ready.')    
    
    def convert_timezone(self, time_str:str, timezone:str = 'US/Pacific'):
        # Parse input string as a datetime object in UTC
        utc_timestamp = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ")
        # Convert the UTC timestamp to PST
        pst_timestamp = utc_timestamp.replace(tzinfo=pytz.timezone('UTC')).astimezone(pytz.timezone(timezone) )
        # Format the PST timestamp without timezone offset, seconds and convert to 12 hr format
        pst_timestamp = pst_timestamp.strftime("%Y-%m-%d %H:%M %p")
        return pst_timestamp

    @app_commands.command(name='live', description='Get the live events')
    async def live(self, interaction: discord.Interaction):
        result = self.lolesports.get_live()
        await interaction.response.send_message(result)
    
    @app_commands.command(name='schedule', description='Get the schedule of upcoming events')
    @app_commands.describe(region='The region to get the schedule for. [required] Defaults to LEC.')
    async def schedule(self, interaction: discord.Interaction, region: str = 'LEC'):
        print(region)
        # validate region
        try:
            keyword = lol.Region[region.upper()]
        except KeyError as e:
            print(f'**`ERROR:`** {type(e).__name__} - {e}')
            await interaction.response.send_message(f'Invalid region: {region}')
            return

        data = self.lolesports.get_schedule(keyword)
        # create dataframe
        df = pd.DataFrame(data['data']['schedule']['events'])
        # unstarted_df = df[df['state'] == 'unstarted'].reset_index(drop=True)
        menu = ViewMenu(interaction, menu_type=ViewMenu.TypeEmbed)
        for index, row in df.iterrows():
            # create new embed if the current embed is filled
            embed = discord.Embed(title=f"Schedule for \"{keyword.name}\":", 
                description = f"Upcoming matches for the {df['league'].iloc[0]['name']}",
                color = discord.Color.teal(),
                # set the timestamp to the current time in PST time
                timestamp = datetime.now(timezone(timedelta(hours=-7))))
            embed.set_footer(text="Time shown in {}".format(self.TIMEZONE))   
        
            teams = [(team['name'], team['code']) for team in row['match']['teams']]
            teams_str = ' vs '.join([f'{name}({code})' for name, code in teams])
            embed.add_field(name='Teams', value=teams_str, inline=False)

            embed.add_field(name='Start time',
                            value= f"{self.convert_timezone(row['startTime'], self.TIMEZONE)} ({row['state']})", 
                            inline=False)
            embed.add_field(name='League', value=row['league']['name'], inline=True)
            embed.add_field(name='Stage', value=row['blockName'], inline=True)
            # add a strategy field with the format of bestOf 5
            embed.add_field(name='Format', value=f"{row['match']['strategy']['type']} {row['match']['strategy']['count']}", inline=True)
            # only add this field if its not the last row
            if index != len(df) - 1:
                embed.add_field(name="\uFEFF", value="Next up", inline=False)

            # add the embed to the menu for every 4 rows or there are less than 4 rows in the dataframe
            # if len(unstarted_df) < 5 or (index % 4 == 0 and index != 0):
            menu.add_page(embed)
            
        menu.add_button(ViewButton.go_to_first_page())
        menu.add_button(ViewButton(style=discord.ButtonStyle.green, label='Back', custom_id=ViewButton.ID_PREVIOUS_PAGE))
        menu.add_button(ViewButton(style=discord.ButtonStyle.primary, label='Next', custom_id=ViewButton.ID_NEXT_PAGE))
        menu.add_button(ViewButton.go_to_last_page())
        menu.add_button(ViewButton.end_session())
        # await interaction.response.send_message(content='Upcoming games')
        await menu.start()

    # using slash commands create the leagues command
    @app_commands.command(name='leagues', description='Display all the esports pro leagues and regions')
    async def leagues(self, interaction: discord.Interaction,):
        # icon url constants
        LOL_ESPORTS_ICON = r"https://am-a.akamaihd.net/image?resize=140:&f=http%3A%2F%2Fstatic.lolesports.com%2Fteams%2F1681281407829_LOLESPORTSICON.png"
        RIOT_ICON = 'https://static.developer.riotgames.com/img/logo.png'
        leagues = self.lolesports.get_leagues(is_sorted=True)
        if leagues is None:
            await interaction.response.send_message('Something went wrong.')
            return
        # create dataframe
        df = pd.DataFrame(leagues)
        menu = ViewMenu(interaction, menu_type=ViewMenu.TypeEmbed)

        # loop through the dataframe create embed and add to menu
        for index, row in df.iterrows():
            embed = discord.Embed(title=f"{row['name']}",
                                # description=f"Pro league #{index+1}",
                                color=discord.Color.blurple(),
                                url=f"https://lolesports.com/schedule?leagues={row['slug']}")
            embed.set_author(name="LoL Esports League", 
                            icon_url= LOL_ESPORTS_ICON)
                            # url="https://lolesports.com")                                
            embed.add_field(name='Region', value=row['region'].title(), inline=False)
            embed.add_field(name='Schedules', value=f"[Click here](https://lolesports.com/schedule?leagues={row['slug']})", inline=True)
            embed.add_field(name='ID', value=row['id'], inline=True)
            embed.set_image(url=row['image'])
            embed.set_footer(text="Powered by Riot Games", icon_url=RIOT_ICON)
            # add the embed to the menu
            menu.add_page(embed)
        # add buttons to the menu
        menu.add_button(ViewButton.go_to_first_page())
        menu.add_button(ViewButton(style=discord.ButtonStyle.green, label='Back', custom_id=ViewButton.ID_PREVIOUS_PAGE))
        menu.add_button(ViewButton(style=discord.ButtonStyle.primary, label='Next', custom_id=ViewButton.ID_NEXT_PAGE))
        menu.add_button(ViewButton.go_to_last_page())
        menu.add_button(ViewButton(style=discord.ButtonStyle.danger, label='close', custom_id=ViewButton.ID_END_SESSION))
        await menu.start()

    
async def setup(client: commands.Bot) -> None:
    await client.add_cog(Query(client))
