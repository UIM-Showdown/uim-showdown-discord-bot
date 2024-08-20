import discord

class ApprovalRequest():
  
  def __init__(self, ctx: discord.Interaction):
    self.user = ctx.user.name
    self.commandName = ctx.command.name
    self.params = {}
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
    print('Approved request: \n' + str(self)) # Turn this into an abstract class and make this method abstract
  
  def deny(self):
    print('Denied request: \n' + str(self)) # Turn this into an abstract class and make this method abstract