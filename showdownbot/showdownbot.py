import json
import logging
import os
from discord.ext import commands
from discord import Intents, ui, app_commands, Interaction, Attachment
from typing import Literal
import showdownbot.errors as errors
import showdownbot.approvalrequest as approvalrequest
import showdownbot.buttons as buttons

class ShowdownBot:
    
  def __init__(self, commandLineArgs, configProperties):
      
    # Load config properties
    bingoProperties = configProperties['BingoProperties']
    self.token = bingoProperties['token']
    self.approvalsChannelId = int(bingoProperties['approvalsChannelId'])
    self.errorsChannelId = int(bingoProperties['errorsChannelId'])
    self.guildId = int(bingoProperties['guildId'])

    # Load team info
    teamInfo = []
    with open('bingo-info/teams.json') as teamsFile:
      teamInfo = json.load(teamsFile)
    self.discordUserTeams = {}
    for team in teamInfo:
      for player in team['players']:
        self.discordUserTeams[player['tag']] = team['name']
    self.teamSubmissionChannels = {}
    for team in teamInfo:
      self.teamSubmissionChannels[team['name']] = team['submissionChannel']

    # Load monster info
    monsterInfo = []
    with open('bingo-info/monsters.json') as monstersFile:
      monsterInfo = json.load(monstersFile)
    self.monsters = []
    for monster in monsterInfo:
      self.monsters.append(monster['name'])

    # Load clog info
    clogInfo = []
    with open('bingo-info/collection-log-items.json') as clogFile:
      clogInfo = json.load(clogFile)
    self.clogItems = []
    for clogItem in clogInfo:
      self.clogItems.append(clogItem['name'])

    # Set up bot object
    intents = Intents.default()
    intents.message_content = True # Required for the commands extension to work
    self.bot = commands.Bot(command_prefix='/', intents=intents)

    # Register callback for all errors thrown out of command methods
    @self.bot.tree.error
    async def handleCommandErrors(ctx, error):
      if(isinstance(error.original, errors.BingoUserError)):
        await ctx.response.send_message(f'Error: {str(error.original)}')
      else:
        logging.error('Error', exc_info=error)
        request = approvalrequest.ApprovalRequest(ctx)
        channel = self.bot.get_channel(self.errorsChannelId)
        errorText = 'Unexpected error during processing of a command:\n'
        errorText += str(request) + '\n'
        errorText += f'Error: {str(error.original)}'
        await channel.send(errorText)
        await ctx.response.send_message('Unexpected error: The admins have been notified to review this error')

    # Set up monster/clog autocomplete callbacks
    async def monster_autocomplete(
      ctx: Interaction,
      current: str
    ) -> list[app_commands.Choice[str]]:
      results = [
        app_commands.Choice(name = monster, value = monster)
        for monster in self.monsters if current.lower() in monster.lower()
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
        for item in self.clogItems if current.lower() in item.lower()
      ]
      if(len(results) > 25):
        results = results[:25]
      return results

    # Register commands
    @self.bot.tree.command(name='submit_monster_killcount', description='Submit a monster killcount for the bingo!')
    @app_commands.autocomplete(monster=monster_autocomplete)
    async def submit_monster_killcount(ctx: Interaction, screenshot: Attachment, monster: str, kc: int):
      if(kc < 0):
        raise errors.BingoUserError('KC cannot be negative')
      if(monster not in self.monsters):
        raise errors.BingoUserError('Invalid monster name (make sure to click on the autocomplete option)')
      request = approvalrequest.ApprovalRequest(ctx, f'{kc} KC of {monster}')
      await self.requestApproval(request)
      responseText = 'Request received:\n'
      responseText += str(request)
      await ctx.response.send_message(responseText)

    @self.bot.tree.command(name='submit_collection_log', description='Submit a collection log item for the bingo! (Make sure the drop is in the screenshot)')
    @app_commands.autocomplete(item=clog_autocomplete)
    async def submit_collection_log(ctx: Interaction, screenshot: Attachment, item: str):
      if(item not in self.clogItems):
        raise errors.BingoUserError('Invalid item name (make sure to click on the autocomplete option)')
      request = approvalrequest.ApprovalRequest(ctx, f'Collection log item "{item}"')
      await self.requestApproval(request)
      responseText = 'Request received:\n'
      responseText += str(request)
      await ctx.response.send_message(responseText)

    @self.bot.tree.command(name='submit_pest_control', description='Submit your pest control games for the bingo! (All difficulties added together)')
    async def submit_pest_control(ctx: Interaction, screenshot: Attachment, total_games: int):
      if(total_games < 0):
        raise errors.BingoUserError('Total games cannot be negative')
      request = approvalrequest.ApprovalRequest(ctx, f'{total_games} games of pest control')
      await self.requestApproval(request)
      responseText = 'Request received:\n'
      responseText += str(request)
      await ctx.response.send_message(responseText)

    @self.bot.tree.command(name='submit_lms', description='Submit your LMS kills for the bingo!')
    async def submit_lms(ctx: Interaction, screenshot: Attachment, kills: int):
      if(kills < 0):
        raise errors.BingoUserError('Kills cannot be negative')
      request = approvalrequest.ApprovalRequest(ctx, f'{kills} kills in LMS')
      await self.requestApproval(request)
      responseText = 'Request received:\n'
      responseText += str(request)
      await ctx.response.send_message(responseText)

    @self.bot.tree.command(name='submit_mta', description='Submit your MTA points for the bingo!')
    async def submit_mta(ctx: Interaction, screenshot: Attachment, alchemy_points: int, graveyard_points: int, enchanting_points: int, telekinetic_points: int):
      if(alchemy_points < 0 or graveyard_points < 0 or enchanting_points < 0 or telekinetic_points < 0):
        raise errors.BingoUserError('Points cannot be negative')
      request = approvalrequest.ApprovalRequest(ctx, f'{alchemy_points}/{graveyard_points}/{enchanting_points}/{telekinetic_points} MTA points')
      await self.requestApproval(request)
      responseText = 'Request received:\n'
      responseText += str(request)
      await ctx.response.send_message(responseText)

    @self.bot.tree.command(name='submit_tithe_farm', description='Submit your tithe farm points for the bingo!')
    async def submit_tithe_farm(ctx: Interaction, screenshot: Attachment, points: int):
      if(points < 0):
        raise errors.BingoUserError('Points cannot be negative')
      request = approvalrequest.ApprovalRequest(ctx, f'{points} tithe farm points')
      await self.requestApproval(request)
      responseText = 'Request received:\n'
      responseText += str(request)
      await ctx.response.send_message(responseText)

    @self.bot.tree.command(name='submit_farming_contracts', description='Submit your farming contracts for the bingo!')
    async def submit_farming_contracts(ctx: Interaction, screenshot: Attachment, contracts: int):
      if(contracts < 0):
        raise errors.BingoUserError('Contracts cannot be negative')
      request = approvalrequest.ApprovalRequest(ctx, f'{contracts} farming contracts')
      await self.requestApproval(request)
      responseText = 'Request received:\n'
      responseText += str(request)
      await ctx.response.send_message(responseText)

    @self.bot.tree.command(name='submit_barbarian_assault', description='Submit your BA points for the bingo! (Make sure to check the optional arguments)')
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
          raise errors.BingoUserError('BA arguments cannot be negative')
      request = approvalrequest.ApprovalRequest(ctx, 'BA points')
      await self.requestApproval(request)
      responseText = 'Request received:\n'
      responseText += str(request)
      await ctx.response.send_message(responseText)

    @self.bot.tree.command(name='submit_challenge', description='Submit your challenge times for the bingo! (Make sure to have precise timing enabled.)')
    async def submit_challenge(ctx: Interaction, screenshot: Attachment, minutes: int, seconds: int, tenths_of_seconds: int, challenge: Literal['Theatre of Blood', 'Tombs of Amascut', 'Sepulchre Relay', 'Barbarian Assault']):
      if(minutes < 0 or seconds < 0 or tenths_of_seconds < 0):
        raise errors.BingoUserError('Times cannot be negative')
      if(tenths_of_seconds > 9):
        raise errors.BingoUserError('tenths_of_seconds cannot be greater than 9')
      request = approvalrequest.ApprovalRequest(ctx, "{0} time of {1:0>2}:{2:0>2}.{3}".format(challenge, minutes, seconds, tenths_of_seconds))
      await self.requestApproval(request)
      responseText = 'Request received:\n'
      responseText += str(request)
      await ctx.response.send_message(responseText)

    @self.bot.event
    async def on_ready():
      print(f'Logged in as {self.bot.user.name}')
      if(commandLineArgs.updatecommands):
        print('Updating commands...')
        synced = await self.bot.tree.sync()
        print(f'Synced {len(synced)} commands.')
        os._exit(0)

  def getAttachmentsFromContext(self, ctx):
    return list(ctx.data['resolved']['attachments'].values())

  async def requestApproval(self, request):
    channel = self.bot.get_channel(self.approvalsChannelId)
    requestText = 'New approval requested:\n'
    requestText += str(request)
    view = ui.View()
    view.add_item(buttons.ApproveButton(request, self))
    view.add_item(buttons.DenyButton(request, self))
    await self.bot.get_channel(self.approvalsChannelId).send(requestText, view=view)
  
  def start(self):
    self.bot.run(self.token)