from google.oauth2 import service_account
from googleapiclient.discovery import build

# Client for interacting with a Google sheet
class GoogleSheetClient():

  def __init__(self, submissionSheetId, bingoInfoSheetId):
    self.submissionSheetId = submissionSheetId
    self.bingoInfoSheetId = bingoInfoSheetId

  def appendSubmission(self, inputRange, data):
    creds = service_account.Credentials.from_service_account_file('google-creds.json', scopes=['https://www.googleapis.com/auth/spreadsheets'])
    with build('sheets', 'v4', credentials=creds) as service:
      spreadsheets = service.spreadsheets()
      spreadsheets.values().append(
        spreadsheetId = self.submissionSheetId,
        range = inputRange,
        body = {'majorDimension': 'ROWS', 'values': [data]},
        valueInputOption = 'USER_ENTERED'
      ).execute()

  def getTeamRosters(self):
    rosters = {}
    creds = service_account.Credentials.from_service_account_file('google-creds.json', scopes=['https://www.googleapis.com/auth/spreadsheets'])
    with build('sheets', 'v4', credentials=creds) as service:
      spreadsheets = service.spreadsheets()
      rows = spreadsheets.values().get(
        spreadsheetId = self.bingoInfoSheetId,
        range = 'Team Rosters!A:C'
      ).execute().get('values', [])
      for row in rows:
        if(row[0] == 'Discord Name' and row[1] == 'RSN' and row[2] == 'Team'):
          continue
        if(row[2] not in rosters):
          rosters[row[2]] = [{'discordName': row[0], 'rsn': row[1]}]
        else:
          rosters[row[2]].append({'discordName': row[0], 'rsn': row[1]})
    return rosters
  
  def getTeamInfo(self):
    teamInfo = {}
    creds = service_account.Credentials.from_service_account_file('google-creds.json', scopes=['https://www.googleapis.com/auth/spreadsheets'])
    with build('sheets', 'v4', credentials=creds) as service:
      spreadsheets = service.spreadsheets()
      rows = spreadsheets.values().get(
        spreadsheetId = self.bingoInfoSheetId,
        range = 'Team Info!A:C'
      ).execute().get('values', [])
      for row in rows:
        if(row[0] == 'Team Name' and row[1] == 'Tag' and row[2] == 'Color'):
          continue
        if(row[0] not in teamInfo):
          teamInfo[row[0]] = {'tag': row[1], 'color': row[2]}
        else:
          teamInfo[row[0]].append({'tag': row[1], 'color': row[2]})
    return teamInfo
  
  def getSignedUpDiscordMembers(self):
    signedUpDiscordMembers = []
    creds = service_account.Credentials.from_service_account_file('google-creds.json', scopes=['https://www.googleapis.com/auth/spreadsheets'])
    with build('sheets', 'v4', credentials=creds) as service:
      spreadsheets = service.spreadsheets()
      rows = spreadsheets.values().get(
        spreadsheetId = self.bingoInfoSheetId,
        range = 'Signups!A:A'
      ).execute().get('values', [])
      for row in rows:
        if(row[0] == 'Discord Name'):
          continue
        signedUpDiscordMembers.append(row[0])
    return signedUpDiscordMembers
  
  def getMonsters(self):
    monsters = []
    creds = service_account.Credentials.from_service_account_file('google-creds.json', scopes=['https://www.googleapis.com/auth/spreadsheets'])
    with build('sheets', 'v4', credentials=creds) as service:
      spreadsheets = service.spreadsheets()
      rows = spreadsheets.values().get(
        spreadsheetId = self.bingoInfoSheetId,
        range = 'Monsters!A:A'
      ).execute().get('values', [])
      for row in rows:
        monsters.append(row[0])
    return monsters
  
  def getClogItems(self):
    clogItems = []
    creds = service_account.Credentials.from_service_account_file('google-creds.json', scopes=['https://www.googleapis.com/auth/spreadsheets'])
    with build('sheets', 'v4', credentials=creds) as service:
      spreadsheets = service.spreadsheets()
      rows = spreadsheets.values().get(
        spreadsheetId = self.bingoInfoSheetId,
        range = 'Collection Log Items!A:A'
      ).execute().get('values', [])
      for row in rows:
        clogItems.append(row[0])
    return clogItems