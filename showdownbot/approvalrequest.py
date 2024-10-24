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

# Represents an approval request
class ApprovalRequest():
  def __init__(self, ctx: Interaction, shortDesc = None):
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