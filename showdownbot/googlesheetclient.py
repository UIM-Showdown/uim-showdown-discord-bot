from google.oauth2 import service_account
from googleapiclient.discovery import build

# Client for interacting with a Google sheet
class GoogleSheetClient():

  def __init__(self, bingoInfoSheetId):
    self.bingoInfoSheetId = bingoInfoSheetId
  
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