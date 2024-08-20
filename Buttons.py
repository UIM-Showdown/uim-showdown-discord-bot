import discord
from discord import ui
import BingoUtils

class ApproveButton(ui.Button):
  def __init__(self, approvalRequest, bot):
    self.bot = bot
    self.approvalRequest = approvalRequest
    super().__init__(style=discord.ButtonStyle.success, custom_id='approve', label='Approve')

  async def callback(self, ctx: discord.Interaction):
    self.approvalRequest.approve()
    await ctx.message.edit(view = ui.View())
    await ctx.response.send_message('Request approved')
    submissionsChannel = self.bot.get_channel(BingoUtils.submissionsChannelId)
    await submissionsChannel.send(f'<@{self.approvalRequest.user.id}> Your {self.approvalRequest.shortDesc} has been approved')

class DenyButton(ui.Button):
  def __init__(self, approvalRequest, bot):
    self.bot = bot
    self.approvalRequest = approvalRequest
    super().__init__(style=discord.ButtonStyle.danger, custom_id='deny', label='Deny')

  async def callback(self, ctx: discord.Interaction):
    self.approvalRequest.deny()
    await ctx.message.edit(view = ui.View())
    await ctx.response.send_message('Request denied')
    submissionsChannel = self.bot.get_channel(BingoUtils.submissionsChannelId)
    await submissionsChannel.send(f'<@{self.approvalRequest.user.id}> Your {self.approvalRequest.shortDesc} has been denied')