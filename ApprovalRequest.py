import discord
from approvalhandlers import MonsterKCHandler, ClogHandler, PestControlHandler, LMSHandler

# Register approval handlers here
handlers = {}
handlers['submit_monster_killcount'] = MonsterKCHandler()
handlers['submit_collection_log'] = ClogHandler()
handlers['submit_pest_control'] = PestControlHandler()
handlers['submit_lms'] = LMSHandler()

# Represents an approval request
class ApprovalRequest():
  def __init__(self, ctx: discord.Interaction, shortDesc = None):
    self.user = ctx.user
    self.commandName = ctx.command.name
    self.params = {}
    self.approvalHandler = handlers[self.commandName]
    self.shortDesc = shortDesc
    for param in ctx.data['options']:
      if(param['name'] == 'screenshot'):
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