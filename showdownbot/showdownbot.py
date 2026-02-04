import logging
import os
from datetime import datetime
from discord.ext import commands
from discord import utils, Intents, ui, app_commands, Interaction, Attachment, Colour, CategoryChannel, TextChannel, VoiceChannel, PermissionOverwrite, InteractionType, ButtonStyle
from typing import Optional
import showdownbot.errors as errors
import showdownbot.submissions as submissions
from showdownbot.backendclient import BackendClient

log = logging.getLogger('showdown')

'''
A wrapper for discord.py's "Bot" class that handles most of the logic for the competition
'''
class ShowdownBot:
  
  '''
  Initializes instance variables and calls instance methods to register callbacks to the bot
  '''
  def __init__(self, commandLineArgs, configProperties):
      
    # Load config properties
    competitionProperties = configProperties['CompetitionProperties']
    self.token = competitionProperties['token']
    self.submissionQueueChannelId = int(competitionProperties['submissionQueueChannelId'])
    self.submissionLogChannelId = int(competitionProperties['submissionLogChannelId'])
    self.errorsChannelId = int(competitionProperties['errorsChannelId'])
    self.guildId = int(competitionProperties['guildId'])
    self.backendUrl = competitionProperties['backendUrl']
    self.backendClient = BackendClient(self.backendUrl)

    # Set up bot object
    intents = Intents.default()
    intents.members = True # Required for role assignments to work
    intents.message_content = True # Required for the commands extension to work
    self.bot = commands.Bot(command_prefix='/', intents=intents)

    self.registerErrorHandler()
    self.registerReadyHook(commandLineArgs)
    self.registerCommands()
    self.registerInteractionHook()

    self.discordUserTeams = {}
    self.discordUserRSNs = {}
    self.teamSubmissionChannels = {}
    self.competitionInfo = {}
    self.players = []
    self.discordNames = []
    self.teams = []
    self.tiles = []
    self.contributionMethods = []
    self.monsters = []
    self.itemDrops = []
    self.clogItems = []
    self.records = []
    self.challenges = []
    self.competitionLoaded = False

  '''
  Helper method to check if the event is currently in progress
  '''
  def eventInProgress():
    now = datetime.now().astimezone()
    startDatetime = datetime.fromisoformat(self.competitionInfo['startDatetime'])
    endDatetime = datetime.fromisoformat(self.competitionInfo['endDatetime'])
    return now > startDatetime and now < endDatetime

  '''
  Helper method to make sure the person submitting the command is a competitor and is in the right channel
  '''
  async def submissionPreChecks(self, interaction):
    if(not self.competitionLoaded):
      raise errors.UserError('The event is not currently in progress')
    if(not self.eventInProgress()):
      raise errors.UserError('The event is not currently in progress')
    if(interaction.user.name not in self.discordUserRSNs):
      raise errors.UserError(f'{interaction.user.display_name} is not a registered player in this event')
    team = self.discordUserTeams[interaction.user.name]
    teamChannel = self.teamSubmissionChannels[team]
    if(teamChannel is None or interaction.channel != teamChannel):
      raise errors.UserError("Please only submit commands in your team's bot submission channel")
    
  async def staffCheck(self, interaction):
    isStaff = False
    staffRole = utils.find(lambda r: r.name == 'Event staff', self.bot.get_guild(self.guildId).roles)
    if(staffRole not in interaction.user.roles):
      raise errors.UserError('This command is only for event staff usage')
    
  '''
  Helper method to raise a UserError if the user that spawned the interaction does not have the Screenshot Approver role (and therefore should not be able to approve/deny submissions)
  '''
  async def checkForScreenshotApprover(self, interaction):
    roles = interaction.user.roles
    hasApproverRole = False
    for role in roles:
      if(role.name == 'Screenshot Approver'):
        hasApproverRole = True
        break
    if(not hasApproverRole):
      raise errors.UserError('User is not a screenshot approver')

  '''
  Helper method to send a message to the error channel to report an error, and respond to the original interaction to notify the user that the error has been reported
  '''
  async def sendErrorMessageToErrorChannel(self, interaction, submission, error):
    errorText = 'Unexpected error occurred:\n'
    if(submission):
      errorText += 'Processing submission: \n' + str(submission) + '\n'
    if(hasattr(error, 'original')):
      errorText += f'Error: {str(error.original)}'
    else:
      errorText += f'Error: {str(error)}'
    channel = self.bot.get_channel(self.errorsChannelId)
    await channel.send(errorText)
    if(interaction):
      await interaction.response.send_message('Unexpected error: The admins have been notified to review this error')

  '''
  Helper method to send a message to the submission queue to request approval for a submission
  '''
  async def sendSubmissionToQueue(self, submission):
    log.info('Submission created:\n' + str(submission))
    submissionText = '# New submission:\n'
    submissionText += str(submission)
    view = ui.View()
    view.add_item(ui.Button(style=ButtonStyle.success, custom_id='approve', label='Approve'))
    view.add_item(ui.Button(style=ButtonStyle.danger, custom_id='deny', label='Deny'))
    await self.bot.get_channel(self.submissionQueueChannelId).send(submissionText, view=view)
  
  '''
  Populates instance variables coming from the backend
  '''
  async def loadCompetitionInfo(self):
    log.info('Loading competition info...')
    try:
      guild = self.bot.get_guild(self.guildId)
      channels = guild.channels
      self.competitionInfo = self.backendClient.getCompetitionInfo()
      self.tiles = self.backendClient.getTiles()
      self.contributionMethods = self.backendClient.getContributionMethods()
      self.contributionMethodNames = []
      for method in self.contributionMethods:
        self.contributionMethodNames.append(method['name'])
      # Create purchase options
      self.purchaseItems = []
      for method in self.contributionMethods:
        for item in method['purchaseItems']:
          self.purchaseItems.append({
            'name': item['name'],
            'cost': item['cost'],
            'methodName': method['name']
          })
      self.purchaseItemNames = []
      for item in self.purchaseItems:
        if(item['name'] not in self.purchaseItemNames):
          self.purchaseItemNames.append(item['name'])
      self.monsters = self.backendClient.getContributionMethodNamesByType('SUBMISSION_KC')
      self.itemDrops = self.backendClient.getContributionMethodNamesByType('SUBMISSION_ITEM_DROP')
      self.clogItems = self.backendClient.getCollectionLogItems()
      self.records = self.backendClient.getRecords()
      self.challenges = self.backendClient.getChallenges()

      teamRosters = self.backendClient.getTeamRosters()
      teamInfo = self.backendClient.getTeamInfo()
      self.players = []
      self.discordNames = []
      self.teams = []
      for teamName in teamRosters:
        self.teams.append(teamName)
        teamTag = teamInfo[teamName]['tag']
        teamBotSubmissionChannelName = teamTag.lower() + '-bot-submissions'
        for channel in channels:
          if(channel.name == teamBotSubmissionChannelName):
            self.teamSubmissionChannels[teamName] = channel
        if(teamName not in self.teamSubmissionChannels):
          self.teamSubmissionChannels[teamName] = None
        for player in teamRosters[teamName]:
          self.players.append(player['rsn'])
          self.discordNames.append(player['discordName'])
          self.discordUserRSNs[player['discordName'].lower()] = player['rsn']
          self.discordUserTeams[player['discordName'].lower()] = teamName

      self.players.sort()
      self.discordNames.sort()
      self.teams.sort()
      self.tiles.sort()
      self.contributionMethodNames.sort()
      self.monsters.sort()
      self.itemDrops.sort()
      self.clogItems.sort()
      self.purchaseItemNames.sort()

      self.competitionLoaded = True
      log.info('Competition info loaded!')
    except Exception as e: # The backend is likely not running, but we can still silently succeed without actually changing anything
      self.discordUserTeams = {}
      self.discordUserRSNs = {}
      self.teamSubmissionChannels = {}
      self.competitionInfo = {}
      self.players = []
      self.discordNames = []
      self.teams = []
      self.tiles = []
      self.contributionMethods = []
      self.monsters = []
      self.itemDrops = []
      self.clogItems = []
      self.records = []
      self.challenges = []
      self.competitionLoaded = False
      log.warning('Failed to load competition info.', e)
  
  '''
  Registers slash command callbacks to the bot
  '''
  def registerCommands(self):

    log.info('Registering commands...')
    # Set up autocomplete callbacks
    async def tile_autocomplete(
      interaction: Interaction,
      current: str
    ) -> list[app_commands.Choice[str]]:
      results = [
        app_commands.Choice(name = tile, value = tile)
        for tile in self.tiles if current.lower() in tile.lower()
      ]
      if(len(results) > 25):
        results = results[:25]
      return results

    async def team_autocomplete(
      interaction: Interaction,
      current: str
    ) -> list[app_commands.Choice[str]]:
      results = [
        app_commands.Choice(name = team, value = team)
        for team in self.teams if current.lower() in team.lower()
      ]
      if(len(results) > 25):
        results = results[:25]
      return results
    
    async def player_autocomplete(
      interaction: Interaction,
      current: str
    ) -> list[app_commands.Choice[str]]:
      results = [
        app_commands.Choice(name = player, value = player)
        for player in self.players if current.lower() in player.lower()
      ]
      if(len(results) > 25):
        results = results[:25]
      return results
    
    async def discord_name_autocomplete(
      interaction: Interaction,
      current: str
    ) -> list[app_commands.Choice[str]]:
      results = [
        app_commands.Choice(name = discordName, value = discordName)
        for discordName in self.discordNames if current.lower() in discordName.lower()
      ]
      if(len(results) > 25):
        results = results[:25]
      return results
    
    async def method_autocomplete(
      interaction: Interaction,
      current: str
    ) -> list[app_commands.Choice[str]]:
      results = [
        app_commands.Choice(name = method, value = method)
        for method in self.contributionMethodNames if current.lower() in method.lower()
      ]
      if(len(results) > 25):
        results = results[:25]
      return results
    
    async def monster_autocomplete(
      interaction: Interaction,
      current: str
    ) -> list[app_commands.Choice[str]]:
      results = [
        app_commands.Choice(name = monster, value = monster)
        for monster in self.monsters if current.lower() in monster.lower()
      ]
      if(len(results) > 25):
        results = results[:25]
      return results
    
    async def item_drop_autocomplete(
      interaction: Interaction,
      current: str
    ) -> list[app_commands.Choice[str]]:
      results = [
        app_commands.Choice(name = drop, value = drop)
        for drop in self.itemDrops if current.lower() in drop.lower()
      ]
      if(len(results) > 25):
        results = results[:25]
      return results
    
    async def purchase_item_autocomplete(
        interaction: Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
      results = [
        app_commands.Choice(name = itemName, value = itemName)
        for itemName in self.purchaseItemNames if current.lower() in itemName.lower()
      ]
      if(len(results) > 25):
        results = results[:25]
      return results

    async def clog_autocomplete(
      interaction: Interaction,
      current: str
    ) -> list[app_commands.Choice[str]]:
      results = [
        app_commands.Choice(name = item, value = item)
        for item in self.clogItems if current.lower() in item.lower()
      ]
      if(len(results) > 25):
        results = results[:25]
      return results
    
    async def record_autocomplete(
      interaction: Interaction,
      current: str
    ) -> list[app_commands.Choice[str]]:
      results = [
        app_commands.Choice(name = record['nameAndHandicap'], value = record['name'] + '|' + str(record['handicap']))
        for record in self.records if current.lower() in record['nameAndHandicap'].lower()
      ]
      if(len(results) > 25):
        results = results[:25]
      return results
    
    async def team_speedrun_autocomplete(
      interaction: Interaction,
      current: str
    ) -> list[app_commands.Choice[str]]:
      results = [
        app_commands.Choice(name = challenge['name'], value = challenge['name'])
        for challenge in self.challenges if current.lower() in challenge['name'].lower() and challenge['relayComponent'] is None
      ]
      if(len(results) > 25):
        results = results[:25]
      return results
    
    async def relay_autocomplete(
      interaction: Interaction,
      current: str
    ) -> list[app_commands.Choice[str]]:
      results = [
        app_commands.Choice(name = challenge['nameAndRelayComponent'], value = challenge['name'] + '|' + str(challenge['relayComponent']))
        for challenge in self.challenges if current.lower() in challenge['nameAndRelayComponent'].lower() and challenge['relayComponent'] is not None
      ]
      if(len(results) > 25):
        results = results[:25]
      return results

    # Register commands
    @self.bot.tree.command(name='initialize_backend', description='STAFF ONLY: Initialize the backend (will not work if the event is in progress)')
    async def initialize_backend(interaction: Interaction):
      await self.staffCheck(interaction)
      if(not self.competitionLoaded):
        raise errors.UserError('Competition not loaded')
      if(self.eventInProgress()):
        raise errors.UserError('The event is currently in progress')
      await interaction.response.send_message('Initializing backend...')
      self.backendClient.initializeBackend()
      await self.loadCompetitionInfo()
      await interaction.followup.send('Success: Backend initialized')

    @self.bot.tree.command(name='update_competitor_role', description='STAFF ONLY: Update the Competitor role (This happens automatically every 60 minutes)')
    async def update_competitor_role(interaction: Interaction):
      await self.staffCheck(interaction)
      if(not self.competitionLoaded):
        raise errors.UserError('Competition not loaded')
      await interaction.response.send_message('Updating competitor role...')
      response = self.backendClient.updateCompetitorRole()
      if(len(response['signupsNotFound']) == 0):
        await interaction.followup.send('Success: Competitor role updated. All Discord names were found on the server.')
      elif(len(response['signupsNotFound']) > 50):
        await interaction.followup.send(f'Success: Competitor role updated. {str(len(response['namesNotFound']))} names were not found on the server.')
      else:
        message = 'Success: Competitor role updated. The following signups were not found on the server:\n'
        for signup in response['signupsNotFound']:
          message += f'RSN: "{signup['rsn']}" / Discord name: "{signup['discordName']}"\n'
        message = message[:-1]
        await interaction.followup.send(message)

    @self.bot.tree.command(name='setup_discord_server', description='STAFF ONLY: Create team channels and create/assign team roles')
    async def setup_discord_server(interaction: Interaction):
      await self.staffCheck(interaction)
      if(not self.competitionLoaded):
        raise errors.UserError('Competition not loaded')
      if(self.eventInProgress()):
        raise errors.UserError('The event is currently in progress')
      await interaction.response.send_message('Setting up Discord server...')
      response = self.backendClient.setupDiscordServer()
      if(len(response['namesNotFound']) == 0):
        await interaction.followup.send('Success: Team roles/channels created. All Discord names were found on the server.')
      elif(len(response['namesNotFound']) > 50):
        await interaction.followup.send('Success: Team roles/channels created. ' + str(len(response['namesNotFound'])) + ' names were not found on the server.')
      else:
        message = 'Success: Team roles/channels created. The following Discord names were not found on the server:\n'
        for name in response['namesNotFound']:
          message += name + "\n"
        message = message[:-1]
        await interaction.followup.send(message)

    @self.bot.tree.command(name='teardown_discord_server', description='STAFF ONLY: Delete team channels/roles and de-assign Competitor/Captain roles')
    async def teardown_discord_server(interaction: Interaction):
      await self.staffCheck(interaction)
      if(not self.competitionLoaded):
        raise errors.UserError('Competition not loaded')
      if(self.eventInProgress()):
        raise errors.UserError('The event is currently in progress')
      await interaction.response.send_message('Tearing down Discord server...')
      self.backendClient.teardownDiscordServer()
      await interaction.followup.send('Success: Team roles/channels deleted; Competitor/Captain roles de-assigned.')

    @self.bot.tree.command(name='update_backend', description='STAFF ONLY: Update the backend (This happens automatically every 60 seconds)')
    async def update_backend(interaction: Interaction, force: Optional[bool] = False):
      await self.staffCheck(interaction)
      if(not self.competitionLoaded):
        raise errors.UserError('Competition not loaded')
      if(not force and not self.eventInProgress()):
        raise errors.UserError('The event is not currently in progress')
      await interaction.response.send_message('Updating backend...')
      self.backendClient.updateBackend(force)
      await interaction.followup.send('Success: Backend updated')

    @self.bot.tree.command(name='reload_competition_info', description='STAFF ONLY: Reload competition info from the backend')
    async def reload_competition_info(interaction: Interaction):
      await self.staffCheck(interaction)
      await interaction.response.send_message('Reloading competition info...')
      await self.loadCompetitionInfo()
      if(self.competitionLoaded):
        await interaction.followup.send('Successfully reloaded competition info')
      else:
        await interaction.followup.send('Failed to reload competition info. The backend might not be running.')

    @self.bot.tree.command(name='reinitialize_tile', description='STAFF ONLY: Reinitialize a tile in the backend')
    @app_commands.autocomplete(tile=tile_autocomplete)
    async def reinitialize_tile(interaction: Interaction, tile: str):
      await self.staffCheck(interaction)
      if(not self.competitionLoaded):
        raise errors.UserError('Competition not loaded')
      if(tile not in self.tiles):
        raise errors.UserError('Tile not found - Make sure to click the autocomplete option')
      await interaction.response.send_message('Reinitializing tile...')
      self.backendClient.reinitializeTile(tile)
      await interaction.followup.send('Success: Tile ' + tile + ' has been reinitialized')

    @self.bot.tree.command(name='add_player', description='STAFF ONLY: Add a player to the competition, and assign the relevant role.')
    @app_commands.autocomplete(team=team_autocomplete)
    async def add_player(interaction: Interaction, rsn: str, discord_name: str, team: str):
      await self.staffCheck(interaction)
      if(not self.competitionLoaded):
        raise errors.UserError('Competition not loaded')
      guild = self.bot.get_guild(self.guildId)
      if(not guild.get_member_named(discord_name.lower())):
        raise errors.UserError('Discord member not found')
      if(team not in self.teams):
        raise errors.UserError('Team not found - Make sure to click the autocomplete option')
      await interaction.response.send_message('Adding player...')
      self.backendClient.addPlayer(rsn, discord_name, team)
      await self.loadCompetitionInfo()
      await interaction.followup.send('Success: Player ' + rsn + ' added on team: ' + team)

    @self.bot.tree.command(name='change_player_team', description='STAFF ONLY: Change the team of a player. Also handles role changes.')
    @app_commands.autocomplete(player=player_autocomplete, team=team_autocomplete)
    async def change_player_team(interaction: Interaction, player: str, team: str):
      await self.staffCheck(interaction)
      if(not self.competitionLoaded):
        raise errors.UserError('Competition not loaded')
      if(player not in self.players):
        raise errors.UserError('Player not found - Make sure to click the autocomplete option')
      if(team not in self.teams):
        raise errors.UserError('Team not found - Make sure to click the autocomplete option')
      await interaction.response.send_message('Changing player team...')
      self.backendClient.changePlayerTeam(player, team)
      await self.loadCompetitionInfo()
      await interaction.followup.send('Success: Player ' + player + ' is now on team ' + team)

    @self.bot.tree.command(name='change_player_rsn', description='STAFF ONLY: Change the RSN of a player.')
    @app_commands.autocomplete(old_rsn=player_autocomplete)
    async def change_player_rsn(interaction: Interaction, old_rsn: str, new_rsn: str):
      await self.staffCheck(interaction)
      if(not self.competitionLoaded):
        raise errors.UserError('Competition not loaded')
      if(old_rsn not in self.players):
        raise errors.UserError('Player not found - Make sure to click the autocomplete option')
      await interaction.response.send_message('Changing player RSN...')
      self.backendClient.changePlayerRsn(old_rsn, new_rsn)
      await self.loadCompetitionInfo()
      await interaction.followup.send('Success: The RSN ' + old_rsn + ' has been changed to ' + new_rsn)

    @self.bot.tree.command(name='change_player_discord_name', description='STAFF ONLY: Change the Discord name of a player.')
    @app_commands.autocomplete(old_discord_name=discord_name_autocomplete)
    async def change_player_discord_name(interaction: Interaction, old_discord_name: str, new_discord_name: str):
      await self.staffCheck(interaction)
      if(not self.competitionLoaded):
        raise errors.UserError('Competition not loaded')
      if(old_discord_name not in self.discordNames):
        raise errors.UserError('Player not found - Make sure to click the autocomplete option')
      await interaction.response.send_message('Changing player Discord name...')
      self.backendClient.changePlayerDiscordName(old_discord_name, new_discord_name)
      await self.loadCompetitionInfo()
      await interaction.followup.send('Success: The Discord name ' + old_discord_name + ' has been changed to ' + new_discord_name)

    @self.bot.tree.command(name='set_staff_adjustment', description='STAFF ONLY: Set the staff adjustment for a contribution method on a player')
    @app_commands.autocomplete(player=player_autocomplete, method=method_autocomplete)
    async def set_staff_adjustment(interaction: Interaction, player: str, method: str, adjustment: int):
      await self.staffCheck(interaction)
      if(not self.competitionLoaded):
        raise errors.UserError('Competition not loaded')
      if(player not in self.players):
        raise errors.UserError('Player not found - Make sure to click the autocomplete option')
      await interaction.response.send_message('Setting staff adjustment...')
      self.backendClient.setStaffAdjustment(player, method, adjustment)
      await self.loadCompetitionInfo()
      await interaction.followup.send('Success: Player ' + player + ' now has a staff adjustment of ' + str(adjustment) + ' for ' + method)

    @self.bot.tree.command(name='submit_monster_killcount', description='Submit a monster killcount for the competition!')
    @app_commands.autocomplete(monster=monster_autocomplete)
    async def submit_monster_killcount(interaction: Interaction, screenshot: Attachment, monster: str, kc: int):
      await self.submissionPreChecks(interaction)
      if(kc < 0):
        raise errors.UserError('KC cannot be negative')
      if(monster not in self.monsters):
        raise errors.UserError('Invalid monster name (make sure to click on the autocomplete option)')
      description = f'{kc} KC of {monster}'
      ids = [self.backendClient.submitContribution(self.discordUserRSNs[interaction.user.name], monster, kc, [screenshot.url], description)]
      submission = submissions.Submission(self, interaction, ids, description)
      await self.sendSubmissionToQueue(submission)
      responseText = '# Submission received:\n'
      responseText += str(submission)
      await interaction.response.send_message(responseText)

    @self.bot.tree.command(name='submit_collection_log', description='Submit a collection log item for the competition! (Make sure the drop is in the screenshot)')
    @app_commands.autocomplete(item=clog_autocomplete)
    async def submit_collection_log(interaction: Interaction, screenshot: Attachment, item: str):
      await self.submissionPreChecks(interaction)
      if(item not in self.clogItems):
        raise errors.UserError('Invalid item name (make sure to click on the autocomplete option)')
      description = f'Collection log item "{item}"'
      ids = [self.backendClient.submitCollectionLogItem(self.discordUserRSNs[interaction.user.name], item, [screenshot.url], description)]
      submission = submissions.Submission(self, interaction, ids, description)
      await self.sendSubmissionToQueue(submission)
      responseText = '# Submission received:\n'
      responseText += str(submission)
      await interaction.response.send_message(responseText)

    @self.bot.tree.command(name='submit_pest_control', description='Submit your pest control games for the competition! (All difficulties added together)')
    async def submit_pest_control(interaction: Interaction, screenshot: Attachment, total_games: int):
      await self.submissionPreChecks(interaction)
      if(total_games < 0):
        raise errors.UserError('Total games cannot be negative')
      description = f'{total_games} games of pest control'
      ids = [self.backendClient.submitContribution(self.discordUserRSNs[interaction.user.name], 'Pest Control Games', total_games, [screenshot.url], description)]
      submission = submissions.Submission(self, interaction, ids, description)
      await self.sendSubmissionToQueue(submission)
      responseText = '# Submission received:\n'
      responseText += str(submission)
      await interaction.response.send_message(responseText)

    @self.bot.tree.command(name='submit_lms', description='Submit your LMS kills for the competition!')
    async def submit_lms(interaction: Interaction, screenshot: Attachment, kills: int, wins: int):
      await self.submissionPreChecks(interaction)
      if(kills < 0):
        raise errors.UserError('Kills cannot be negative')
      if(wins < 0):
        raise errors.UserError('Wins cannot be negative')
      description = f'{kills} kills and {wins} wins in LMS'
      ids = []
      ids.append(self.backendClient.submitContribution(self.discordUserRSNs[interaction.user.name], 'LMS: Kills', kills, [screenshot.url], description))
      ids.append(self.backendClient.submitContribution(self.discordUserRSNs[interaction.user.name], 'LMS: Wins', wins, [screenshot.url], description))
      submission = submissions.Submission(self, interaction, ids, description)
      await self.sendSubmissionToQueue(submission)
      responseText = '# Submission received:\n'
      responseText += str(submission)
      await interaction.response.send_message(responseText)

    @self.bot.tree.command(name='submit_mta', description='Submit your MTA points for the competition!')
    async def submit_mta(interaction: Interaction, screenshot: Attachment, telekinetic_points: int, alchemy_points: int, enchanting_points: int, graveyard_points: int):
      await self.submissionPreChecks(interaction)
      if(alchemy_points < 0 or graveyard_points < 0 or enchanting_points < 0 or telekinetic_points < 0):
        raise errors.UserError('Points cannot be negative')
      description = f'{alchemy_points}/{graveyard_points}/{enchanting_points}/{telekinetic_points} MTA points'
      ids = []
      ids.append(self.backendClient.submitContribution(self.discordUserRSNs[interaction.user.name], "MTA: Alchemist's Playground", alchemy_points, [screenshot.url], description))
      ids.append(self.backendClient.submitContribution(self.discordUserRSNs[interaction.user.name], "MTA: Creature Graveyard", graveyard_points, [screenshot.url], description))
      ids.append(self.backendClient.submitContribution(self.discordUserRSNs[interaction.user.name], "MTA: Enchanting Chamber", enchanting_points, [screenshot.url], description))
      ids.append(self.backendClient.submitContribution(self.discordUserRSNs[interaction.user.name], "MTA: Telekinetic Theatre", telekinetic_points, [screenshot.url], description))
      submission = submissions.Submission(self, interaction, ids, description)
      await self.sendSubmissionToQueue(submission)
      responseText = '# Submission received:\n'
      responseText += str(submission)
      await interaction.response.send_message(responseText)

    @self.bot.tree.command(name='submit_tithe_farm', description='Submit your tithe farm points for the competition!')
    async def submit_tithe_farm(interaction: Interaction, screenshot: Attachment, points: int):
      await self.submissionPreChecks(interaction)
      if(points < 0):
        raise errors.UserError('Points cannot be negative')
      description = f'{points} tithe farm points'
      ids = [self.backendClient.submitContribution(self.discordUserRSNs[interaction.user.name], 'Tithe Farm Points', points, [screenshot.url], description)]
      submission = submissions.Submission(self, interaction, ids, description)
      await self.sendSubmissionToQueue(submission)
      responseText = '# Submission received:\n'
      responseText += str(submission)
      await interaction.response.send_message(responseText)

    @self.bot.tree.command(name='submit_farming_contracts', description='Submit your farming contracts for the competition!')
    async def submit_farming_contracts(interaction: Interaction, screenshot: Attachment, contracts: int):
      await self.submissionPreChecks(interaction)
      if(contracts < 0):
        raise errors.UserError('Contracts cannot be negative')
      description = f'{contracts} farming contracts'
      ids = [self.backendClient.submitContribution(self.discordUserRSNs[interaction.user.name], 'Farming Contracts', contracts, [screenshot.url], description)]
      submission = submissions.Submission(self, interaction, ids, description)
      await self.sendSubmissionToQueue(submission)
      responseText = '# Submission received:\n'
      responseText += str(submission)
      await interaction.response.send_message(responseText)

    @self.bot.tree.command(name='submit_nex_nihil_shards', description='Submit your nihil shards from Nex for the competition!')
    async def submit_nex_nihil_shards(interaction: Interaction, screenshot: Attachment, shards: int):
      await self.submissionPreChecks(interaction)
      if(shards < 0):
        raise errors.UserError('Shards cannot be negative')
      description = f'{shards} nihil shards'
      ids = [self.backendClient.submitContribution(self.discordUserRSNs[interaction.user.name], 'Nex: Nihil Shards', shards, [screenshot.url], description)]
      submission = submissions.Submission(self, interaction, ids, description)
      await self.sendSubmissionToQueue(submission)
      responseText = '# Submission received:\n'
      responseText += str(submission)
      await interaction.response.send_message(responseText)

    @self.bot.tree.command(name='submit_revenant_ether', description='Submit your revenant ether for the competition!')
    async def submit_revenant_ether(interaction: Interaction, screenshot: Attachment, ether: int):
      await self.submissionPreChecks(interaction)
      if(ether < 0):
        raise errors.UserError('Ether cannot be negative')
      description = f'{ether} revenant ether'
      ids = [self.backendClient.submitContribution(self.discordUserRSNs[interaction.user.name], 'Revenants: Ether', ether, [screenshot.url], description)]
      submission = submissions.Submission(self, interaction, ids, description)
      await self.sendSubmissionToQueue(submission)
      responseText = '# Submission received:\n'
      responseText += str(submission)
      await interaction.response.send_message(responseText)
    
    @self.bot.tree.command(name='submit_hueycoatl_hides', description='Submit your Hueycoatl hides for the competition!')
    async def submit_hueycoatl_hides(interaction: Interaction, screenshot: Attachment, hides: int):
      await self.submissionPreChecks(interaction)
      if(hides < 0):
        raise errors.UserError('Hides cannot be negative')
      description = f'{hides} Hueycoatl hides'
      ids = [self.backendClient.submitContribution(self.discordUserRSNs[interaction.user.name], 'Hueycoatl: Hides', hides, [screenshot.url], description)]
      submission = submissions.Submission(self, interaction, ids, description)
      await self.sendSubmissionToQueue(submission)
      responseText = '# Submission received:\n'
      responseText += str(submission)
      await interaction.response.send_message(responseText)

    @self.bot.tree.command(name='submit_mixology', description='Submit your mixology resin counts for the competition!')
    async def submit_mixology(interaction: Interaction, screenshot: Attachment, mox_resin: int, aga_resin: int, lye_resin: int):
      await self.submissionPreChecks(interaction)
      if(mox_resin < 0 or aga_resin < 0 or lye_resin < 0):
        raise errors.UserError('Resin counts cannot be negative')
      totalResin = mox_resin + aga_resin + lye_resin
      description = f'{totalResin} mixology resin'
      ids = [self.backendClient.submitContribution(self.discordUserRSNs[interaction.user.name], 'Mixology: Resin', totalResin, [screenshot.url], description)]
      submission = submissions.Submission(self, interaction, ids, description)
      await self.sendSubmissionToQueue(submission)
      responseText = '# Submission received:\n'
      responseText += str(submission)
      await interaction.response.send_message(responseText)

    @self.bot.tree.command(name='submit_barbarian_assault', description='Submit your BA points for the competition!')
    async def submit_barbarian_assault(interaction: Interaction, screenshot: Attachment,
      attacker_points: int,
      defender_points: int,
      collector_points: int,
      healer_points: int,
    ):
      await self.submissionPreChecks(interaction)
      for param in submit_barbarian_assault.parameters:
        argName = param.name
        argValue = locals()[argName]
        if(isinstance(argValue, int) and argValue < 0):
          raise errors.UserError('BA arguments cannot be negative')
      points = attacker_points + defender_points + collector_points + healer_points
      description = f'{points} BA points'
      ids = [self.backendClient.submitContribution(self.discordUserRSNs[interaction.user.name], 'Barbarian Assault Points', points, [screenshot.url], description)]
      submission = submissions.Submission(self, interaction, ids, description)
      await self.sendSubmissionToQueue(submission)
      responseText = '# Submission received:\n'
      responseText += str(submission)
      await interaction.response.send_message(responseText)

    @self.bot.tree.command(name='submit_doom_of_mokhaiotl', description='Submit your delve completions for the Doom of Mokhaiotl boss!')
    async def submit_doom_of_mokhaiotl(interaction: Interaction, screenshot: Attachment,
      delve_1: int,
      delve_2: int,
      delve_3: int,
      delve_4: int,
      delve_5: int,
      delve_6: int,
      delve_7: int,
      delve_8: int,
      delve_8_plus: int
    ):
      await self.submissionPreChecks(interaction)
      totalDelves = 0
      for param in submit_doom_of_mokhaiotl.parameters:
        argName = param.name
        argValue = locals()[argName]
        if(isinstance(argValue, int) and argValue < 0):
          raise errors.UserError('Delve completions cannot be negative')
        if(isinstance(argValue, int)):
          totalDelves += argValue
      description = f'{totalDelves} total delves at Doom of Mokhaiotl'
      ids = []
      ids.append(self.backendClient.submitContribution(self.discordUserRSNs[interaction.user.name], 'Doom of Mokhaiotl - Delve Level 1', delve_1, [screenshot.url], description))
      ids.append(self.backendClient.submitContribution(self.discordUserRSNs[interaction.user.name], 'Doom of Mokhaiotl - Delve Level 2', delve_2, [screenshot.url], description))
      ids.append(self.backendClient.submitContribution(self.discordUserRSNs[interaction.user.name], 'Doom of Mokhaiotl - Delve Level 3', delve_3, [screenshot.url], description))
      ids.append(self.backendClient.submitContribution(self.discordUserRSNs[interaction.user.name], 'Doom of Mokhaiotl - Delve Level 4', delve_4, [screenshot.url], description))
      ids.append(self.backendClient.submitContribution(self.discordUserRSNs[interaction.user.name], 'Doom of Mokhaiotl - Delve Level 5', delve_5, [screenshot.url], description))
      ids.append(self.backendClient.submitContribution(self.discordUserRSNs[interaction.user.name], 'Doom of Mokhaiotl - Delve Level 6', delve_6, [screenshot.url], description))
      ids.append(self.backendClient.submitContribution(self.discordUserRSNs[interaction.user.name], 'Doom of Mokhaiotl - Delve Level 7', delve_7, [screenshot.url], description))
      ids.append(self.backendClient.submitContribution(self.discordUserRSNs[interaction.user.name], 'Doom of Mokhaiotl - Delve Level 8', delve_8, [screenshot.url], description))
      ids.append(self.backendClient.submitContribution(self.discordUserRSNs[interaction.user.name], 'Doom of Mokhaiotl - Delve Level 8+', delve_8_plus, [screenshot.url], description))
      submission = submissions.Submission(self, interaction, ids, description)
      await self.sendSubmissionToQueue(submission)
      responseText = '# Submission received:\n'
      responseText += str(submission)
      await interaction.response.send_message(responseText)
    
    @self.bot.tree.command(name='submit_team_speedrun', description='Submit your team speedruns for the competition! (Make sure to have precise timing enabled.)')
    @app_commands.autocomplete(challenge=team_speedrun_autocomplete, rsn_1=player_autocomplete, rsn_2=player_autocomplete, rsn_3=player_autocomplete, rsn_4=player_autocomplete, rsn_5=player_autocomplete)
    async def submit_team_speedrun(interaction: Interaction, screenshot: Attachment, minutes: int, seconds: int, tenths_of_seconds: int, challenge: str, rsn_1: str, rsn_2: Optional[str], rsn_3: Optional[str], rsn_4: Optional[str], rsn_5: Optional[str]):
      await self.submissionPreChecks(interaction)
      if(minutes < 0 or seconds < 0 or tenths_of_seconds < 0):
        raise errors.UserError('Times cannot be negative')
      if(tenths_of_seconds > 9):
        raise errors.UserError('tenths_of_seconds cannot be greater than 9')
      finalSeconds = (minutes * 60) + seconds + (tenths_of_seconds * 0.1)
      description = '{0} time of {1:0>2}:{2:0>2}.{3}'.format(challenge, minutes, seconds, tenths_of_seconds)
      ids = [self.backendClient.submitChallenge(rsn_1, challenge, finalSeconds, [screenshot.url], description)]
      if(rsn_2 is not None):
        ids.append(self.backendClient.submitChallenge(rsn_2, challenge, finalSeconds, [screenshot.url], description))
      if(rsn_3 is not None):
        ids.append(self.backendClient.submitChallenge(rsn_3, challenge, finalSeconds, [screenshot.url], description))
      if(rsn_4 is not None):
        ids.append(self.backendClient.submitChallenge(rsn_4, challenge, finalSeconds, [screenshot.url], description))
      if(rsn_5 is not None):
        ids.append(self.backendClient.submitChallenge(rsn_5, challenge, finalSeconds, [screenshot.url], description))
      submission = submissions.Submission(self, interaction, ids, description)
      await self.sendSubmissionToQueue(submission)
      responseText = '# Submission received:\n'
      responseText += str(submission)
      await interaction.response.send_message(responseText)

    @self.bot.tree.command(name='submit_relay_time', description='Submit your relay times for the competition! (Make sure to have precise timing enabled.)')
    @app_commands.autocomplete(challenge=relay_autocomplete)
    async def submit_relay_time(interaction: Interaction, screenshot: Attachment, minutes: int, seconds: int, tenths_of_seconds: int, challenge: str):
      await self.submissionPreChecks(interaction)
      if(minutes < 0 or seconds < 0 or tenths_of_seconds < 0):
        raise errors.UserError('Times cannot be negative')
      if(tenths_of_seconds > 9):
        raise errors.UserError('tenths_of_seconds cannot be greater than 9')
      finalSeconds = (minutes * 60) + seconds + (tenths_of_seconds * 0.1)
      challengeName = challenge.split('|')[0]
      if(challenge.split('|')[1] != 'None'):
        challengeName += ' - ' + challenge.split('|')[1]
      description = '{0} time of {1:0>2}:{2:0>2}.{3}'.format(challengeName, minutes, seconds, tenths_of_seconds)
      ids = [self.backendClient.submitChallenge(self.discordUserRSNs[interaction.user.name], challenge, finalSeconds, [screenshot.url], description)]
      submission = submissions.Submission(self, interaction, ids, description)
      await self.sendSubmissionToQueue(submission)
      responseText = '# Submission received:\n'
      responseText += str(submission)
      await interaction.response.send_message(responseText)

    @self.bot.tree.command(name='submit_record', description='Submit your record values for the competition!')
    @app_commands.autocomplete(record=record_autocomplete)
    async def submit_record(interaction: Interaction, video_url: str, value: int, record: str):
      await self.submissionPreChecks(interaction)
      if(value < 0):
        raise errors.UserError('Value cannot be negative')
      description = 'Record of {0} XP in {1}'.format(value, record.split('|')[0])
      if(record.split('|')[1] != 'None'):
        description += ' with handicap ' + record.split('|')[1]
      ids = [self.backendClient.submitRecord(self.discordUserRSNs[interaction.user.name], record, value, video_url, description)]
      submission = submissions.Submission(self, interaction, ids, description)
      await self.sendSubmissionToQueue(submission)
      responseText = '# Submission received:\n'
      responseText += str(submission)
      await interaction.response.send_message(responseText)

    @self.bot.tree.command(name='submit_item_drops', description='Submit an item drop from an activity!')
    @app_commands.autocomplete(item_type=item_drop_autocomplete)
    async def submit_item_drops(interaction: Interaction, screenshot: Attachment, item_type: str):
      await self.submissionPreChecks(interaction)
      description = 'Item drop for {0}'.format(item_type)
      ids = [self.backendClient.submitContributionIncrement(self.discordUserRSNs[interaction.user.name], item_type, 1, [screenshot.url], description)]
      submission = submissions.Submission(self, interaction, ids, description)
      await self.sendSubmissionToQueue(submission)
      responseText = '# Submission received:\n'
      responseText += str(submission)
      await interaction.response.send_message(responseText)

    @self.bot.tree.command(name='submit_minigame_purchase', description='Submit an item purchase for a minigame!')
    @app_commands.autocomplete(item_name=purchase_item_autocomplete)
    async def submit_item_drops(interaction: Interaction, before_screenshot: Attachment, after_screenshot: Attachment, item_name: str, quantity: int):
      await self.submissionPreChecks(interaction)
      if(quantity < 1):
        raise errors.UserError('Quantity cannot be 0 or negative')
      description = 'Purchase of {0} {1}'.format(quantity, item_name)
      ids = []
      for item in self.purchaseItems:
        if(item['name'] == item_name):
          totalCost = quantity * item['cost']
          ids.append(self.backendClient.submitContributionPurchase(self.discordUserRSNs[interaction.user.name], item['methodName'], totalCost, [before_screenshot.url, after_screenshot.url], description))
      submission = submissions.Submission(self, interaction, ids, description)
      await self.sendSubmissionToQueue(submission)
      responseText = '# Submission received:\n'
      responseText += str(submission)
      await interaction.response.send_message(responseText)

  '''
  Registers an error handler callback to the bot
  '''
  def registerErrorHandler(self):
    log.info('Registering error handler...')
    @self.bot.tree.error
    async def handleCommandErrors(interaction, error):
      if(isinstance(error.original, errors.UserError)):
        await interaction.response.send_message(f'Error: {str(error.original)}')
      else:
        log.error('Error', exc_info=error)
        submission = submissions.Submission(self, interaction)
        await self.sendErrorMessageToErrorChannel(interaction, submission, error)

  '''
  Registers an interaction hook callback to the bot
  '''
  def registerInteractionHook(self):
    log.info('Registering interaction hook...')
    @self.bot.event
    async def on_interaction(interaction):
      data = interaction.data
      if(interaction.type == InteractionType.component and data['component_type'] == 2): # This is a button click interaction
        if(not self.competitionLoaded):
          await interaction.response.send_message('Event not loaded')
          return
        # Parse the Submission out of the message contents
        message = interaction.message.content
        submissionJson = None
        for line in message.splitlines():
          if(line.startswith('Submission json: `')): # This is the line that has our json on it
            submissionJson = line.replace('Submission json: ', '').replace('`', '')
            break
        if(submissionJson == None):
          return # Not a submission message
        if(data['custom_id'] == 'approve'): # User has clicked the "Approve" button

          # Make sure the user is a screenshot approver
          try:
            await self.checkForScreenshotApprover(interaction)
          except errors.UserError as error:
            log.error('Error', exc_info=error)
            await interaction.response.send_message(f'Error: {interaction.user.display_name} tried to approve this submission but is not a screenshot approver')
            return
          
          # Log the approval
          submission = submissions.fromJson(submissionJson, self)
          log.info('Submission approved by ' + interaction.user.name + ':\n' + submissionJson)

          # Send the approval to the backend
          for id in submission.ids:
            response = self.backendClient.approveSubmission(id, interaction.user.display_name)

          # Delete the submission message and any replies (which could exist because of error messages)
          submissionQueueChannel = self.bot.get_channel(self.submissionQueueChannelId)
          async for message in submissionQueueChannel.history(limit=None):
            if(message.reference and message.reference.message_id == interaction.message.id): # The message we're looking at is a reply to the submission message
              await message.delete()
          await interaction.message.delete()

          # Send a message to the submission log
          submissionLogChannel = self.bot.get_channel(self.submissionLogChannelId)
          view = ui.View()
          view.add_item(ui.Button(style=ButtonStyle.grey, custom_id='undo', label='Undo'))
          await submissionLogChannel.send(f'# Submission approved by {interaction.user.display_name}:\n' + str(submission), view=view)

          # Send a message to the player's team submission channel
          submissionsChannel = self.teamSubmissionChannels[submission.team]
          await submissionsChannel.send(f'<@{submission.user.id}> Your {submission.shortDesc} has been approved by {interaction.user.display_name}')
          
        elif(data['custom_id'] == 'deny'): # User has clicked the "Deny" button

          # Make sure the user is a screenshot approver
          try:
            await self.checkForScreenshotApprover(interaction)
          except errors.UserError as error:
            log.error('Error', exc_info=error)
            await interaction.response.send_message(f'Error: {interaction.user.display_name} tried to deny this submission but is not a screenshot approver')
            return
          
          # Log the denial
          submission = submissions.fromJson(submissionJson, self)
          log.info('Submission denied by ' + interaction.user.name + ':\n' + submissionJson)

          # Send the denial to the backend
          for id in submission.ids:
            response = self.backendClient.denySubmission(id, interaction.user.display_name)

          # Delete the submission message and any replies (which could exist because of error messages)
          submissionQueueChannel = self.bot.get_channel(self.submissionQueueChannelId)
          async for message in submissionQueueChannel.history(limit=None):
            if(message.reference and message.reference.message_id == interaction.message.id): # The message we're looking at is a reply to the submission message
              await message.delete()
          await interaction.message.delete()

          # Send a message to the submission log
          submissionLogChannel = self.bot.get_channel(self.submissionLogChannelId)
          view = ui.View()
          view.add_item(ui.Button(style=ButtonStyle.grey, custom_id='undo', label='Undo'))
          await submissionLogChannel.send(f'# Submission denied by {interaction.user.display_name}:\n' + str(submission), view=view)

          # Send a message to the player's team submission channel
          submissionsChannel = self.teamSubmissionChannels[submission.team]
          await submissionsChannel.send(f'<@{submission.user.id}> Your {submission.shortDesc} has been denied by {interaction.user.display_name}')

        elif(data['custom_id'] == 'undo'): # User has clicked the "Undo" button in the submission log

          # Make sure the user is a screenshot approver
          try:
            await self.checkForScreenshotApprover(interaction)
          except errors.UserError as error:
            log.error('Error', exc_info=error)
            await interaction.response.send_message(f'Error: {interaction.user.display_name} tried to undo this decision but is not a screenshot approver')
            return
          
          # Log the undo
          submission = submissions.fromJson(submissionJson, self)
          log.info('Submission undone by ' + interaction.user.name + ':\n' + submissionJson)

          # Send the undo to the backend
          for id in submission.ids:
            response = self.backendClient.undoDecision(id)

          # Delete the submission message and any replies (which could exist because of error messages)
          submissionQueueChannel = self.bot.get_channel(self.submissionQueueChannelId)
          async for message in submissionQueueChannel.history(limit=None):
            if(message.reference and message.reference.message_id == interaction.message.id): # The message we're looking at is a reply to the submission message
              await message.delete()
          await interaction.message.delete()

          # Send the submission back to the queue
          await self.sendSubmissionToQueue(submission)

        else: # Something unexpected
          pass

  '''
  Registers a ready hook callback to the bot
  '''
  def registerReadyHook(self, commandLineArgs):
    log.info('Registering ready hook...')
    @self.bot.event
    async def on_ready():
      log.info(f'Logged in as {self.bot.user.name}')

      if(commandLineArgs.clearcommands):
        log.info('Clearing commands...')
        guild = self.bot.get_guild(self.guildId)
        self.bot.tree.clear_commands(guild=None)
        self.bot.tree.clear_commands(guild=guild)
        await self.bot.tree.sync(guild=None)
        await self.bot.tree.sync(guild=guild)
        log.info('Commands cleared')
        os._exit(0)
      if(commandLineArgs.updatecommands):
        log.info('Updating commands...')
        synced = await self.bot.tree.sync()
        log.info(f'Synced {len(synced)} commands.')
        os._exit(0)
          
      await self.loadCompetitionInfo()

      log.info('Startup complete, ready to accept commands!')
  
  '''
  Connects the bot to the server to begin accepting commands
  '''
  def start(self):
    self.bot.run(self.token)