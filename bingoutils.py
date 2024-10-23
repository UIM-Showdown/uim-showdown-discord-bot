import json
import configparser
import logging
from discord import ui, app_commands, Interaction
from buttons import ApproveButton, DenyButton
from approvalrequest import ApprovalRequest

# Load properties
config = configparser.ConfigParser()
config.read('config.ini')
bingoProperties = config['BingoProperties']
token = bingoProperties['token']
approvalsChannelId = int(bingoProperties['approvalsChannelId'])
errorsChannelId = int(bingoProperties['errorsChannelId'])
guildId = int(bingoProperties['guildId'])

# Load team info
teamInfo = []
with open('bingo-info/teams.json') as teamsFile:
  teamInfo = json.load(teamsFile)
discordUserTeams = {}
for team in teamInfo:
  for player in team['players']:
    discordUserTeams[player['tag']] = team['name']
teamSubmissionChannels = {}
for team in teamInfo:
  teamSubmissionChannels[team['name']] = team['submissionChannel']

# Load monster info
monsterInfo = []
with open('bingo-info/monsters.json') as monstersFile:
  monsterInfo = json.load(monstersFile)
monsters = []
for monster in monsterInfo:
  monsters.append(monster['name'])

# Load clog info
clogInfo = []
with open('bingo-info/collection-log-items.json') as clogFile:
  clogInfo = json.load(clogFile)
clogItems = []
for clogItem in clogInfo:
  clogItems.append(clogItem['name'])

# Autocomplete callbacks
async def monster_autocomplete(
  ctx: Interaction, 
  current: str
) -> list[app_commands.Choice[str]]:
  results = [
    app_commands.Choice(name = monster, value = monster)
    for monster in monsters if current.lower() in monster.lower()
  ]
  if(len(results) > 25):
    results = results[:25]
  return results

async def clog_autocomplete(
  ctx: Interaction, 
  current: str
) -> list[app_commands.Choice[str]]:
  results = [
    app_commands.Choice(name = item, value = item)
    for item in clogItems if current.lower() in item.lower()
  ]
  if(len(results) > 25):
    results = results[:25]
  return results


class BingoUserError(Exception):

  def __init__(self, message):
    self.message = message
    
  def __str__(self):
    return self.message

def getAttachmentsFromContext(ctx):
  return list(ctx.data['resolved']['attachments'].values())

async def handleCommandError(bot, ctx, error):
  if(isinstance(error.original, BingoUserError)):
    await ctx.response.send_message(f'Error: {str(error.original)}')
  else:
    logging.error('Error', exc_info=error)
    request = ApprovalRequest(ctx)
    channel = bot.get_channel(errorsChannelId)
    errorText = 'Unexpected error during processing of a command:\n'
    errorText += str(request) + '\n'
    errorText += f'Error: {str(error.original)}'
    await channel.send(errorText)
    await ctx.response.send_message('Unexpected error: The admins have been notified to review this error')

async def requestApproval(bot, request):
  channel = bot.get_channel(approvalsChannelId)
  requestText = 'New approval requested:\n'
  requestText += str(request)
  view = ui.View()
  view.add_item(ApproveButton(request, bot))
  view.add_item(DenyButton(request, bot))
  await bot.get_channel(approvalsChannelId).send(requestText, view=view)