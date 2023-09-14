import discord
from discord.ext import commands
from discord import app_commands
import utils.lolesports as lol
import pandas as pd
from datetime import datetime, timezone, timedelta
import pytz
from reactionmenu import ViewMenu, ViewButton, ViewSelect, Page

class Query(commands.Cog):
    def __init__(self, client: commands.Bot) -> None:
        self.client = client
        self.TIMEZONE = 'US/Pacific'
        self.lolesports = lol.LolEsports(region='lcs')

    @commands.Cog.listener()
    async def on_ready(self):
        print('Query commands are ready.')    
    
    def _convert_timezone(self, time_str:str, timezone:str = 'US/Pacific'):
        # Parse input string as a datetime object in UTC
        utc_timestamp = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ")
        # Convert the UTC timestamp to PST
        pst_timestamp = utc_timestamp.replace(tzinfo=pytz.timezone('UTC')).astimezone(pytz.timezone(timezone) )
        # Format the PST timestamp without timezone offset, seconds and convert to 12 hr format
        pst_timestamp = pst_timestamp.strftime("%Y-%m-%d %H:%M %p")
        return pst_timestamp
    
    # set the embed color based on the region: LCS = blurple, LEC = teal, LCK = white, LPL = red
    @staticmethod
    def get_region_color(region: str) -> discord.Color:
        region = region.upper()
        if region == 'LCS':
            return discord.Color.blurple()
        elif region == 'LEC':
            return discord.Color.teal()
        elif region == 'LCK':
            return discord.Color.from_rgb(255,255,255)
        elif region == 'LPL':
            return discord.Color.red()
        else:
            return discord.Color.random()
    
    # set emoji based on the player role
    @staticmethod
    def get_player_emoji(role: str) -> str:
        role = role.lower()
        emoji = ''
        if role == 'top':
            emoji = '↖'
        elif role == 'jungle':
            emoji = '🌴'
        elif role == 'mid':
            emoji = '↗'
        elif role == 'bottom':
            emoji = '↘'
        elif role == 'support':
            emoji = '🍼'
        else:
            emoji = '🌟'
        return emoji


    @app_commands.command(name='live', description='Get the live events')
    async def live(self, interaction: discord.Interaction):
        result = self.lolesports.live()
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
        data = self.lolesports.schedules(keyword)
        await interaction.response.defer(thinking=True)
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
                            value= f"{self._convert_timezone(row['startTime'], self.TIMEZONE)} ({row['state']})", 
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
    def _create_league_embeds(self, leagues: list, color: discord.Color) -> list:
        '''Create embeds for the leagues'''
        # icon url constants
        LOL_ESPORTS_ICON = r"https://am-a.akamaihd.net/image?resize=140:&f=http%3A%2F%2Fstatic.lolesports.com%2Fteams%2F1681281407829_LOLESPORTSICON.png"
        RIOT_ICON = 'https://static.developer.riotgames.com/img/logo.png'        
        # create an embed list to store all the embeds
        embeds = []
        for league in leagues:
            embed = discord.Embed(title=f"{league['name']}",
                color=color,
                url=f"https://lolesports.com/schedule?leagues={league['slug']}"
            )
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
        leagues = self.lolesports.leagues(is_sorted=True)       
        if leagues is None:
            await interaction.response.send_message('Something went wrong.')
            return
        major_leagues, popular_leagues, primary_leagues = self.lolesports._get_sub_leagues(leagues)
        leagues_embeds = self._create_league_embeds(leagues, discord.Color.blurple())
        major_leagues_embeds = self._create_league_embeds(major_leagues, discord.Color.blurple())
        primary_leagues_embeds = self._create_league_embeds(primary_leagues, discord.Color.green())

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
            # reset all the buttons
            menu.enable_all_buttons()
            major_leagues_button.disabled = True
            await menu.update(new_pages=major_leagues_embeds, new_buttons=buttons)
        
        # all leagues: have all the basic navigation buttons, can navigate to the primary leagues, and major leagues
        async def all_leagues_followup():
            menu.enable_all_buttons()
            all_leagues_button.disabled = True
            await menu.update(new_pages=leagues_embeds, new_buttons=buttons)
        
        # primary leagues(landing): have all the basic navigation buttons, can navigate to the all leagues, and major leagues
        async def primary_leagues_followup():
            menu.enable_all_buttons()
            primary_leagues_button.disabled = True
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
            label='All Leagues', 
            custom_id=ViewButton.ID_CALLER,
            followup=ViewButton.Followup(details=ViewButton.Followup.set_caller_details(all_leagues_followup)),
            row=1
        )
        major_leagues_button = ViewButton(
            name='major-leagues-button', 
            style=discord.ButtonStyle.blurple, 
            label='Major Leagues', 
            custom_id=ViewButton.ID_CALLER,
            followup=ViewButton.Followup(details=ViewButton.Followup.set_caller_details(major_leagues_followup)),
            row=1
        )
        primary_leagues_button = ViewButton(
            name='primary-leagues-button', 
            style=discord.ButtonStyle.green, 
            label='Primary Leagues', 
            custom_id=ViewButton.ID_CALLER,
            followup=ViewButton.Followup(details=ViewButton.Followup.set_caller_details(primary_leagues_followup)),
            row=1,
            disabled=True   # disable the button by default since the menu starts with the primary leagues
        )
        # intialize the basic layout for the starting menu: major leagues
        menu = ViewMenu(interaction, menu_type=ViewMenu.TypeEmbed, name='leagues-menu')
        # navigation buttons
        nav_buttons = [
            ViewButton(style=discord.ButtonStyle.gray, label='First Page', custom_id=ViewButton.ID_GO_TO_FIRST_PAGE),
            ViewButton(style=discord.ButtonStyle.secondary, label='Back', custom_id=ViewButton.ID_PREVIOUS_PAGE),
            ViewButton(style=discord.ButtonStyle.secondary, label='Next', custom_id=ViewButton.ID_NEXT_PAGE),
            ViewButton(style=discord.ButtonStyle.secondary, label='Last Page', custom_id=ViewButton.ID_GO_TO_LAST_PAGE),
            # delete_menu_button
        ]
        # add additional buttons
        buttons = [*nav_buttons, major_leagues_button, primary_leagues_button, all_leagues_button]
        menu.add_buttons(buttons)
        menu.add_pages(primary_leagues_embeds)  # landing pages
        await menu.start()

    # create a slash command to get the standings
    @app_commands.command(name='all-standings', description='Get the standings for all the major leagues')
    @app_commands.describe(timeframe='The timeframe/keyword to get the standings for. [required] Defaults to summer_2023.')
    async def all_standings(self, interaction: discord.Interaction, timeframe: str = 'summer_2023'):
        await interaction.response.defer()
        major_league_ids = self.lolesports.get_major_league_ids()
        message = self.lolesports.display_standings(major_league_ids, timeframe=timeframe, to_str=True)
        await interaction.followup.send(f"```{message}```")
    
    # create a slash command to get the standings of a specific league
    @app_commands.command(name='standings', description='Get the standings for a specific league')
    @app_commands.describe(league='The league to get the standings for. [required] Defaults to LCS.')
    async def standings(self, interaction: discord.Interaction, league: str = 'LCS'):
        # validate league
        try:
            keyword = lol.Region[league.upper()]
        except KeyError as e:
            print(f'**`ERROR:`** {type(e).__name__} - {e}')
            await interaction.response.send_message(f'Invalid league: {league}')
            return
        await interaction.response.defer()
        message = self.lolesports.display_standings([keyword.value], timeframe= "summer_2023", to_str=True)
        await interaction.followup.send(f"```{message}```")
        
        leagues = self.lolesports.leagues(is_sorted=True)
        if leagues is None:
            await interaction.response.send_message('Something went wrong.')
            return
        major_leagues = self.lolesports._get_sub_leagues(leagues)[0]
        major_regions_ids = self.lolesports.get_major_league_ids()
        timeframe = "summer_2023"

        tournaments = self.lolesports.tournaments(major_regions_ids)
        # get the tournaments for the timeframe
        matching_tournaments = self.lolesports.extract_tournaments_by_timeframe(tournaments, timeframe)
        # get the matching ids
        matching_ids = self.lolesports.extract_tournament_ids(matching_tournaments)
        # get the standings
        standings = self.lolesports.standings(matching_ids)
        # display the standings
        standings_results = []
        standings_titles = []
        for standing in standings:
            for standing_name, rankings in standing.items():
                standings_titles.append(f"{standing_name}")
                standding_str = ""
                for ranking in rankings:    # ranking within each league
                    ordinal = ranking['ordinal']
                    team = ranking['teams'][0] # only one team per slot
                    name = team['name']
                    code = team['code']
                    wins = team['record']['wins']
                    losses = team['record']['losses']
                    standding_str += f"\n{ordinal}. {name} ({code}): {wins}-{losses}"
                standings_results.append(standding_str)

        menu = ViewMenu(interaction, menu_type=ViewMenu.TypeEmbed)
        menu.add_page(discord.Embed(title="Seasonal Standings", color=discord.Color.dark_magenta()))

        menu.add_select(ViewSelect(title="Select from the following leagues", options={
            discord.SelectOption(label="LEC", emoji="<:lec:1148398301641703516>") : [
                Page(embed=discord.Embed(title=f"{standings_titles[0]} Regular Season Standings", description=standings_results[0], color=self.get_region_color("LEC")).set_thumbnail(url=major_leagues[1]['image'])),
            ],
            discord.SelectOption(label="LCK", emoji="<:lck:1148398360307433593>") : [
                Page(embed=discord.Embed(title=f"{standings_titles[1]} Regular Season Standings", description=standings_results[1], color=self.get_region_color("LCK")).set_thumbnail(url=major_leagues[2]['image'])),
            ],
            discord.SelectOption(label="LCS", emoji="<:lcs:1148398424950063196>") : [
                Page(embed=discord.Embed(title=f"{standings_titles[2]} Regular Season Standings", description=standings_results[2], color=self.get_region_color("LCS")).set_thumbnail(url=major_leagues[0]['image'])),
            ],            
            discord.SelectOption(label="LPL", emoji="<:lpl:1148398196683448380>") : [
                Page(embed=discord.Embed(title=f"{standings_titles[3]} Regular Season Standings", description=standings_results[3], color=self.get_region_color("LPL")).set_thumbnail(url=major_leagues[3]['image'])),
            ],
        }))

        menu.add_button(ViewButton.back())
        menu.add_button(ViewButton.next())
        await menu.start()

    # create a slash command to get the players and info for a specific team
    @app_commands.command(name='team', description='Get the players and info for a specific team')
    @app_commands.describe(team_code='The team code of the given team. [required] (ex. C9, edg, t1...)')
    async def team_info(self, interaction: discord.Interaction, team_code: str):
        # initialize the team object and get the teams mappping for the major leagues
        major_league_ids = self.lolesports.get_major_league_ids()
        major_teams = self.lolesports.get_teams_mapping_from_leagues(major_league_ids)
        await interaction.response.defer()
        team_slug = team_code.lower()   # lowercase the team code
        # check if the team code is valid
        if team_slug not in major_teams:
            await interaction.followup.send(f'Invalid team code: {team_code}')
            return
        team = self.lolesports.team(major_teams[team_slug])
        roster = self.lolesports.get_roster(team)
        league = team['homeLeague']['name']
        league_image = self.lolesports.get_image_url(league)
        embed = discord.Embed(title=f"{team['name']}",
            color=self.get_region_color(league),
            url=f"https://lolesports.com/team/{team['slug']}"
        )
        # set the author to the the region icon and region name
        embed.set_author(name=f"{league} Esports Team", 
                        icon_url= league_image)
        embed.add_field(name='Code', value=team['code'], inline=True)
        embed.add_field(name='Region', value=team['homeLeague']['region'], inline=True)
        embed.add_field(name='League', value=league, inline=True)
        embed.add_field(name='Players', value=len(roster), inline=True)
        embed.add_field(name='ID', value=team['id'], inline=True)
        embed.set_image(url=team['image'])
        embed.set_footer(text="Powered by Riot Games", icon_url='https://static.developer.riotgames.com/img/logo.png')
        # await interaction.followup.send(embed=embed)

        # create a select menu to display the players
        menu = ViewMenu(interaction, menu_type=ViewMenu.TypeEmbed, show_page_director=False)
        # menu.add_page(discord.Embed(title=f"{team['name']} Roster", color=self.get_region_color(league)))
        menu.add_page(embed)
        menu.add_select(ViewSelect(title="View full roster", options={
            # set the role to "fill" if its
            discord.SelectOption(label=f"{player['summonerName']} ({player['role'].title() if player['role'] != 'none' else 'Fill'})", emoji="{}".format(self.get_player_emoji(player['role']))) : [
                # embed for each player contains first + last name, summoner name, role as field
                Page(embed=discord.Embed(
                        title=player['fullname'],
                        color=self.get_region_color(league)
                        ).set_image(url=player['image'])
                        # set the author to the team icon and team name
                        .set_author(name=f"{team['name']} Roster", icon_url=team['image'])
                        .add_field(name='Name', value=f'{player["firstName"]} {player["lastName"]}', inline=True)
                        .add_field(name='Role', value=player['role'].title() if player['role'] != 'none' else 'Fill', inline=True)
                        # set the footer to the league
                        # .set_footer(text=f"{team['name']} | {league}", icon_url=team['image'])
                        .set_footer(text=f"{league} Esports Team", icon_url=league_image)

                )
            ] for player in roster
        }))
        menu.add_button(ViewButton.back())
        menu.add_button(ViewButton.next())
        await menu.start()

    
async def setup(client: commands.Bot) -> None:
    await client.add_cog(Query(client))
