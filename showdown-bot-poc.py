import discord
import BingoUtils
import configparser
import argparse
from discord.ext import commands
from discord import app_commands
from ApprovalRequest import ApprovalRequest
from typing import Literal

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

# Register commands
@bot.tree.command(name='submit_monster_killcount', description='Submit a monster killcount for the bingo!')
@app_commands.autocomplete(monster=BingoUtils.monster_autocomplete)
async def submit_monster_killcount(ctx: discord.Interaction, screenshot: discord.Attachment, monster: str, kc: int):
  if(kc < 0):
    raise BingoUtils.BingoUserError('KC cannot be negative')
  if(monster not in BingoUtils.monsters):
    raise BingoUtils.BingoUserError('Invalid monster name (make sure to click on the autocomplete option)')
  request = ApprovalRequest(ctx, f'{kc} KC of {monster}')
  await BingoUtils.requestApproval(bot, request)
  responseText = 'Request received:\n'
  responseText += str(request)
  await ctx.response.send_message(responseText)

@bot.tree.command(name='submit_collection_log', description='Submit a collection log item for the bingo! (Make sure the drop is in the screenshot)')
@app_commands.autocomplete(item=BingoUtils.clog_autocomplete)
async def submit_collection_log(ctx: discord.Interaction, screenshot: discord.Attachment, item: str):
  if(item not in BingoUtils.clogItems):
    raise BingoUtils.BingoUserError('Invalid item name (make sure to click on the autocomplete option)')
  request = ApprovalRequest(ctx, f'Collection log item "{item}"')
  await BingoUtils.requestApproval(bot, request)
  responseText = 'Request received:\n'
  responseText += str(request)
  await ctx.response.send_message(responseText)

@bot.tree.command(name='submit_pest_control', description='Submit your pest control games for the bingo! (Make sure to add up your games across all difficulties)')
async def submit_pest_control(ctx: discord.Interaction, screenshot: discord.Attachment, totalGames: int):
  if(totalGames < 0):
    raise BingoUtils.BingoUserError('Total games cannot be negative')
  request = ApprovalRequest(ctx, f'{totalGames} games of pest control')
  await BingoUtils.requestApproval(bot, request)
  responseText = 'Request received:\n'
  responseText += str(request)
  await ctx.response.send_message(responseText)

@bot.tree.command(name='submit_lms', description='Submit your LMS kills for the bingo!')
async def submit_lms(ctx: discord.Interaction, screenshot: discord.Attachment, kills: int):
  if(kills < 0):
    raise BingoUtils.BingoUserError('Kills cannot be negative')
  request = ApprovalRequest(ctx, f'{kills} kills in LMS')
  await BingoUtils.requestApproval(bot, request)
  responseText = 'Request received:\n'
  responseText += str(request)
  await ctx.response.send_message(responseText)

@bot.tree.command(name='submit_mta', description='Submit your MTA points for the bingo!')
async def submit_mta(ctx: discord.Interaction, screenshot: discord.Attachment, alchemyPoints: int, graveyardPoints: int, enchantingPoints: int, telekineticPoints: int):
  if(alchemyPoints < 0 or graveyardPoints < 0 or enchantingPoints < 0 or telekineticPoints < 0):
    raise BingoUtils.BingoUserError('Points cannot be negative')
  request = ApprovalRequest(ctx, f'{alchemyPoints}/{graveyardPoints}/{enchantingPoints}/{telekineticPoints} MTA points')
  await BingoUtils.requestApproval(bot, request)
  responseText = 'Request received:\n'
  responseText += str(request)
  await ctx.response.send_message(responseText)

@bot.tree.command(name='submit_tithe_farm', description='Submit your tithe farm points for the bingo!')
async def submit_tithe_farm(ctx: discord.Interaction, screenshot: discord.Attachment, points: int):
  if(points < 0):
    raise BingoUtils.BingoUserError('Points cannot be negative')
  request = ApprovalRequest(ctx, f'{points} tithe farm points')
  await BingoUtils.requestApproval(bot, request)
  responseText = 'Request received:\n'
  responseText += str(request)
  await ctx.response.send_message(responseText)

@bot.tree.command(name='submit_farming_contracts', description='Submit your farming contracts for the bingo!')
async def submit_farming_contracts(ctx: discord.Interaction, screenshot: discord.Attachment, contracts: int):
  if(contracts < 0):
    raise BingoUtils.BingoUserError('Contracts cannot be negative')
  request = ApprovalRequest(ctx, f'{contracts} farming contracts')
  await BingoUtils.requestApproval(bot, request)
  responseText = 'Request received:\n'
  responseText += str(request)
  await ctx.response.send_message(responseText)

@bot.tree.command(name='submit_barbarian_assault', description='Submit your BA points for the bingo! (Make sure you enter any arguments that are listed as "optional" if they are not 0)')
async def submit_barbarian_assault(ctx: discord.Interaction, clogScreenshot: discord.Attachment, blackboardScreenshot: discord.Attachment,
  highGambles = 0,
  attackerPoints = 0,
  defenderPoints = 0,
  collectorPoints = 0,
  healerPoints = 0,
  attackerLevel = 0,
  defenderLevel = 0,
  collectorLevel = 0,
  healerLevel = 0,
  hats = 0,
  torso = 0,
  skirt = 0,
  gloves = 0,
  boots = 0
):
  argValues = [locals()[param.name] for param in inspect.signature(submit_farming_contracts).parameters.values()]
  for argValue in argValues:
    if(isinstance(argValue, int) and argValue < 0):
      raise BingoUtils.BingoUserError('BA arguments cannot be negative')
  request = ApprovalRequest(ctx, 'BA points')
  await BingoUtils.requestApproval(bot, request)
  responseText = 'Request received:\n'
  responseText += str(request)
  await ctx.response.send_message(responseText)

@bot.tree.command(name='submit_challenge', description='Submit your challenge times for the bingo! (Make sure to have precise timing enabled.)')
async def submit_challenge(ctx: discord.Interaction, screenshot: discord.Attachment, minutes: int, seconds: int, tenthsOfSeconds: int, challenge: Literal['Theatre of Blood', 'Tombs of Amascut', 'Sepulchre Relay', 'Barbarian Assault']):
  if(minutes < 0 or seconds < 0 or tenthsOfSeconds < 0):
    raise BingoUtils.BingoUserError('Times cannot be negative')
  request = ApprovalRequest(ctx, f'{challenge} time of {minutes}:{seconds}.{tenthsOfSeconds}')
  await BingoUtils.requestApproval(bot, request)
  responseText = 'Request received:\n'
  responseText += str(request)
  await ctx.response.send_message(responseText)

@bot.event
async def on_ready():
  print(f'Logged in as {bot.user.name}')
  await bot.tree.sync() # This sets up the app commands in the Discord server based on what we register here
  print(f'Command tree synced!')

bot.run(BingoUtils.token)