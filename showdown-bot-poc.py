import discord
import BingoUtils
import configparser
import argparse
from discord.ext import commands
from discord import app_commands
from ApprovalRequest import ApprovalRequest

# Parse command-line args
parser = argparse.ArgumentParser(
  prog = 'Showdown Bot POC',
  description = 'POC for the UIM Showdown bot'
)
parser.add_argument('--test', action='store_true')
commandLineArgs = parser.parse_args()

# Set up bot object
intents = discord.Intents.default()
intents.message_content = True # Required for the commands extension to work
bot = commands.Bot(command_prefix='/', intents=intents)

# Register callback for all errors thrown out of command methods
@bot.tree.error
async def handleCommandErrors(ctx, error):
  await BingoUtils.handleCommandError(bot, ctx, error)

# Demo command for submitting KC for something
@bot.tree.command(name='test_submit_kc', description='Test command for submitting KC')
async def test_submit_kc(ctx: discord.Interaction, screenshot: discord.Attachment, kc: int):
  if(kc < 0):
    raise BingoUtils.BingoUserError('KC cannot be negative')
  if(kc == 999):
    x = 1 / 0 # To demo an unexpected error
  request = ApprovalRequest(ctx)
  await BingoUtils.requestApproval(bot, request)
  responseText = 'Request received:\n'
  responseText += str(request)
  await ctx.response.send_message(responseText)

# Utility command during testing to purge all bot-related channels
# This will only work if testing mode is enabled at the command line
@bot.tree.command(name='purge_all', description='Purge all bot-related channels, THIS IS DANGEROUS')
@app_commands.checks.has_role('Event staff')
async def purge_all(ctx: discord.Interaction):
  if(not commandLineArgs.test):
    raise BingoUtils.BingoUserError('Test mode is not enabled, rerun the bot with --test to enable test mode')
  submissionsChannel = bot.get_channel(BingoUtils.submissionsChannelId)
  approvalsChannel = bot.get_channel(BingoUtils.approvalsChannelId)
  errorsChannel = bot.get_channel(BingoUtils.errorsChannelId)
  await submissionsChannel.purge(limit=99999)
  await approvalsChannel.purge(limit=99999)
  await errorsChannel.purge(limit=99999)

@bot.event
async def on_ready():
  print(f'Logged in as {bot.user.name}')
  await bot.tree.sync() # This sets up the app commands in the Discord server based on what we register here
  print(f'Command tree synced!')

bot.run(BingoUtils.token)