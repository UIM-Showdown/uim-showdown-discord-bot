import logging
import os
import re
from datetime import datetime
from discord.ext import commands
from discord import utils, Intents, ui, app_commands, Interaction, Attachment, Colour, CategoryChannel, TextChannel, VoiceChannel, PermissionOverwrite, InteractionType, ButtonStyle
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
    self.teams = []
    self.contributionMethods = []
    self.monsters = []
    self.itemDrops = []
    self.unrankedStartingValues = []
    self.clogItems = []
    self.records = []
    self.challenges = []
    self.competitionLoaded = False

  '''
  Helper method to make sure the person submitting the command is a competitor and is in the right channel
  '''
  async def submissionPreChecks(self, interaction):
    if(not self.competitionLoaded):
      raise errors.UserError('The event is not currently in progress')
    startDatetime = datetime.fromisoformat(self.competitionInfo['startDatetime'])
    endDatetime = datetime.fromisoformat(self.competitionInfo['endDatetime'])
    now = datetime.now().astimezone()
    if(now < startDatetime or now > endDatetime):
      raise errors.UserError('The event is not currently in progress')
    if(interaction.user.name not in self.discordUserRSNs):
      raise errors.UserError(f'{interaction.user.display_name} is not a registered player in this event')
    team = self.discordUserTeams[interaction.user.name]
    teamChannel = self.teamSubmissionChannels[team]
    if(teamChannel is None or interaction.channel != teamChannel):
      raise errors.UserError("Please only submit commands in your team's bot submission channel")
    
  async def adminCheck(self, interaction):
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
  Creates team roles/categories/channels and assigns team roles to players, using data from the backend
  '''
  async def setUpServer(self):
    teamInfo = self.backendClient.getTeamInfo()
    teamRosters = self.backendClient.getTeamRosters()
    guild = self.bot.get_guild(self.guildId)
    roles = guild.roles
    channels = guild.channels
    eventStaffRole = None
    captainRole = None
    cheerleaderRole = None
    for role in roles:
      if(role.name == 'Event staff'):
        eventStaffRole = role
      if(role.name == 'Captain'):
        captainRole = role
      if(role.name == 'Cheerleader'):
        cheerleaderRole = role
    if(eventStaffRole is None):
      log.error('Could not find event staff role. Exiting...')
      os._exit(1)
    if(captainRole is None):
      log.error('Could not find captain role. Exiting...')
      os._exit(1)
    if(cheerleaderRole is None):
      log.error('Could not find cheerleader role. Exiting...')
      os._exit(1)

    for teamName in teamInfo:
      # Create team role
      teamRole = None
      for role in roles:
        if(role.name == teamName):
          teamRole = role
      if(teamRole is None):
        teamRole = await guild.create_role(
          name = teamName,
          color = Colour.from_str('#' + teamInfo[teamName]['color'])
        )

      # Create team category
      category = None
      for channel in channels:
        if(isinstance(channel, CategoryChannel) and channel.name == teamName):
          category = channel
      if(category is None):
        category = await guild.create_category(
          name = teamName,
          overwrites = {
            guild.default_role: PermissionOverwrite(view_channel = False),
            eventStaffRole: PermissionOverwrite(view_channel = True, administrator = True),
            teamRole: PermissionOverwrite(view_channel = True, attach_files = True),
            cheerleaderRole: PermissionOverwrite(view_channel = True, attach_files = True),
            captainRole: PermissionOverwrite(manage_channels = True, manage_messages = True)
          }
        )

      # Create announcements text channel
      announcementsTextChannel = None
      announcementsTextChannelName = teamInfo[teamName]['tag'].lower() + '-announcements'
      for channel in channels:
        if(isinstance(channel, TextChannel) and channel.name == announcementsTextChannelName):
          announcementsTextChannel = channel
      if(announcementsTextChannel is None):
        announcementsTextChannel = await guild.create_text_channel(
          name = announcementsTextChannelName,
          category = category,
          overwrites = {
            guild.default_role: PermissionOverwrite(view_channel = False),
            eventStaffRole: PermissionOverwrite(view_channel = True, administrator = True),
            teamRole: PermissionOverwrite(view_channel = True, send_messages = False),
            cheerleaderRole: PermissionOverwrite(view_channel = True, send_messages = False),
            captainRole: PermissionOverwrite(send_messages = True, manage_messages = True)
          }
        )

      # Create general text channel
      generalTextChannel = None
      generalTextChannelName = teamInfo[teamName]['tag'].lower() + '-general'
      for channel in channels:
        if(isinstance(channel, TextChannel) and channel.name == generalTextChannelName):
          generalTextChannel = channel
      if(generalTextChannel is None):
        generalTextChannel = await guild.create_text_channel(
          name = generalTextChannelName,
          category = category
        )
      
      # Create general voice channel
      generalVoiceChannel = None
      generalVoiceChannelName = teamInfo[teamName]['tag'].lower() + '-general'
      for channel in channels:
        if(isinstance(channel, VoiceChannel) and channel.name == generalVoiceChannelName):
          generalVoiceChannel = channel
      if(generalVoiceChannel is None):
        generalVoiceChannel = await guild.create_voice_channel(
          name = generalVoiceChannelName,
          category = category
        )
      
      # Create bot submissions channel
      botSubmissionsChannel = None
      botSubmissionsChannelName = teamInfo[teamName]['tag'].lower() + '-bot-submissions'
      for channel in channels:
        if(isinstance(channel, TextChannel) and channel.name == botSubmissionsChannelName):
          botSubmissionsChannel = channel
      if(botSubmissionsChannel is None):
        botSubmissionsChannel = await guild.create_text_channel(
          name = botSubmissionsChannelName,
          category = category,
          overwrites = {
            guild.default_role: PermissionOverwrite(view_channel = False),
            eventStaffRole: PermissionOverwrite(view_channel = True, administrator = True),
            teamRole: PermissionOverwrite(view_channel = True),
            cheerleaderRole: PermissionOverwrite(view_channel = True),
            captainRole: PermissionOverwrite(manage_channels = False)
          }
        )

      # Assign team roles to players
      teamRoster = teamRosters[teamName]
      for player in teamRoster:
        member = guild.get_member_named(player['discordName'])
        if(member is None):
          log.error('Could not find Discord server member named "' + player['discordName'] + '". Continuing...')
          continue
        if(not member.get_role(teamRole.id)):
          await member.add_roles(teamRole)

  '''
  Deletes team roles/categories/channels, using data from the backend
  '''
  async def tearDownServer(self):
    teamInfo = self.backendClient.getTeamInfo()
    guild = self.bot.get_guild(self.guildId)
    roles = guild.roles
    channels = guild.channels
    competitorRole = None
    captainRole = None
    for role in roles:
      if(role.name == 'Competitor'):
        competitorRole = role
      if(role.name == 'Captain'):
        captainRole = role
    if(competitorRole is None):
      log.error('Could not find role named "Competitor". Exiting...')
      os._exit(1)
    if(captainRole is None):
      log.error('Could not find role named "Captain". Exiting...')
      os._exit(1)
    
    for teamName in teamInfo:
      # Delete team channels
      for channel in channels:
        if(isinstance(channel, CategoryChannel) and channel.name == teamName):
          category = channel
          for channelInCategory in category.channels:
            await channelInCategory.delete()
          await category.delete()

      # Delete team role
      for role in roles:
        if(role.name == teamName):
          await role.delete()

    # De-assign competitor role
    for member in guild.members:
      if(member.get_role(competitorRole.id)):
        await member.remove_roles(competitorRole)

    # De-assign captain role
    for member in guild.members:
      if(member.get_role(captainRole.id)):
        await member.remove_roles(captainRole)

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
      self.monsters = self.backendClient.getContributionMethodsByType('SUBMISSION_KC')
      self.itemDrops = self.backendClient.getContributionMethodsByType('SUBMISSION_ITEM_DROP')
      self.unrankedStartingValues = self.backendClient.getContributionMethodsByType('TEMPLE_KC')
      self.contributionMethods = self.backendClient.getContributionMethods()
      self.clogItems = self.backendClient.getCollectionLogItems()
      self.records = self.backendClient.getRecords()
      self.challenges = self.backendClient.getChallenges()

      teamRosters = self.backendClient.getTeamRosters()
      teamInfo = self.backendClient.getTeamInfo()
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
          self.discordUserRSNs[player['discordName']] = player['rsn']
          self.discordUserTeams[player['discordName']] = teamName

      self.players.sort()
      self.teams.sort()
      self.contributionMethods.sort()
      self.monsters.sort()
      self.itemDrops.sort()
      self.unrankedStartingValues.sort()
      self.clogItems.sort()

      self.competitionLoaded = True
      log.info('Competition info loaded!')
    except Exception as e: # The backend is likely not running, but we can still silently succeed without actually changing anything
      self.discordUserTeams = {}
      self.discordUserRSNs = {}
      self.teamSubmissionChannels = {}
      self.competitionInfo = {}
      self.players = []
      self.teams = []
      self.contributionMethods = []
      self.monsters = []
      self.itemDrops = []
      self.unrankedStartingValues = []
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
    
    async def method_autocomplete(
      interaction: Interaction,
      current: str
    ) -> list[app_commands.Choice[str]]:
      results = [
        app_commands.Choice(name = method, value = method)
        for method in self.contributionMethods if current.lower() in method.lower()
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
    
    async def unranked_starting_value_autocomplete(
      interaction: Interaction,
      current: str
    ) -> list[app_commands.Choice[str]]:
      results = [
        app_commands.Choice(name = value, value = value)
        for value in self.unrankedStartingValues if current.lower() in value.lower()
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
    
    async def challenge_autocomplete(
      interaction: Interaction,
      current: str
    ) -> list[app_commands.Choice[str]]:
      results = [
        app_commands.Choice(name = challenge['nameAndRelayComponent'], value = challenge['name'] + '|' + str(challenge['relayComponent']))
        for challenge in self.challenges if current.lower() in challenge['nameAndRelayComponent'].lower()
      ]
      if(len(results) > 25):
        results = results[:25]
      return results

    # Register commands
    @self.bot.tree.command(name='reload_competition_info', description='STAFF ONLY: Reload competition info from the backend')
    async def reload_competition_info(interaction: Interaction):
      await self.adminCheck(interaction)
      await interaction.response.send_message('Reloading competition info...')
      await self.loadCompetitionInfo()
      if(self.competitionLoaded):
        await interaction.followup.send('Successfully reloaded competition info')
      else:
        await interaction.followup.send('Failed to reload competition info. The backend might not be running.')

    @self.bot.tree.command(name='change_player_team', description='STAFF ONLY: Change the team of a player')
    @app_commands.autocomplete(player=player_autocomplete, team=team_autocomplete)
    async def change_player_team(interaction: Interaction, player: str, team: str):
      await self.adminCheck(interaction)
      if(not self.competitionLoaded):
        await interaction.response.send_message('Competition not loaded')
      await interaction.response.send_message('Changing player team...')
      self.backendClient.changePlayerTeam(player, team)
      await self.loadCompetitionInfo()
      if(self.competitionLoaded):
        await interaction.followup.send('Success: Player ' + player + ' is now on team ' + team)
      else:
        await interaction.followup.send('Failed to reload competition info after switching team. The backend might not be running.')

    @self.bot.tree.command(name='set_staff_adjustment', description='STAFF ONLY: Set the staff adjustment for a contribution method on a player')
    @app_commands.autocomplete(player=player_autocomplete, method=method_autocomplete)
    async def change_player_team(interaction: Interaction, player: str, method: str, adjustment: int):
      await self.adminCheck(interaction)
      if(not self.competitionLoaded):
        await interaction.response.send_message('Competition not loaded')
      await interaction.response.send_message('Setting staff adjustment...')
      self.backendClient.setStaffAdjustment(player, method, adjustment)
      await self.loadCompetitionInfo()
      if(self.competitionLoaded):
        await interaction.followup.send('Success: Player ' + player + ' now has a staff adjustment of ' + str(adjustment) + ' for ' + method)
      else:
        await interaction.followup.send('Failed to reload competition info after setting staff adjustment. The backend might not be running.')

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
    async def submit_lms(interaction: Interaction, screenshot: Attachment, kills: int):
      await self.submissionPreChecks(interaction)
      if(kills < 0):
        raise errors.UserError('Kills cannot be negative')
      description = f'{kills} kills in LMS'
      ids = [self.backendClient.submitContribution(self.discordUserRSNs[interaction.user.name], 'LMS: Kills', kills, [screenshot.url], description)]
      submission = submissions.Submission(self, interaction, ids, description)
      await self.sendSubmissionToQueue(submission)
      responseText = '# Submission received:\n'
      responseText += str(submission)
      await interaction.response.send_message(responseText)

    @self.bot.tree.command(name='submit_mta', description='Submit your MTA points for the competition!')
    async def submit_mta(interaction: Interaction, screenshot: Attachment, alchemy_points: int, graveyard_points: int, enchanting_points: int, telekinetic_points: int):
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

    @self.bot.tree.command(name='submit_barbarian_assault', description='Submit your BA points for the competition!')
    async def submit_barbarian_assault(interaction: Interaction, clog_screenshot: Attachment, blackboard_screenshot: Attachment,
      high_gambles: int,
      attacker_points: int,
      defender_points: int,
      collector_points: int,
      healer_points: int,
      attacker_level: int,
      defender_level: int,
      collector_level: int,
      healer_level: int,
      hats: int,
      torso: int,
      skirt: int,
      gloves: int,
      boots: int
    ):
      await self.submissionPreChecks(interaction)
      for param in submit_barbarian_assault.parameters:
        argName = param.name
        argValue = locals()[argName]
        if(isinstance(argValue, int) and argValue < 0):
          raise errors.UserError('BA arguments cannot be negative')
        if('level' in argName and (argValue < 1 or argValue > 5)):
          raise errors.UserError('BA levels must be 1-5')
      points = 0
      points += high_gambles * 500
      points += attacker_points + defender_points + collector_points + healer_points
      for level in [attacker_level, defender_level, collector_level, healer_level]:
        if(level > 1):
          points += 200
        if(level > 2):
          points += 300
        if(level > 3):
          points += 400
        if(level > 4):
          points += 500
      points += hats * 275 * 4
      points += torso * 375 * 4
      points += skirt * 375 * 4
      points += gloves * 150 * 4
      points += boots * 100 * 4
      description = f'{points} BA points'
      ids = [self.backendClient.submitContribution(self.discordUserRSNs[interaction.user.name], 'Barbarian Assault Points', points, [clog_screenshot.url, blackboard_screenshot.url], description)]
      submission = submissions.Submission(self, interaction, ids, description)
      await self.sendSubmissionToQueue(submission)
      responseText = '# Submission received:\n'
      responseText += str(submission)
      await interaction.response.send_message(responseText)

    @self.bot.tree.command(name='submit_challenge', description='Submit your challenge times for the competition! (Make sure to have precise timing enabled.)')
    @app_commands.autocomplete(challenge=challenge_autocomplete)
    async def submit_challenge(interaction: Interaction, screenshot: Attachment, minutes: int, seconds: int, tenths_of_seconds: int, challenge: str):
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

    @self.bot.tree.command(name='submit_record', description='Submit your record values for the competition! Format for completed_at is "2025-05-30 16:00:00"')
    @app_commands.autocomplete(record=record_autocomplete)
    async def submit_record(interaction: Interaction, video_url: str, value: int, record: str, completed_at: str):
      await self.submissionPreChecks(interaction)
      if(value < 0):
        raise errors.UserError('Value cannot be negative')
      if(not re.match('^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}$', completed_at)):
        raise errors.UserError('Please use the datetime format: "2025-05-30 16:00:00"')
      description = 'Record of {0} XP in {1}'.format(value, record.split('|')[0])
      if(record.split('|')[1] != 'None'):
        description += ' with handicap ' + record.split('|')[1]
      ids = [self.backendClient.submitRecord(self.discordUserRSNs[interaction.user.name], record, value, video_url, completed_at, description)]
      submission = submissions.Submission(self, interaction, ids, description)
      await self.sendSubmissionToQueue(submission)
      responseText = '# Submission received:\n'
      responseText += str(submission)
      await interaction.response.send_message(responseText)

    @self.bot.tree.command(name='submit_unranked_starting_kc', description='Submit your real starting KC if you are unranked in a boss!')
    @app_commands.autocomplete(boss=unranked_starting_value_autocomplete)
    async def submit_unranked_starting_kc(interaction: Interaction, screenshot: Attachment, boss: str, kc: int):
      await self.submissionPreChecks(interaction)
      if(kc < 0):
        raise errors.UserError('KC cannot be negative')
      description = 'Starting KC of {0} for {1}'.format(kc, boss)
      ids = [self.backendClient.submitUnrankedStartingKC(self.discordUserRSNs[interaction.user.name], boss, kc, [screenshot.url], description)]
      submission = submissions.Submission(self, interaction, ids, description)
      await self.sendSubmissionToQueue(submission)
      responseText = '# Submission received:\n'
      responseText += str(submission)
      await interaction.response.send_message(responseText)

    @self.bot.tree.command(name='submit_item_drops', description='Submit the number of item drops you have! (Make sure to submit the TOTAL NUMBER from your log.)')
    @app_commands.autocomplete(method=item_drop_autocomplete)
    async def submit_item_drops(interaction: Interaction, screenshot: Attachment, method: str, num_drops: int):
      await self.submissionPreChecks(interaction)
      if(num_drops < 0):
        raise errors.UserError('KC cannot be negative')
      description = '{0} drops from {1}'.format(num_drops, method)
      ids = [self.backendClient.submitContribution(self.discordUserRSNs[interaction.user.name], method, num_drops, [screenshot.url], description)]
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
            response = self.backendClient.approveSubmission(id)

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
            response = self.backendClient.denySubmission(id)

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
      if(commandLineArgs.setupserver):
        response = input('Are you sure you want to start the server setup process? This will create categories/channels/roles for every team and assign roles to players (Y/N): ')
        if(response.lower() == 'y'):
          log.info('Starting server setup...')
          await self.setUpServer()
          log.info('Server setup completed')
          os._exit(0)
        else:
          log.info('Exiting...')
          os._exit(0)
      if(commandLineArgs.teardownserver):
        response = input('Are you sure you want to DELETE ALL THE TEAM CHANNELS AND ROLES? This is very dangerous (Y/N): ')
        if(response.lower() == 'y'):
          log.info('Starting server teardown...')
          await self.tearDownServer()
          log.info('Server teardown completed')
          os._exit(0)
        else:
          log.info('Exiting...')
          os._exit(0)
          
      await self.loadCompetitionInfo()

      log.info('Startup complete, ready to accept commands!')
  
  '''
  Connects the bot to the server to begin accepting commands
  '''
  def start(self):
    self.bot.run(self.token)