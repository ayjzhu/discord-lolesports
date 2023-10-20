import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import os
import utils.lolesports as lol

load_dotenv()
CHANNEL_ID = os.getenv('CHANNEL_ID')

class BackgroundTasks(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.pending_msg = False
        self.live_event_id = None
        self.event_is_ready = False    # ready flag for invoking the upnext command
        self.counter = 1
        self.my_background_task.start()

    def cog_unload(self):
        self.my_background_task.cancel()

    # invoke the live command every 7 minute to check for live matches
    @tasks.loop(minutes=7.0)
    async def my_background_task(self):
        channel = self.bot.get_channel(int(CHANNEL_ID))
        # get the content of the last message
        last_messages = [message async for message in channel.history(limit=1)]
        ctx = await self.bot.get_context(last_messages[0])
        esports = lol.LolEsports(region='WORLDS')
        live_events = esports.live()
        if live_events: # if there is a live match
            # find the en-US stream parameter
            param = 'riotgames'
            for stream in live_events[0]["streams"]:
                if stream['locale'] == 'en-US' and stream['provider'] == 'twitch':
                    param = stream['parameter']

            # check if the live match is a new event
            if self.live_event_id != live_events[0]['id']:
                self.pending_msg = True
                self.live_event_id = live_events[0]['id'] # update the live event id
                if live_events[0]['type'] == 'show':
                    name = f'{live_events[0]["league"]["name"]} Pre{live_events[0]["type"]}'
                elif live_events[0]['type'] == 'match':
                    name = f'{live_events[0]["match"]["teams"][0]["code"]} vs {live_events[0]["match"]["teams"][1]["code"]}'

                await ctx.invoke(self.bot.get_command('live'))
                await self.bot.change_presence(activity=discord.Streaming(name=name, url=f"https://www.twitch.tv/{param}"))
        else:   # if there is no live match
            if self.pending_msg:    # if there was a live match and it is over
                self.live_event_id = None
                # check the upcoming eventlist until is it ready
                all_events = esports.eventlists(league_ids=esports.get_league_id())

                if not all_events:    # if there are no events
                    self.event_is_ready = True
                    print('There are no upcoming matches.')
                elif not self.event_is_ready:    # if there are events but not ready
                    events = esports.get_events_without_tbd(all_events)
                    if events:
                        await ctx.invoke(self.bot.get_command('upnext'))
                        self.event_is_ready = True
                
                # reset the flags once the event is ready and sent
                if self.event_is_ready: 
                    self.pending_msg = False
                    self.event_is_ready = False
                    
                # change the presence of activity to the default status
                await self.bot.change_presence(activity=discord.Activity(name='/schedule', type=discord.ActivityType.watching))
        print(f'Checking for live matches #{self.counter}...')
        self.counter += 1
    
    # cancel command to cancel the background task
    @commands.command(name='cancel', hidden = True)
    @commands.is_owner()
    async def cancel(self, ctx: commands.Context):
        if self.my_background_task.is_running():
            self.my_background_task.cancel()
            await ctx.send('Cancelled the background task!')
        else:
            await ctx.send('The background task is not running.')
    
    # start command to start the background task
    @commands.command(name='start', hidden = True)
    @commands.is_owner()
    async def start(self, ctx: commands.Context):
        if self.my_background_task.is_running():
            await ctx.send('The background task is already running.')
            return
        self.my_background_task.start()
        await ctx.send('Started the background task!')

    # stop command to stop the background task
    @commands.command(name='stop', hidden = True)
    @commands.is_owner()
    async def stop(self, ctx: commands.Context):
        if self.my_background_task.is_running():
            self.my_background_task.stop()
            await ctx.send('Stopped the background task!')
        else:
            await ctx.send('The background task is not running.')
    
    @commands.command(name='interval', hidden = True)
    @commands.is_owner()
    async def change_interval(self, ctx: commands.Context, seconds: int):
        self.my_background_task.change_interval(seconds=seconds)
        await ctx.send(f'Changed interval to {seconds} seconds.')

    @my_background_task.before_loop
    async def before_my_background_task(self):
        await self.bot.wait_until_ready()
    
    @my_background_task.after_loop
    async def after_my_background_task(self):
        if self.my_background_task.is_being_cancelled():
            print('Background task was cancelled.')
        else:
            print('Background task finished without error.')

    # is_running command to check if the background task is running
    @commands.command(name='isrunning', hidden = True)
    @commands.is_owner()
    async def is_running(self, ctx: commands.Context):
        if self.my_background_task.is_running():
            await ctx.send('The background task is running.')
        else:
            await ctx.send('The background task is not running.')

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BackgroundTasks(bot))
