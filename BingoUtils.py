import discord
from discord import ui
import configparser
from Buttons import ApproveButton, DenyButton
from ApprovalRequest import ApprovalRequest

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