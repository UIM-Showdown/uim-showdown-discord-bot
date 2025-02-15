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
        if(row[0] == 'Discord Name' and row[1] == 'RSN' and row[2] == 'Team'): # This is the header row
          continue
        if(row[2] not in rosters):
          rosters[row[2]] = [{'discordName': row[0].lower(), 'rsn': row[1]}]
        else:
          rosters[row[2]].append({'discordName': row[0].lower(), 'rsn': row[1]})
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
        if(row[0] == 'Team Name' and row[1] == 'Tag' and row[2] == 'Color'): # This is the header row
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
        range = 'Form Responses 1!D:D'
      ).execute().get('values', [])
      for row in rows:
        if('Enter your Discord username.' in row[0]): # This is the header row
          continue
        signedUpDiscordMembers.append(row[0].lower())
    return signedUpDiscordMembers
  
  def getListFromBingoInfoSheet(self, tabName):
    values = []
    creds = service_account.Credentials.from_service_account_file('google-creds.json', scopes=['https://www.googleapis.com/auth/spreadsheets'])
    with build('sheets', 'v4', credentials=creds) as service:
      spreadsheets = service.spreadsheets()
      rows = spreadsheets.values().get(
        spreadsheetId = self.bingoInfoSheetId,
        range = tabName + '!A:A'
      ).execute().get('values', [])
      for row in rows:
        values.append(row[0])
    return values