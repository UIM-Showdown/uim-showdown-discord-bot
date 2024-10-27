from abc import ABC, abstractmethod
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import time


# ABC for approval handlers. The requestApproved method on the extending class should 
# handle all bot-external actions to take upon a request's approval (e.g. modifying a 
# spreadsheet)
class ApprovalHandler(ABC):

  @abstractmethod
  async def requestApproved(self, request):
    pass

  def appendToGoogleSheet(self, range, row, spreadsheetId):
    creds = service_account.Credentials.from_service_account_file('google-creds.json', scopes=['https://www.googleapis.com/auth/spreadsheets'])
    with build('sheets', 'v4', credentials=creds) as service:
      spreadsheets = service.spreadsheets()
      spreadsheets.values().append(
        spreadsheetId = spreadsheetId,
        range = range,
        body = {'majorDimension': 'ROWS', 'values': [row]},
        valueInputOption = 'USER_ENTERED'
      ).execute()

class BAHandler(ApprovalHandler):
  async def requestApproved(self, request):
    self.appendToGoogleSheet(
      'BAPointDump!A:K',
      [
        request.user.name,
        request.team,
        request.params['blackboard_screenshot'],
        request.params['attacker_points'],
        request.params['defender_points'],
        request.params['collector_points'],
        request.params['healer_points'],
        request.params['attacker_level'],
        request.params['defender_level'],
        request.params['collector_level'],
        request.params['healer_level']
      ],
      request.spreadsheetId
    )
    self.appendToGoogleSheet(
      'BAColLogDump!A:K',
      [
        request.user.name,
        request.team,
        request.params['clog_screenshot'],
        request.params['high_gambles'],
        request.params['hats'],
        int(request.params['torso']) + int(request.params['skirt']),
        request.params['gloves'],
        request.params['boots']
      ],
      request.spreadsheetId
    )

class ChallengeHandler(ApprovalHandler):
  async def requestApproved(self, request):
    self.appendToGoogleSheet(
      'ChallengesDump!A:F',
      [
        request.user.name,
        request.params['challenge'],
        '{0:0>2}:{1:0>2}.{2}'.format(request.params['minutes'], request.params['seconds'], request.params['tenths_of_seconds']),
        None,
        request.team,
        request.params['screenshot']
      ],
      request.spreadsheetId
    )

class ClogHandler(ApprovalHandler):
  async def requestApproved(self, request):
    self.appendToGoogleSheet(
      'CLogBotDump!A:D',
      [
        request.user.name,
        request.team,
        request.params['item'],
        request.params['screenshot']
      ],
      request.spreadsheetId
    )

class FarmingContractsHandler(ApprovalHandler):
  async def requestApproved(self, request):
    self.appendToGoogleSheet(
      'FarmingDump!A:E',
      [
        request.user.name,
        'Farming Contracts',
        request.params['contracts'],
        request.team,
        request.params['screenshot']
      ],
      request.spreadsheetId
    )

class LMSHandler(ApprovalHandler):
  async def requestApproved(self, request):
    self.appendToGoogleSheet(
      'MinigameBotDump!A:E',
      [
        request.user.name,
        'LMS Kills',
        request.params['kills'],
        request.team,
        request.params['screenshot']
      ],
      request.spreadsheetId
    )

class MonsterKCHandler(ApprovalHandler):
  async def requestApproved(self, request):
    self.appendToGoogleSheet(
      'MonKCBotDump!A:E',
      [
        request.user.name,
        request.params['monster'],
        request.params['kc'],
        request.team,
        request.params['screenshot']
      ],
      request.spreadsheetId
    )

class MTAHandler(ApprovalHandler):
  async def requestApproved(self, request):
    self.appendToGoogleSheet(
      'MinigameBotDump!A:E',
      [
        request.user.name,
        'MTA: Alchemists Playground',
        request.params['alchemy_points'],
        request.team,
        request.params['screenshot']
      ],
      request.spreadsheetId
    )
    self.appendToGoogleSheet(
      'MinigameBotDump!A:E',
      [
        request.user.name,
        'MTA: Creature Graveyard',
        request.params['graveyard_points'],
        request.team,
        request.params['screenshot']
      ],
      request.spreadsheetId
    )
    self.appendToGoogleSheet(
      'MinigameBotDump!A:E',
      [
        request.user.name,
        'MTA: Enchanting Chamber',
        request.params['enchanting_points'],
        request.team,
        request.params['screenshot']
      ],
      request.spreadsheetId
    )
    self.appendToGoogleSheet(
      'MinigameBotDump!A:E',
      [
        request.user.name,
        'MTA: Telekinetic Theatre',
        request.params['telekinetic_points'],
        request.team,
        request.params['screenshot']
      ],
      request.spreadsheetId
    )

class PestControlHandler(ApprovalHandler):
  async def requestApproved(self, request):
    self.appendToGoogleSheet(
      'MinigameBotDump!A:E',
      [
        request.user.name,
        'Pest Control',
        request.params['total_games'],
        request.team,
        request.params['screenshot']
      ],
      request.spreadsheetId
    )

class TitheFarmHandler(ApprovalHandler):
  async def requestApproved(self, request):
    self.appendToGoogleSheet(
      'FarmingDump!A:E',
      [
        request.user.name,
        'Tithe Farm',
        request.params['points'],
        request.team,
        request.params['screenshot']
      ],
      request.spreadsheetId
    )