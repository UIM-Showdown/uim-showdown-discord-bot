from abc import ABC, abstractmethod
from google.oauth2 import service_account
from googleapiclient.discovery import build


# ABC for approval handlers. The requestApproved method on the extending class should 
# handle all bot-external actions to take upon a request's approval (e.g. modifying a 
# spreadsheet)
class ApprovalHandler(ABC):

  @abstractmethod
  async def requestApproved(self, request):
    pass

class BAHandler(ApprovalHandler):
  async def requestApproved(self, request):
    request.showdownBot.googleSheetClient.appendSubmission(
      'BAPointDump!A:K',
      [
        request.user.name,
        request.team,
        request.params['blackboard_screenshot'],
        request.params['clog_screenshot'],
        request.params['attacker_points'],
        request.params['defender_points'],
        request.params['collector_points'],
        request.params['healer_points'],
        request.params['attacker_level'],
        request.params['defender_level'],
        request.params['collector_level'],
        request.params['healer_level'],
        request.params['high_gambles'],
        request.params['hats'],
        int(request.params['torso']) + int(request.params['skirt']),
        request.params['gloves'],
        request.params['boots']
      ]
    )

class ChallengeHandler(ApprovalHandler):
  async def requestApproved(self, request):
    request.showdownBot.googleSheetClient.appendSubmission(
      'ChallengesDump!A:F',
      [
        request.user.name,
        request.params['challenge'],
        '{0:0>2}:{1:0>2}.{2}'.format(request.params['minutes'], request.params['seconds'], request.params['tenths_of_seconds']),
        None,
        request.team,
        request.params['screenshot']
      ]
    )

class ClogHandler(ApprovalHandler):
  async def requestApproved(self, request):
    request.showdownBot.googleSheetClient.appendSubmission(
      'CLogBotDump!A:D',
      [
        request.user.name,
        request.team,
        request.params['item'],
        request.params['screenshot']
      ]
    )

class FarmingContractsHandler(ApprovalHandler):
  async def requestApproved(self, request):
    request.showdownBot.googleSheetClient.appendSubmission(
      'FarmingDump!A:E',
      [
        request.user.name,
        'Farming Contracts',
        request.params['contracts'],
        request.team,
        request.params['screenshot']
      ]
    )

class LMSHandler(ApprovalHandler):
  async def requestApproved(self, request):
    request.showdownBot.googleSheetClient.appendSubmission(
      'MinigameBotDump!A:E',
      [
        request.user.name,
        'LMS Kills',
        request.params['kills'],
        request.team,
        request.params['screenshot']
      ]
    )

class MonsterKCHandler(ApprovalHandler):
  async def requestApproved(self, request):
    request.showdownBot.googleSheetClient.appendSubmission(
      'MonKCBotDump!A:E',
      [
        request.user.name,
        request.params['monster'],
        request.params['kc'],
        request.team,
        request.params['screenshot']
      ]
    )

class MTAHandler(ApprovalHandler):
  async def requestApproved(self, request):
    request.showdownBot.googleSheetClient.appendSubmission(
      'MinigameBotDump!A:E',
      [
        request.user.name,
        'MTA: Alchemists Playground',
        request.params['alchemy_points'],
        request.team,
        request.params['screenshot']
      ]
    )
    request.showdownBot.googleSheetClient.appendSubmission(
      'MinigameBotDump!A:E',
      [
        request.user.name,
        'MTA: Creature Graveyard',
        request.params['graveyard_points'],
        request.team,
        request.params['screenshot']
      ]
    )
    request.showdownBot.googleSheetClient.appendSubmission(
      'MinigameBotDump!A:E',
      [
        request.user.name,
        'MTA: Enchanting Chamber',
        request.params['enchanting_points'],
        request.team,
        request.params['screenshot']
      ]
    )
    request.showdownBot.googleSheetClient.appendSubmission(
      'MinigameBotDump!A:E',
      [
        request.user.name,
        'MTA: Telekinetic Theatre',
        request.params['telekinetic_points'],
        request.team,
        request.params['screenshot']
      ]
    )

class PestControlHandler(ApprovalHandler):
  async def requestApproved(self, request):
    request.showdownBot.googleSheetClient.appendSubmission(
      'MinigameBotDump!A:E',
      [
        request.user.name,
        'Pest Control',
        request.params['total_games'],
        request.team,
        request.params['screenshot']
      ]
    )

class TitheFarmHandler(ApprovalHandler):
  async def requestApproved(self, request):
    request.showdownBot.googleSheetClient.appendSubmission(
      'FarmingDump!A:E',
      [
        request.user.name,
        'Tithe Farm',
        request.params['points'],
        request.team,
        request.params['screenshot']
      ]
    )