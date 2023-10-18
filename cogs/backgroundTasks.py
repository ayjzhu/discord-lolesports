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
        self.my_background_task.start()
        self.is_live = False

    def cog_unload(self):
        self.my_background_task.cancel()

    # invoke the live command every 2 minute to check for live matches
    @tasks.loop(minutes=2.0)
    async def my_background_task(self):
        channel = self.bot.get_channel(int(CHANNEL_ID))
        # get the content of the last message
        last_messages = [message async for message in channel.history(limit=1)]
        ctx = await self.bot.get_context(last_messages[0])
        le = lol.LolEsports(region='WORLDS')
        # check whether there is a live match, invoke the live command only once
        # once live is over, invoke the upnext command and send message about the upcoming matches
        live_events = le.live()
        if live_events:
            if not self.is_live:
                self.is_live = True
                await ctx.invoke(self.bot.get_command('live'))
            else:
                # while live, check if the live match is a show or a match
                # if it is a match, invoke the live command again
                if live_events[0]['type'] == 'match':
                    await ctx.invoke(self.bot.get_command('live'))
        else:
            if self.is_live:
                self.is_live = False
                await ctx.invoke(self.bot.get_command('upnext'))
        print('Checking for live matches...')
    
    # cancel command to cancel the background task
    @commands.command(name='cancel')
    async def cancel(self, ctx: commands.Context):
        if self.my_background_task.is_running():
            self.my_background_task.cancel()
            await ctx.send('Cancelled the background task!')
        else:
            await ctx.send('The background task is not running.')
    
    # start command to start the background task
    @commands.command(name='start')
    async def start(self, ctx: commands.Context):
        if self.my_background_task.is_running():
            await ctx.send('The background task is already running.')
            return
        self.my_background_task.start()
        await ctx.send('Started the background task!')

    # stop command to stop the background task
    @commands.command(name='stop')
    async def stop(self, ctx: commands.Context):
        if self.my_background_task.is_running():
            self.my_background_task.stop()
            await ctx.send('Stopped the background task!')
        else:
            await ctx.send('The background task is not running.')
    
    @commands.command(name='interval')
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
    @commands.command(name='running')
    async def is_running(self, ctx: commands.Context):
        if self.my_background_task.is_running():
            await ctx.send('The background task is running.')
        else:
            await ctx.send('The background task is not running.')

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BackgroundTasks(bot))