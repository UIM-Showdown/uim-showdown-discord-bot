import discord
from approvalhandlers import TestSubmitKCHandler

# Register approval handlers here
handlers = {}
handlers['test_submit_kc'] = TestSubmitKCHandler()

class ApprovalRequest():
  
  def __init__(self, ctx: discord.Interaction):
    self.user = ctx.user.name
    self.commandName = ctx.command.name
    self.params = {}
    self.approvalHandler = handlers[self.commandName]
    for param in ctx.data['options']:
      if(param['name'] == 'screenshot'):
        self.params[param['name']] = ctx.data['resolved']['attachments'][param['value']]['url']
      else:
        self.params[param['name']] = str(param['value'])

  def __str__(self):
    requestText = 'User: ' + self.user + '\n'
    requestText += 'Command: /' + self.commandName
    for paramName in self.params:
      requestText += '\n' + paramName + ': ' + self.params[paramName]
    return requestText

  def approve(self):
    self.approvalHandler.requestApproved(self)
  
  def deny(self):
    print('Denied request: \n' + str(self))