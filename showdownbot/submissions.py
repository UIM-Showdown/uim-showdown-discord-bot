import logging
import json
from discord import Interaction

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
  jsonObject['ids'] = submission.ids
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
    params = jsonObject['params'],
    ids = jsonObject['ids']
  )

# Represents a submission made via the bot
class Submission():
  def __init__(self, showdownBot = None, interaction: Interaction = None, ids = None, shortDesc = None, user = None, rsn = None, team = None, commandName = None, params = None):
    if(interaction):
      self.showdownBot = showdownBot
      self.ids = ids
      self.user = interaction.user
      self.rsn = self.showdownBot.discordUserRSNs[self.user.name]
      self.team = self.showdownBot.discordUserTeams[self.user.name]
      self.commandName = interaction.command.name
      self.params = {}
      self.shortDesc = shortDesc
      for param in interaction.data['options']:
        if('screenshot' in param['name'].lower()):
          self.params[param['name']] = interaction.data['resolved']['attachments'][param['value']]['url']
        else:
          self.params[param['name']] = str(param['value'])
    else: # Creating from raw params, i.e. a previously serialized json string
      self.showdownBot = showdownBot
      self.ids = ids
      self.user = user
      self.rsn = rsn
      self.team = team
      self.commandName = commandName
      self.params = params
      self.shortDesc = shortDesc

  def __str__(self):
    submissionText = 'IDs: ' + str(self.ids) + '\n'
    submissionText += 'RSN: ' + self.rsn + '\n'
    submissionText += 'Team: ' + self.team + '\n'
    submissionText += 'Command: /' + self.commandName
    for paramName in self.params:
      submissionText += '\n' + paramName + ': ' + self.params[paramName]
    if('Record of' in self.shortDesc):
      submissionText += '\n' + f'Temple link to verify record: https://templeosrs.com/player/overview.php?player={self.rsn.lower()}&skill={self.params['record'].split('|')[0].title()}'
    submissionText += '\n' + 'Submission json: `' + toJson(self) + '`'
    return submissionText