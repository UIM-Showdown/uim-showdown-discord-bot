import discord
from discord import ui

class ApproveButton(ui.Button):
  def __init__(self, approvalRequest):
    self.approvalRequest = approvalRequest
    super().__init__(style=discord.ButtonStyle.success, custom_id='approve', label='Approve')

  async def callback(self, ctx: discord.Interaction):
    self.approvalRequest.approve()
    await ctx.message.edit(view = ui.View())
    await ctx.response.send_message('Request approved')

class DenyButton(ui.Button):
  def __init__(self, approvalRequest):
    self.approvalRequest = approvalRequest
    super().__init__(style=discord.ButtonStyle.danger, custom_id='deny', label='Deny')

  async def callback(self, ctx: discord.Interaction):
    self.approvalRequest.deny()
    await ctx.message.edit(view = ui.View())
    await ctx.response.send_message('Request denied')