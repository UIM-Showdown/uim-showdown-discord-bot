import logging
import json
from discord import Interaction
import showdownbot.approvalhandlers as approvalhandlers

# Register approval handlers here
handlers = {}
handlers['submit_monster_killcount'] = approvalhandlers.MonsterKCHandler()
handlers['submit_collection_log'] = approvalhandlers.ClogHandler()
handlers['submit_pest_control'] = approvalhandlers.PestControlHandler()
handlers['submit_lms'] = approvalhandlers.LMSHandler()
handlers['submit_mta'] = approvalhandlers.MTAHandler()
handlers['submit_tithe_farm'] = approvalhandlers.TitheFarmHandler()
handlers['submit_farming_contracts'] = approvalhandlers.FarmingContractsHandler()
handlers['submit_barbarian_assault'] = approvalhandlers.BAHandler()
handlers['submit_challenge'] = approvalhandlers.ChallengeHandler()

'''
Serializes a Submission to a json string
'''
def toJson(submission):
  jsonObject = {}
  jsonObject['user'] = submission.user.name
  jsonObject['rsn'] = submission.rsn
  jsonObject['team'] = submission.team
  jsonObject['commandName'] = submission.commandName
  jsonObject['params'] = submission.params
  jsonObject['shortDesc'] = submission.shortDesc
  return json.dumps(jsonObject)

'''
Deserializes a Submission from a json string
'''
def fromJson(jsonString, showdownBot):
  jsonObject = json.loads(jsonString)
  guild = showdownBot.bot.get_guild(showdownBot.guildId)
  user = guild.get_member_named(jsonObject['user'])
  return Submission(
    showdownBot = showdownBot,
    user = user,
    shortDesc = jsonObject['shortDesc'],
    rsn = jsonObject['rsn'],
    team = jsonObject['team'],
    commandName = jsonObject['commandName'],
    params = jsonObject['params']
  )

# Represents a submission made via the bot
class Submission():
  def __init__(self, showdownBot = None, interaction: Interaction = None, shortDesc = None, user = None, rsn = None, team = None, commandName = None, params = None):
    if(interaction):
      self.showdownBot = showdownBot
      self.user = interaction.user
      self.rsn = self.showdownBot.discordUserRSNs[self.user.name]
      self.team = self.showdownBot.discordUserTeams[self.user.name]
      self.commandName = interaction.command.name
      self.params = {}
      self.approvalHandler = handlers[self.commandName]
      self.shortDesc = shortDesc
      for param in interaction.data['options']:
        if('screenshot' in param['name'].lower()):
          self.params[param['name']] = interaction.data['resolved']['attachments'][param['value']]['url']
        else:
          self.params[param['name']] = str(param['value'])
    else: # Creating from raw params, i.e. a previously serialized json string
      self.showdownBot = showdownBot
      self.user = user
      self.rsn = rsn
      self.team = team
      self.commandName = commandName
      self.params = params
      self.approvalHandler = handlers[self.commandName]
      self.shortDesc = shortDesc

  def __str__(self):
    submissionText = 'RSN: ' + self.rsn + '\n'
    submissionText += 'Team: ' + self.team + '\n'
    submissionText += 'Command: /' + self.commandName
    for paramName in self.params:
      submissionText += '\n' + paramName + ': ' + self.params[paramName]
    submissionText += '\n' + 'Submission json: `' + toJson(self) + '`'
    return submissionText

  async def approve(self):
    await self.approvalHandler.submissionApproved(self)