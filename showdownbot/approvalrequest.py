import logging
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
  def __init__(self, showdownBot, ctx: Interaction, shortDesc = None):
    self.showdownBot = showdownBot
    self.user = ctx.user
    self.rsn = self.showdownBot.discordUserRSNs[self.user.name]
    self.team = self.showdownBot.discordUserTeams[self.user.name]
    self.commandName = ctx.command.name
    self.params = {}
    self.approvalHandler = handlers[self.commandName]
    self.shortDesc = shortDesc
    for param in ctx.data['options']:
      if('screenshot' in param['name'].lower()):
        self.params[param['name']] = ctx.data['resolved']['attachments'][param['value']]['url']
      else:
        self.params[param['name']] = str(param['value'])
    logging.info('Approval request created:')
    logging.info(self.__str__())

  def __str__(self):
    requestText = 'RSN: ' + self.rsn + '\n'
    requestText += 'Command: /' + self.commandName
    for paramName in self.params:
      requestText += '\n' + paramName + ': ' + self.params[paramName]
    return requestText

  async def approve(self):
    await self.approvalHandler.requestApproved(self)