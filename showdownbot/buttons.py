from discord import ui, ButtonStyle, Interaction
import logging

class ApproveButton(ui.Button):
  def __init__(self, approvalRequest, showdownBot):
    self.showdownBot = showdownBot
    self.approvalRequest = approvalRequest
    super().__init__(style=ButtonStyle.success, custom_id='approve', label='Approve')

  async def callback(self, ctx: Interaction):
    logging.info('Request approved by ' + ctx.user.name + ':')
    logging.info(str(self.approvalRequest))
    await ctx.message.edit(view = ui.View())
    await ctx.response.send_message('Request approved')
    team = self.showdownBot.discordUserTeams[self.approvalRequest.user.name]
    submissionsChannel = self.showdownBot.teamSubmissionChannels[team]
    await submissionsChannel.send(f'<@{self.approvalRequest.user.id}> Your {self.approvalRequest.shortDesc} has been approved by {ctx.user.display_name}')
    try:
      await self.approvalRequest.approve()
    except Exception as error:
      logging.error('Error', exc_info=error)
      await self.showdownBot.sendErrorMessageToErrorChannel(ctx, self.approvalRequest, error)
      return

class DenyButton(ui.Button):
  def __init__(self, approvalRequest, showdownBot):
    self.showdownBot = showdownBot
    self.approvalRequest = approvalRequest
    super().__init__(style=ButtonStyle.danger, custom_id='deny', label='Deny')

  async def callback(self, ctx: Interaction):
    logging.info('Request denied by ' + ctx.user.name + ':')
    logging.info(str(self.approvalRequest))
    await ctx.message.edit(view = ui.View())
    await ctx.response.send_message('Request denied')
    team = self.showdownBot.discordUserTeams[self.approvalRequest.user.name]
    submissionsChannel = self.showdownBot.teamSubmissionChannels[team]
    await submissionsChannel.send(f'<@{self.approvalRequest.user.id}> Your {self.approvalRequest.shortDesc} has been denied by {ctx.user.display_name}')