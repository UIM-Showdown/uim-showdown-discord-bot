import logging
import os
from discord.ext import commands
from discord import Intents, ui, app_commands, Interaction, Attachment, Colour, CategoryChannel, TextChannel, VoiceChannel, PermissionOverwrite, InteractionType, ButtonStyle
from typing import Literal
import showdownbot.errors as errors
import showdownbot.approvalrequest as approvalrequest
from showdownbot.googlesheetclient import GoogleSheetClient

'''
A wrapper for discord.py's "Bot" class that handles most of the logic for the bingo
'''
class ShowdownBot:
  
  '''
  Initializes instance variables and calls instance methods to register callbacks to the bot
  '''
  def __init__(self, commandLineArgs, configProperties):
      
    # Load config properties
    bingoProperties = configProperties['BingoProperties']
    self.token = bingoProperties['token']
    self.submissionQueueChannelId = int(bingoProperties['submissionQueueChannelId'])
    self.submissionLogChannelId = int(bingoProperties['submissionLogChannelId'])
    self.errorsChannelId = int(bingoProperties['errorsChannelId'])
    self.guildId = int(bingoProperties['guildId'])
    self.submissionSheetId = bingoProperties['submissionSheetId']
    self.bingoInfoSheetId = bingoProperties['bingoInfoSheetId']
    self.googleSheetClient = GoogleSheetClient(self.submissionSheetId, self.bingoInfoSheetId)

    # Set up bot object
    intents = Intents.default()
    intents.members = True # Required for role assignments to work
    intents.message_content = True # Required for the commands extension to work
    self.bot = commands.Bot(command_prefix='/', intents=intents)

    self.registerErrorHandler()
    self.registerReadyHook(commandLineArgs)
    self.registerCommands()
    self.registerInteractionHook()

  '''
  Helper method to raise a BingoUserError if the user that spawned the interaction is not on a team (and therefore should not be able to use commands)
  '''
  async def checkForValidPlayer(self, interaction):
    if(interaction.user.name not in self.discordUserRSNs):
      raise errors.BingoUserError('User is not a registered player in this event')
  
  '''
  Creates team roles/categories/channels and assigns team roles to players, using data from the bingo info sheet
  '''
  async def setUpServer(self):
    await self.updateCompetitorRole()
    teamInfo = self.googleSheetClient.getTeamInfo()
    teamRosters = self.googleSheetClient.getTeamRosters()
    guild = self.bot.get_guild(self.guildId)
    roles = guild.roles
    channels = guild.channels
    eventStaffRole = None
    captainRole = None
    for role in roles:
      if(role.name == 'Event staff'):
        eventStaffRole = role
      if(role.name == 'Captain'):
        captainRole = role
    if(eventStaffRole is None):
      print('Could not find event staff role. Exiting...')
      os._exit(1)
    if(captainRole is None):
      print('Could not find captain role. Exiting...')
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
          color = Colour.from_str(teamInfo[teamName]['color'])
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
            teamRole: PermissionOverwrite(view_channel = True),
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
            captainRole: PermissionOverwrite(manage_channels = False)
          }
        )

      # Assign team roles to players
      teamRoster = teamRosters[teamName]
      for player in teamRoster:
        member = guild.get_member_named(player['discordName'])
        if(member is None):
          print('Could not find Discord server member named "' + player['discordName'] + '". Continuing...')
          continue
        if(not member.get_role(teamRole.id)):
          await member.add_roles(teamRole)

  '''
  Deletes team roles/categories/channels, using data from the bingo info sheet
  '''
  async def tearDownServer(self):
    teamInfo = self.googleSheetClient.getTeamInfo()
    guild = self.bot.get_guild(self.guildId)
    roles = guild.roles
    channels = guild.channels
    competitorRole = None
    for role in roles:
      if(role.name == 'Competitor'):
        competitorRole = role
    if(competitorRole is None):
      print('Could not find role named "Competitor". Exiting...')
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

  '''
  Assigns the "Competitor" role, using data from the bingo info sheet
  '''
  async def updateCompetitorRole(self):
    signedUpDiscordMembers = self.googleSheetClient.getSignedUpDiscordMembers()
    guild = self.bot.get_guild(self.guildId)
    roles = guild.roles
    competitorRole = None
    for role in roles:
      if(role.name == 'Competitor'):
        competitorRole = role
    if(competitorRole is None):
      print('Could not find role named "Competitor". Exiting...')
      os._exit(1)

    for signedUpDiscordMember in signedUpDiscordMembers:
      member = guild.get_member_named(signedUpDiscordMember)
      if(member is None):
        print('Could not find Discord server member named "' + signedUpDiscordMember + '". Continuing...')
        continue
      if(not member.get_role(competitorRole.id)):
        await member.add_roles(competitorRole)

  '''
  Helper method to send a message to the error channel to report an error, and respond to the original interaction to notify the user that the error has been reported
  '''
  async def sendErrorMessageToErrorChannel(self, interaction, request, error):
    errorText = 'Unexpected error occurred:\n'
    if(request):
      errorText += 'Processing request: \n' + str(request) + '\n'
    if(hasattr(error, 'original')):
      errorText += f'Error: {str(error.original)}'
    else:
      errorText += f'Error: {str(error)}'
    channel = self.bot.get_channel(self.errorsChannelId)
    await channel.send(errorText)
    if(interaction):
      await interaction.response.send_message('Unexpected error: The admins have been notified to review this error')

  '''
  Helper method to send a message to the approvals channel to request approval for a submission
  '''
  async def requestApproval(self, request):
    requestText = 'New approval requested:\n'
    requestText += str(request)
    view = ui.View()
    view.add_item(ui.Button(style=ButtonStyle.success, custom_id='approve', label='Approve'))
    view.add_item(ui.Button(style=ButtonStyle.danger, custom_id='deny', label='Deny'))
    await self.bot.get_channel(self.submissionQueueChannelId).send(requestText, view=view)
  
  '''
  Checks for command line arguments indicating alternate run commands, and executes them, exiting afterwards
  '''
  async def handleAlternateRunCommands(self, commandLineArgs):
    if(commandLineArgs.clearcommands):
      print('Clearing commands...')
      guild = self.bot.get_guild(self.guildId)
      self.bot.tree.clear_commands(guild=None)
      self.bot.tree.clear_commands(guild=guild)
      await self.bot.tree.sync(guild=None)
      await self.bot.tree.sync(guild=guild)
      print('Commands cleared')
      os._exit(0)
    if(commandLineArgs.updatecommands):
      print('Updating commands...')
      synced = await self.bot.tree.sync()
      print(f'Synced {len(synced)} commands.')
      os._exit(0)
    if(commandLineArgs.updatecompetitorrole):
      print('Updating competitor role...')
      await self.updateCompetitorRole()
      print('Competitor role updated')
      os._exit(0)
    if(commandLineArgs.setupserver):
      response = input('Are you sure you want to start the server setup process? This will create categories/channels/roles for every team and assign roles to players (Y/N): ')
      if(response.lower() == 'y'):
        print('Starting server setup...')
        await self.setUpServer()
        print('Server setup completed')
        os._exit(0)
      else:
        print('Exiting...')
        os._exit(0)
    if(commandLineArgs.teardownserver):
      response = input('Are you sure you want to DELETE ALL THE TEAM CHANNELS AND ROLES? This is very dangerous (Y/N): ')
      if(response.lower() == 'y'):
        print('Starting server teardown...')
        await self.tearDownServer()
        print('Server teardown completed')
        os._exit(0)
      else:
        print('Exiting...')
        os._exit(0)
  
  '''
  Populates instance variables coming from the bingo info sheet
  '''
  def loadBingoInfo(self):
    print('Loading bingo info...')
    guild = self.bot.get_guild(self.guildId)
    channels = guild.channels
    self.discordUserTeams = {}
    self.discordUserRSNs = {}
    self.teamSubmissionChannels = {}
    self.monsters = self.googleSheetClient.getListFromBingoInfoSheet('Monsters')
    self.clogItems = self.googleSheetClient.getListFromBingoInfoSheet('Collection Log Items')
    teamRosters = self.googleSheetClient.getTeamRosters()
    teamInfo = self.googleSheetClient.getTeamInfo()
    for teamName in teamRosters:
      teamTag = teamInfo[teamName]['tag']
      teamBotSubmissionChannelName = teamTag.lower() + '-bot-submissions'
      for channel in channels:
        if(channel.name == teamBotSubmissionChannelName):
          self.teamSubmissionChannels[teamName] = channel
      if(teamName not in self.teamSubmissionChannels):
        print('Could not find channel named ' + teamBotSubmissionChannelName + '. The server might not have been set up correctly. Exiting...')
        os._exit(1)
      for player in teamRosters[teamName]:
        self.discordUserRSNs[player['discordName']] = player['rsn']
        self.discordUserTeams[player['discordName']] = teamName
  
  '''
  Registers slash command callbacks to the bot
  '''
  def registerCommands(self):

    # Set up monster/clog autocomplete callbacks
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
    
    # Set up dynamically-generated option list for challenges
    challenges = self.googleSheetClient.getListFromBingoInfoSheet('Challenges')

    # Register commands
    @self.bot.tree.command(name='submit_monster_killcount', description='Submit a monster killcount for the bingo!')
    @app_commands.autocomplete(monster=monster_autocomplete)
    async def submit_monster_killcount(interaction: Interaction, screenshot: Attachment, monster: str, kc: int):
      await self.checkForValidPlayer(interaction)
      if(kc < 0):
        raise errors.BingoUserError('KC cannot be negative')
      if(monster not in self.monsters):
        raise errors.BingoUserError('Invalid monster name (make sure to click on the autocomplete option)')
      request = approvalrequest.ApprovalRequest(self, interaction, f'{kc} KC of {monster}')
      await self.requestApproval(request)
      responseText = 'Request received:\n'
      responseText += str(request)
      await interaction.response.send_message(responseText)

    @self.bot.tree.command(name='submit_collection_log', description='Submit a collection log item for the bingo! (Make sure the drop is in the screenshot)')
    @app_commands.autocomplete(item=clog_autocomplete)
    async def submit_collection_log(interaction: Interaction, screenshot: Attachment, item: str):
      await self.checkForValidPlayer(interaction)
      if(item not in self.clogItems):
        raise errors.BingoUserError('Invalid item name (make sure to click on the autocomplete option)')
      request = approvalrequest.ApprovalRequest(self, interaction, f'Collection log item "{item}"')
      await self.requestApproval(request)
      responseText = 'Request received:\n'
      responseText += str(request)
      await interaction.response.send_message(responseText)

    @self.bot.tree.command(name='submit_pest_control', description='Submit your pest control games for the bingo! (All difficulties added together)')
    async def submit_pest_control(interaction: Interaction, screenshot: Attachment, total_games: int):
      await self.checkForValidPlayer(interaction)
      if(total_games < 0):
        raise errors.BingoUserError('Total games cannot be negative')
      request = approvalrequest.ApprovalRequest(self, interaction, f'{total_games} games of pest control')
      await self.requestApproval(request)
      responseText = 'Request received:\n'
      responseText += str(request)
      await interaction.response.send_message(responseText)

    @self.bot.tree.command(name='submit_lms', description='Submit your LMS kills for the bingo!')
    async def submit_lms(interaction: Interaction, screenshot: Attachment, kills: int):
      await self.checkForValidPlayer(interaction)
      if(kills < 0):
        raise errors.BingoUserError('Kills cannot be negative')
      request = approvalrequest.ApprovalRequest(self, interaction, f'{kills} kills in LMS')
      await self.requestApproval(request)
      responseText = 'Request received:\n'
      responseText += str(request)
      await interaction.response.send_message(responseText)

    @self.bot.tree.command(name='submit_mta', description='Submit your MTA points for the bingo!')
    async def submit_mta(interaction: Interaction, screenshot: Attachment, alchemy_points: int, graveyard_points: int, enchanting_points: int, telekinetic_points: int):
      await self.checkForValidPlayer(interaction)
      if(alchemy_points < 0 or graveyard_points < 0 or enchanting_points < 0 or telekinetic_points < 0):
        raise errors.BingoUserError('Points cannot be negative')
      request = approvalrequest.ApprovalRequest(self, interaction, f'{alchemy_points}/{graveyard_points}/{enchanting_points}/{telekinetic_points} MTA points')
      await self.requestApproval(request)
      responseText = 'Request received:\n'
      responseText += str(request)
      await interaction.response.send_message(responseText)

    @self.bot.tree.command(name='submit_tithe_farm', description='Submit your tithe farm points for the bingo!')
    async def submit_tithe_farm(interaction: Interaction, screenshot: Attachment, points: int):
      await self.checkForValidPlayer(interaction)
      if(points < 0):
        raise errors.BingoUserError('Points cannot be negative')
      request = approvalrequest.ApprovalRequest(self, interaction, f'{points} tithe farm points')
      await self.requestApproval(request)
      responseText = 'Request received:\n'
      responseText += str(request)
      await interaction.response.send_message(responseText)

    @self.bot.tree.command(name='submit_farming_contracts', description='Submit your farming contracts for the bingo!')
    async def submit_farming_contracts(interaction: Interaction, screenshot: Attachment, contracts: int):
      await self.checkForValidPlayer(interaction)
      if(contracts < 0):
        raise errors.BingoUserError('Contracts cannot be negative')
      request = approvalrequest.ApprovalRequest(self, interaction, f'{contracts} farming contracts')
      await self.requestApproval(request)
      responseText = 'Request received:\n'
      responseText += str(request)
      await interaction.response.send_message(responseText)

    @self.bot.tree.command(name='submit_barbarian_assault', description='Submit your BA points for the bingo!')
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
      await self.checkForValidPlayer(interaction)
      for param in submit_barbarian_assault.parameters:
        argName = param.name
        argValue = locals()[argName]
        if(isinstance(argValue, int) and argValue < 0):
          raise errors.BingoUserError('BA arguments cannot be negative')
        if('level' in argName and (argValue < 1 or argValue > 5)):
          raise errors.BingoUserError('BA levels must be 1-5')
      request = approvalrequest.ApprovalRequest(self, interaction, 'BA points')
      await self.requestApproval(request)
      responseText = 'Request received:\n'
      responseText += str(request)
      await interaction.response.send_message(responseText)

    @self.bot.tree.command(name='submit_challenge', description='Submit your challenge times for the bingo! (Make sure to have precise timing enabled.)')
    async def submit_challenge(interaction: Interaction, screenshot: Attachment, minutes: int, seconds: int, tenths_of_seconds: int, challenge: Literal[tuple(challenges)]): # type: ignore - Tuple technically works for a Literal but isn't "proper"
      await self.checkForValidPlayer(interaction)
      if(minutes < 0 or seconds < 0 or tenths_of_seconds < 0):
        raise errors.BingoUserError('Times cannot be negative')
      if(tenths_of_seconds > 9):
        raise errors.BingoUserError('tenths_of_seconds cannot be greater than 9')
      request = approvalrequest.ApprovalRequest(self, interaction, "{0} time of {1:0>2}:{2:0>2}.{3}".format(challenge, minutes, seconds, tenths_of_seconds))
      await self.requestApproval(request)
      responseText = 'Request received:\n'
      responseText += str(request)
      await interaction.response.send_message(responseText)

  '''
  Registers an error handler callback to the bot
  '''
  def registerErrorHandler(self):
    @self.bot.tree.error
    async def handleCommandErrors(interaction, error):
      if(isinstance(error.original, errors.BingoUserError)):
        await interaction.response.send_message(f'Error: {str(error.original)}')
      else:
        logging.error('Error', exc_info=error)
        request = approvalrequest.ApprovalRequest(self, interaction)
        await self.sendErrorMessageToErrorChannel(interaction, request, error)

  '''
  Registers an interaction hook callback to the bot
  '''
  def registerInteractionHook(self):
    @self.bot.event
    async def on_interaction(interaction):
      data = interaction.data
      if(interaction.type == InteractionType.component and data['component_type'] == 2): # This is a button click interaction
        # Parse the ApprovalRequest out of the message contents
        message = interaction.message.content
        requestJson = None
        for line in message.splitlines():
          if(line.startswith('Request json: `')): # This is the line that has our json on it
            requestJson = line.replace('Request json: ', '').replace('`', '')
            break
        if(requestJson == None):
          return # Not an approval request message
        if(data['custom_id'] == 'approve'): # User has clicked the "Approve" button
          request = approvalrequest.fromJson(requestJson, self)
          logging.info('Request approved by ' + interaction.user.name + ':')
          logging.info(requestJson)
          await interaction.message.delete()
          submissionLogChannel = self.bot.get_channel(self.submissionLogChannelId)
          await submissionLogChannel.send(f'Request approved by {interaction.user.display_name}\n' + str(request))
          submissionsChannel = self.teamSubmissionChannels[request.team]
          await submissionsChannel.send(f'<@{request.user.id}> Your {request.shortDesc} has been approved by {interaction.user.display_name}')
          try:
            await request.approve()
          except Exception as error:
            logging.error('Error', exc_info=error)
            await self.sendErrorMessageToErrorChannel(interaction, request, error)
            return
        if(data['custom_id'] == 'deny'): # User has clicked the "Deny" button
          request = approvalrequest.fromJson(requestJson, self)
          logging.info('Request denied by ' + interaction.user.name + ':')
          logging.info(requestJson)
          await interaction.message.delete()
          submissionLogChannel = self.bot.get_channel(self.submissionLogChannelId)
          await submissionLogChannel.send(f'Request denied by {interaction.user.display_name}\n' + str(request))
          submissionsChannel = self.teamSubmissionChannels[request.team]
          await submissionsChannel.send(f'<@{request.user.id}> Your {request.shortDesc} has been denied by {interaction.user.display_name}')
        else: # Something unexpected
          pass

  '''
  Registers a ready hook callback to the bot
  '''
  def registerReadyHook(self, commandLineArgs):
    @self.bot.event
    async def on_ready():
      print(f'Logged in as {self.bot.user.name}')

      await self.handleAlternateRunCommands(commandLineArgs)
      self.loadBingoInfo()

      print('Ready to accept commands!')
  
  '''
  Connects the bot to the server to begin accepting commands
  '''
  def start(self):
    self.bot.run(self.token)