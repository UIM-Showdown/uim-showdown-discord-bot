from abc import ABC, abstractmethod
from google.oauth2 import service_account
from googleapiclient.discovery import build


# ABC for approval handlers. The submissionApproved method on the extending class should 
# handle all bot-external actions to take upon a submission's approval (e.g. modifying a 
# spreadsheet)
class ApprovalHandler(ABC):

  @abstractmethod
  async def submissionApproved(self, submission):
    pass

class BAHandler(ApprovalHandler):
  async def submissionApproved(self, submission):
    submission.showdownBot.googleSheetClient.appendSubmission(
      'BAPointDump!A:K',
      [
        submission.user.name,
        submission.team,
        submission.params['blackboard_screenshot'],
        submission.params['clog_screenshot'],
        submission.params['attacker_points'],
        submission.params['defender_points'],
        submission.params['collector_points'],
        submission.params['healer_points'],
        submission.params['attacker_level'],
        submission.params['defender_level'],
        submission.params['collector_level'],
        submission.params['healer_level'],
        submission.params['high_gambles'],
        submission.params['hats'],
        int(submission.params['torso']) + int(submission.params['skirt']),
        submission.params['gloves'],
        submission.params['boots']
      ]
    )

class ChallengeHandler(ApprovalHandler):
  async def submissionApproved(self, submission):
    submission.showdownBot.googleSheetClient.appendSubmission(
      'ChallengesDump!A:F',
      [
        submission.user.name,
        submission.params['challenge'],
        '{0:0>2}:{1:0>2}.{2}'.format(submission.params['minutes'], submission.params['seconds'], submission.params['tenths_of_seconds']),
        None,
        submission.team,
        submission.params['screenshot']
      ]
    )

class ClogHandler(ApprovalHandler):
  async def submissionApproved(self, submission):
    submission.showdownBot.googleSheetClient.appendSubmission(
      'CLogBotDump!A:D',
      [
        submission.user.name,
        submission.team,
        submission.params['item'],
        submission.params['screenshot']
      ]
    )

class FarmingContractsHandler(ApprovalHandler):
  async def submissionApproved(self, submission):
    submission.showdownBot.googleSheetClient.appendSubmission(
      'FarmingDump!A:E',
      [
        submission.user.name,
        'Farming Contracts',
        submission.params['contracts'],
        submission.team,
        submission.params['screenshot']
      ]
    )

class LMSHandler(ApprovalHandler):
  async def submissionApproved(self, submission):
    submission.showdownBot.googleSheetClient.appendSubmission(
      'MinigameBotDump!A:E',
      [
        submission.user.name,
        'LMS Kills',
        submission.params['kills'],
        submission.team,
        submission.params['screenshot']
      ]
    )

class MonsterKCHandler(ApprovalHandler):
  async def submissionApproved(self, submission):
    submission.showdownBot.googleSheetClient.appendSubmission(
      'MonKCBotDump!A:E',
      [
        submission.user.name,
        submission.params['monster'],
        submission.params['kc'],
        submission.team,
        submission.params['screenshot']
      ]
    )

class MTAHandler(ApprovalHandler):
  async def submissionApproved(self, submission):
    submission.showdownBot.googleSheetClient.appendSubmission(
      'MinigameBotDump!A:E',
      [
        submission.user.name,
        'MTA: Alchemists Playground',
        submission.params['alchemy_points'],
        submission.team,
        submission.params['screenshot']
      ]
    )
    submission.showdownBot.googleSheetClient.appendSubmission(
      'MinigameBotDump!A:E',
      [
        submission.user.name,
        'MTA: Creature Graveyard',
        submission.params['graveyard_points'],
        submission.team,
        submission.params['screenshot']
      ]
    )
    submission.showdownBot.googleSheetClient.appendSubmission(
      'MinigameBotDump!A:E',
      [
        submission.user.name,
        'MTA: Enchanting Chamber',
        submission.params['enchanting_points'],
        submission.team,
        submission.params['screenshot']
      ]
    )
    submission.showdownBot.googleSheetClient.appendSubmission(
      'MinigameBotDump!A:E',
      [
        submission.user.name,
        'MTA: Telekinetic Theatre',
        submission.params['telekinetic_points'],
        submission.team,
        submission.params['screenshot']
      ]
    )

class PestControlHandler(ApprovalHandler):
  async def submissionApproved(self, submission):
    submission.showdownBot.googleSheetClient.appendSubmission(
      'MinigameBotDump!A:E',
      [
        submission.user.name,
        'Pest Control',
        submission.params['total_games'],
        submission.team,
        submission.params['screenshot']
      ]
    )

class TitheFarmHandler(ApprovalHandler):
  async def submissionApproved(self, submission):
    submission.showdownBot.googleSheetClient.appendSubmission(
      'FarmingDump!A:E',
      [
        submission.user.name,
        'Tithe Farm',
        submission.params['points'],
        submission.team,
        submission.params['screenshot']
      ]
    )