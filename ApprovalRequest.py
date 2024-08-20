import discord
from approvalhandlers import *

# Register approval handlers here
handlers = {}
handlers['submit_monster_killcount'] = monsterkchandler.MonsterKCHandler()
handlers['submit_collection_log'] = cloghandler.ClogHandler()
handlers['submit_pest_control'] = pestcontrolhandler.PestControlHandler()
handlers['submit_lms'] = lmshandler.LMSHandler()
handlers['submit_mta'] = mtahandler.MTAHandler()
handlers['submit_tithe_farm'] = tithefarmhandler.TitheFarmHandler()
handlers['submit_farming_contracts'] = farmingcontractshandler.FarmingContractsHandler()
handlers['submit_barbarian_assault'] = bahandler.BAHandler()
handlers['submit_challenge'] = challengehandler.ChallengeHandler()

# Represents an approval request
class ApprovalRequest():
  def __init__(self, ctx: discord.Interaction, shortDesc = None):
    self.user = ctx.user
    self.commandName = ctx.command.name
    self.params = {}
    self.approvalHandler = handlers[self.commandName]
    self.shortDesc = shortDesc
    for param in ctx.data['options']:
      if('screenshot' in param['name'].lower()):
        self.params[param['name']] = ctx.data['resolved']['attachments'][param['value']]['url']
      else:
        self.params[param['name']] = str(param['value'])

  def __str__(self):
    requestText = 'User: ' + self.user.name + '\n'
    requestText += 'Command: /' + self.commandName
    for paramName in self.params:
      requestText += '\n' + paramName + ': ' + self.params[paramName]
    return requestText

  def approve(self):
    self.approvalHandler.requestApproved(self)
  
  def deny(self):
    print('Denied request: \n' + str(self))