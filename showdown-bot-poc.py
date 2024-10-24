import argparse
import bingoutils
import os
from discord.ext import commands
from discord import app_commands, Intents, Interaction, Attachment
from typing import Literal, Optional
from approvalrequest import ApprovalRequest

# Parse command-line args
parser = argparse.ArgumentParser(
  prog = 'Showdown Bot POC',
  description = 'POC for the UIM Showdown bot'
)
parser.add_argument('--updatecommands', action='store_true')
commandLineArgs = parser.parse_args()

# Set up bot object
intents = Intents.default()
intents.message_content = True # Required for the commands extension to work
bot = commands.Bot(command_prefix='/', intents=intents)

# Register callback for all errors thrown out of command methods
@bot.tree.error
async def handleCommandErrors(ctx, error):
  await bingoutils.handleCommandError(bot, ctx, error)

# Register commands
@bot.tree.command(name='submit_monster_killcount', description='Submit a monster killcount for the bingo!')
@app_commands.autocomplete(monster=bingoutils.monster_autocomplete)
async def submit_monster_killcount(ctx: Interaction, screenshot: Attachment, monster: str, kc: int):
  if(kc < 0):
    raise bingoutils.BingoUserError('KC cannot be negative')
  if(monster not in bingoutils.monsters):
    raise bingoutils.BingoUserError('Invalid monster name (make sure to click on the autocomplete option)')
  request = ApprovalRequest(ctx, f'{kc} KC of {monster}')
  await bingoutils.requestApproval(bot, request)
  responseText = 'Request received:\n'
  responseText += str(request)
  await ctx.response.send_message(responseText)

@bot.tree.command(name='submit_collection_log', description='Submit a collection log item for the bingo! (Make sure the drop is in the screenshot)')
@app_commands.autocomplete(item=bingoutils.clog_autocomplete)
async def submit_collection_log(ctx: Interaction, screenshot: Attachment, item: str):
  if(item not in bingoutils.clogItems):
    raise bingoutils.BingoUserError('Invalid item name (make sure to click on the autocomplete option)')
  request = ApprovalRequest(ctx, f'Collection log item "{item}"')
  await bingoutils.requestApproval(bot, request)
  responseText = 'Request received:\n'
  responseText += str(request)
  await ctx.response.send_message(responseText)

@bot.tree.command(name='submit_pest_control', description='Submit your pest control games for the bingo! (All difficulties added together)')
async def submit_pest_control(ctx: Interaction, screenshot: Attachment, total_games: int):
  if(total_games < 0):
    raise bingoutils.BingoUserError('Total games cannot be negative')
  request = ApprovalRequest(ctx, f'{total_games} games of pest control')
  await bingoutils.requestApproval(bot, request)
  responseText = 'Request received:\n'
  responseText += str(request)
  await ctx.response.send_message(responseText)

@bot.tree.command(name='submit_lms', description='Submit your LMS kills for the bingo!')
async def submit_lms(ctx: Interaction, screenshot: Attachment, kills: int):
  if(kills < 0):
    raise bingoutils.BingoUserError('Kills cannot be negative')
  request = ApprovalRequest(ctx, f'{kills} kills in LMS')
  await bingoutils.requestApproval(bot, request)
  responseText = 'Request received:\n'
  responseText += str(request)
  await ctx.response.send_message(responseText)

@bot.tree.command(name='submit_mta', description='Submit your MTA points for the bingo!')
async def submit_mta(ctx: Interaction, screenshot: Attachment, alchemy_points: int, graveyard_points: int, enchanting_points: int, telekinetic_points: int):
  if(alchemy_points < 0 or graveyard_points < 0 or enchanting_points < 0 or telekinetic_points < 0):
    raise bingoutils.BingoUserError('Points cannot be negative')
  request = ApprovalRequest(ctx, f'{alchemy_points}/{graveyard_points}/{enchanting_points}/{telekinetic_points} MTA points')
  await bingoutils.requestApproval(bot, request)
  responseText = 'Request received:\n'
  responseText += str(request)
  await ctx.response.send_message(responseText)

@bot.tree.command(name='submit_tithe_farm', description='Submit your tithe farm points for the bingo!')
async def submit_tithe_farm(ctx: Interaction, screenshot: Attachment, points: int):
  if(points < 0):
    raise bingoutils.BingoUserError('Points cannot be negative')
  request = ApprovalRequest(ctx, f'{points} tithe farm points')
  await bingoutils.requestApproval(bot, request)
  responseText = 'Request received:\n'
  responseText += str(request)
  await ctx.response.send_message(responseText)

@bot.tree.command(name='submit_farming_contracts', description='Submit your farming contracts for the bingo!')
async def submit_farming_contracts(ctx: Interaction, screenshot: Attachment, contracts: int):
  if(contracts < 0):
    raise bingoutils.BingoUserError('Contracts cannot be negative')
  request = ApprovalRequest(ctx, f'{contracts} farming contracts')
  await bingoutils.requestApproval(bot, request)
  responseText = 'Request received:\n'
  responseText += str(request)
  await ctx.response.send_message(responseText)

@bot.tree.command(name='submit_barbarian_assault', description='Submit your BA points for the bingo! (Make sure to check the optional arguments)')
async def submit_barbarian_assault(ctx: Interaction, clog_screenshot: Attachment, blackboard_screenshot: Attachment,
  high_gambles: int = 0,
  attacker_points: int = 0,
  defender_points: int = 0,
  collector_points: int = 0,
  healer_points: int = 0,
  attacker_level: int = 0,
  defender_level: int = 0,
  collector_level: int = 0,
  healer_level: int = 0,
  hats: int = 0,
  torso: int = 0,
  skirt: int = 0,
  gloves: int = 0,
  boots: int = 0
):
  argValues = [locals()[param.name] for param in submit_barbarian_assault.parameters]
  for argValue in argValues:
    if(isinstance(argValue, int) and argValue < 0):
      raise bingoutils.BingoUserError('BA arguments cannot be negative')
  request = ApprovalRequest(ctx, 'BA points')
  await bingoutils.requestApproval(bot, request)
  responseText = 'Request received:\n'
  responseText += str(request)
  await ctx.response.send_message(responseText)

@bot.tree.command(name='submit_challenge', description='Submit your challenge times for the bingo! (Make sure to have precise timing enabled.)')
async def submit_challenge(ctx: Interaction, screenshot: Attachment, minutes: int, seconds: int, tenths_of_seconds: int, challenge: Literal['Theatre of Blood', 'Tombs of Amascut', 'Sepulchre Relay', 'Barbarian Assault']):
  if(minutes < 0 or seconds < 0 or tenths_of_seconds < 0):
    raise bingoutils.BingoUserError('Times cannot be negative')
  request = ApprovalRequest(ctx, f'{challenge} time of {minutes}:{seconds}.{tenths_of_seconds}')
  await bingoutils.requestApproval(bot, request)
  responseText = 'Request received:\n'
  responseText += str(request)
  await ctx.response.send_message(responseText)

@bot.event
async def on_ready():
  print(f'Logged in as {bot.user.name}')
  if(commandLineArgs.updatecommands):
    print('Updating commands...')
    synced = await bot.tree.sync()
    print(f'Synced {len(synced)} commands.')
    os._exit(0)

bot.run(bingoutils.token)
