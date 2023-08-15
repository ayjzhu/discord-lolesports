import discord
from discord.ext import commands
from discord import app_commands
import utils.lolesports as lolesports
import pandas as pd
from datetime import datetime, timezone, timedelta
import pytz

class Query(commands.Cog):
    def __init__(self, client: commands.Bot) -> None:
        self.client = client
        self.TIMEZONE = 'US/Pacific'

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
        result = lolesports.get_live()
        await interaction.response.send_message(result)
    
    @app_commands.command(name='schedule', description='Get the schedule of upcoming events')
    @app_commands.describe(region='The region to get the schedule for. [required] Defaults to LEC.')
    async def schedule(self, interaction: discord.Interaction, region: str = 'LEC'):
        print(region)
        # validate region
        try:
            keyword = lolesports.Region[region.upper()]
        except KeyError as e:
            print(f'**`ERROR:`** {type(e).__name__} - {e}')
            await interaction.response.send_message(f'Invalid region: {region}')
            return

        data = lolesports.get_schedule(keyword)
        # create dataframe
        df = pd.DataFrame(data['data']['schedule']['events'])
        unstarted_df = df[df['state'] == 'unstarted'].reset_index(drop=True)
        embed = discord.Embed(title=f"Schedule for \"{keyword.name}\":", 
                        description = f"Upcoming matches for the {unstarted_df['league'].iloc[0]['name']}",
                        color = discord.Color.teal(),
                        # set the timestamp to the current time in PST time
                        timestamp = datetime.now(timezone(timedelta(hours=-7))))
        embed.set_footer(text="Time shown in {}".format(self.TIMEZONE))

        for index, row in unstarted_df.iterrows():
            teams = [(team['name'], team['code']) for team in row['match']['teams']]
            teams_str = ' vs '.join([f'{name}({code})' for name, code in teams])
            embed.add_field(name='Teams', value=teams_str, inline=False)

            embed.add_field(name='Start time',
                            value= f"{self.convert_timezone(row['startTime'], self.TIMEZONE)} ({row['state']})", 
                            inline=False)
            embed.add_field(name='League', value=row['league']['name'], inline=True)
            embed.add_field(name='Stage', value=row['blockName'], inline=True)
            # add a strategy field with the format of bestOf 5
            embed.add_field(name='format', value=f"{row['match']['strategy']['type']} {row['match']['strategy']['count']}", inline=True)
            
            # only add this field if its not the last row
            # if index != len(unstarted_df) - 1:
            #     embed.add_field(name="\uFEFF", value="Next up", inline=False)
        await interaction.response.send_message(content='Upcoming games', embed=embed)
    
async def setup(client: commands.Bot) -> None:
    await client.add_cog(Query(client))
