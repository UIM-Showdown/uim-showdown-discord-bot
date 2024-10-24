from discord import ui, ButtonStyle, Interaction

class ApproveButton(ui.Button):
  def __init__(self, approvalRequest, showdownBot):
    self.showdownBot = showdownBot
    self.approvalRequest = approvalRequest
    super().__init__(style=ButtonStyle.success, custom_id='approve', label='Approve')

  async def callback(self, ctx: Interaction):
    self.approvalRequest.approve()
    await ctx.message.edit(view = ui.View())
    await ctx.response.send_message('Request approved')
    team = self.showdownBot.discordUserTeams[ctx.user.name]
    submissionsChannel = self.showdownBot.bot.get_channel(self.showdownBot.teamSubmissionChannels[team])
    await submissionsChannel.send(f'<@{self.approvalRequest.user.id}> Your {self.approvalRequest.shortDesc} has been approved')

class DenyButton(ui.Button):
  def __init__(self, approvalRequest, showdownBot):
    self.showdownBot = showdownBot
    self.approvalRequest = approvalRequest
    super().__init__(style=ButtonStyle.danger, custom_id='deny', label='Deny')

  async def callback(self, ctx: Interaction):
    await ctx.message.edit(view = ui.View())
    await ctx.response.send_message('Request denied')
    team = self.showdownBot.discordUserTeams[ctx.user.name]
    submissionsChannel = self.showdownBot.bot.get_channel(self.showdownBot.teamSubmissionChannels[team])
    await submissionsChannel.send(f'<@{self.approvalRequest.user.id}> Your {self.approvalRequest.shortDesc} has been denied')