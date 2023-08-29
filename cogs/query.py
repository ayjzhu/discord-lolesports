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

    # helper function to create embeds for the leagues
    def _create_league_embeds(self, leagues: list) -> list:
        '''Create embeds for the leagues'''
        # icon url constants
        LOL_ESPORTS_ICON = r"https://am-a.akamaihd.net/image?resize=140:&f=http%3A%2F%2Fstatic.lolesports.com%2Fteams%2F1681281407829_LOLESPORTSICON.png"
        RIOT_ICON = 'https://static.developer.riotgames.com/img/logo.png'        
        # create an embed list to store all the embeds
        embeds = []
        for league in leagues:
            embed = discord.Embed(title=f"{league['name']}",
                                color=discord.Color.blurple(),
                                url=f"https://lolesports.com/schedule?leagues={league['slug']}")
            embed.set_author(name="LoL Esports League", 
                            icon_url= LOL_ESPORTS_ICON)
            embed.add_field(name='Region', value=league['region'].title(), inline=False)
            embed.add_field(name='Schedules', value=f"[Click here](https://lolesports.com/schedule?leagues={league['slug']})", inline=True)
            embed.add_field(name='ID', value=league['id'], inline=True)
            embed.set_image(url=league['image'])
            embed.set_footer(text="Powered by Riot Games", icon_url=RIOT_ICON)
            embeds.append(embed)

        return embeds

    # using slash commands create the leagues command
    @app_commands.command(name='leagues', description='Display all the esports pro leagues and regions')
    async def leagues(self, interaction: discord.Interaction,):
        menu = ViewMenu(interaction, menu_type=ViewMenu.TypeEmbed, name='leagues-menu')
        leagues = self.lolesports.get_leagues(is_sorted=True)       
        if leagues is None:
            await interaction.response.send_message('Something went wrong.')
            return
        major_leagues, popular_leagues, primary_leagues = self.lolesports.get_sub_leagues(leagues)
        leagues_embeds = self._create_league_embeds(leagues)
        major_leagues_embeds = self._create_league_embeds(major_leagues)
        primary_leagues_embeds = self._create_league_embeds(primary_leagues)

        # # approach #2 to create a task and pass it to the followup
        # async def task():
        #     await menu.stop(delete_menu_message=True)
        #     # await interaction.response.edit_message(content='Deleted menu', ephemeral=True)
        #     await interaction.followup.send('Deleted menu', ephemeral=True)
        # def taskWrapper():
        #     self.client.loop.create_task(task())
        #     print("excuted task")
        
        # major_league: have all the basic navigation buttons, can navigate to the primary leagues, and all leagues
        async def major_leagues_followup():
            # await menu.stop(delete_menu_message=True)
            # add the nav buttons and the primary leagues button, all leagues button
            buttons = [*nav_buttons, primary_leagues_button, all_leagues_button]
            await menu.update(new_pages=major_leagues_embeds, new_buttons=buttons)
            
            # await major_leagues_menu.start()
        
        # all leagues: have all the basic navigation buttons, can navigate to the primary leagues, and major leagues
        async def all_leagues_followup():
            buttons = [*nav_buttons, primary_leagues_button, major_leagues_button]
            await menu.update(new_pages=leagues_embeds, new_buttons=buttons)
        
        # primary leagues: have all the basic navigation buttons, can navigate to the all leagues, and major leagues
        async def primary_leagues_followup():
            buttons = [*nav_buttons, major_leagues_button, all_leagues_button]
            await menu.update(new_pages=primary_leagues_embeds, new_buttons=buttons)

    
        # # ID caller for delete follow up to remove viewmenu asynchrounously
        async def delete_menu():
            await menu.stop(delete_menu_message=True)
            await interaction.followup.send('Deleted menu', ephemeral=True)

        delete_menu_followup = ViewButton.Followup(details=ViewButton.Followup.set_caller_details(delete_menu))
        # major leagues button
        delete_menu_button = ViewButton(
            style=discord.ButtonStyle.red,
            name='delete-button',
            label='Delete',
            custom_id=ViewButton.ID_CALLER,
            followup=delete_menu_followup,
            row=2
        )
        all_leagues_button = ViewButton(
            name='all-leagues-button', 
            style=discord.ButtonStyle.blurple, 
            label='All Regions', 
            custom_id=ViewButton.ID_CALLER,
            followup=ViewButton.Followup(details=ViewButton.Followup.set_caller_details(all_leagues_followup)),
            row=1
        )

        major_leagues_button = ViewButton(
            name='major-leagues-button', 
            style=discord.ButtonStyle.blurple, 
            label='Major Regions', 
            custom_id=ViewButton.ID_CALLER,
            followup=ViewButton.Followup(details=ViewButton.Followup.set_caller_details(major_leagues_followup)),
            row=1
        )
        primary_leagues_button = ViewButton(
            name='primary-leagues-button', 
            style=discord.ButtonStyle.blurple, 
            label='Primary Regions', 
            custom_id=ViewButton.ID_CALLER,
            followup=ViewButton.Followup(details=ViewButton.Followup.set_caller_details(primary_leagues_followup)),
            row=1
        )
        # add navigation buttons
        nav_buttons = [
            ViewButton(style=discord.ButtonStyle.gray, label='First Page', custom_id=ViewButton.ID_GO_TO_FIRST_PAGE),
            ViewButton(style=discord.ButtonStyle.primary, label='Back', custom_id=ViewButton.ID_PREVIOUS_PAGE),
            ViewButton(style=discord.ButtonStyle.success, label='Next', custom_id=ViewButton.ID_NEXT_PAGE),
            ViewButton(style=discord.ButtonStyle.secondary, label='Last Page', custom_id=ViewButton.ID_GO_TO_LAST_PAGE)
        ]
        menu.add_buttons(nav_buttons)
        menu.add_button(delete_menu_button)
        menu.add_button(primary_leagues_button)
        menu.add_button(major_leagues_button)
        menu.add_pages(leagues_embeds)
        await menu.start()

    
async def setup(client: commands.Bot) -> None:
    await client.add_cog(Query(client))
