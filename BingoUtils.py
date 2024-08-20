import discord
from discord import ui
import configparser
from Buttons import ApproveButton, DenyButton

# Load properties
config = configparser.ConfigParser()
config.read('config.ini')
bingoProperties = config['BingoProperties']
token = bingoProperties['token']
approvalsChannelId = int(bingoProperties['approvalsChannelId'])
errorsChannelId = int(bingoProperties['errorsChannelId'])
submissionsChannelId = int(bingoProperties['submissionsChannelId'])

class BingoUserError(Exception):

  def __init__(self, message):
    self.message = message
    
  def __str__(self):
    return self.message

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

def getAttachmentsFromContext(ctx):
  return list(ctx.data['resolved']['attachments'].values())

async def handleCommandError(bot, ctx, error):
  if(isinstance(error.original, BingoUserError)):
    await ctx.response.send_message(f'Error: {str(error.original)}')
  else:
    request = ApprovalRequest(ctx)
    channel = bot.get_channel(errorsChannelId)
    errorText = 'Unexpected error during processing of a command:\n'
    errorText += str(request) + '\n'
    errorText += f'Error: {str(error.original)}'
    await channel.send(errorText)
    await ctx.response.send_message('Unexpected error: The admins have been notified to review this error')

async def requestApproval(bot, request):
  channel = bot.get_channel(approvalsChannelId)
  requestText = 'New approval requested:\n'
  requestText += str(request)
  view = ui.View()
  denyButton = ui.Button(style=discord.ButtonStyle.danger, custom_id='deny', label='Deny')
  view.add_item(ApproveButton(request))
  view.add_item(DenyButton(request))
  await bot.get_channel(approvalsChannelId).send(requestText, view=view)