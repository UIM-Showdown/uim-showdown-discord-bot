import requests

# Client for interacting with the UIM Showdown backend

class BackendClient():
  
  def __init__(self, url):
    self.url = url

  def get(self, uri):
    try:
      return requests.get(self.url + uri)
    except Exception as e:
      raise Exception('Failed to connect to backend', e)
  
  def post(self, uri, data):
    try:
      return requests.post(self.url + uri, json=data)
    except Exception as e:
      raise Exception('Failed to connect to backend', e)
  
  def patch(self, uri, data):
    try:
      return requests.patch(self.url + uri, json=data)
    except Exception as e:
      raise Exception('Failed to connect to backend', e)

  def put(self, uri, data):
    try:
      return requests.put(self.url + uri, json=data)
    except Exception as e:
      raise Exception('Failed to connect to backend', e)

  def delete(self, uri, data):
    try:
      return requests.delete(self.url + uri, json=data)
    except Exception as e:
      raise Exception('Failed to connect to backend', e)
    
  def getCompetitionInfo(self):
    response = self.get('/competitionInfo')
    if(response.status_code != 200):
      raise Exception('Failed to get competition info')
    return response.json()
  
  def initializeBackend(self):
    response = self.post('/admin/initializeCompetition', None)
    if(response.status_code != 200):
      raise Exception('Failed to initialize backend')
    
  def updateCompetitorRole(self):
    response = self.post('/admin/updateCompetitorRole', None)
    if(response.status_code != 200):
      raise Exception('Failed to update competitor role')
    return response.json()
  
  def setupDiscordServer(self):
    response = self.post('/admin/setupDiscordServer', None)
    if(response.status_code != 200):
      raise Exception('Failed to setup Discord server')
    return response.json()
  
  def teardownDiscordServer(self):
    response = self.post('/admin/teardownDiscordServer', None)
    if(response.status_code != 200):
      raise Exception('Failed to teardown Discord server')
    
  def updateBackend(self):
    response = self.post('/admin/updateCompetition', None)
    if(response.status_code != 200):
      raise Exception('Failed to update backend')
    
  def reinitializeTile(self, tile):
    response = self.post('/admin/reinitializeTile/' + tile, None)
    if(response.status_code != 200):
      raise Exception('Failed to reinitialize tile')
    
  def addPlayer(self, rsn, discordName, teamName):
    body = {
      'rsn': rsn,
      'discordName': discordName,
      'teamName': teamName
    }
    response = self.post('/admin/addPlayer', body)
    if(response.status_code != 200):
      raise Exception('Failed to add player')
    
  def changePlayerRsn(self, oldRsn, newRsn):
    body = {
      'oldRsn': oldRsn,
      'newRsn': newRsn
    }
    response = self.patch('/admin/changePlayerRsn', body)
    if(response.status_code != 200):
      raise Exception('Failed to change player RSN')
    
  def changePlayerDiscordName(self, oldDiscordName, newDiscordName):
    body = {
      'oldDiscordName': oldDiscordName,
      'newDiscordName': newDiscordName
    }
    response = self.patch('/admin/changePlayerDiscordName', body)
    if(response.status_code != 200):
      raise Exception('Failed to change player Discord name')
  
  def changePlayerTeam(self, player, team):
    body = {
      'rsn': player,
      'teamName': team
    }
    response = self.patch('/admin/changePlayerTeam', body)
    if(response.status_code != 200):
      raise Exception('Failed to get competition info')
    
  def setStaffAdjustment(self, player, method, adjustment):
    body = {
      'rsn': player,
      'contributionMethodName': method,
      'adjustment': adjustment
    }
    response = self.post('/admin/setStaffAdjustment', body)
    if(response.status_code != 200):
      raise Exception('Failed to set staff adjustment')

  def getTeamRosters(self):
    rosters = {}
    response = self.get('/teams')
    if(response.status_code != 200):
      raise Exception('Failed to get team rosters')
    for team in response.json():
      roster = []
      for player in team['players']:
        roster.append(player)
      rosters[team['name']] = roster
    return rosters
  
  def getTeamInfo(self):
    teamInfo = {}
    response = self.get('/teams')
    if(response.status_code != 200):
      raise Exception('Failed to get team info')
    for team in response.json():
      teamInfo[team['name']] = {'tag': team['abbreviation'], 'color': team['color']}
    return teamInfo
  
  def getTiles(self):
    tiles = []
    response = self.get('/tiles')
    if(response.status_code != 200):
      raise Exception('Failed to get tiles')
    for tile in response.json():
      tiles.append(tile['name'])
    return tiles
  
  def getContributionMethods(self):
    methods = []
    response = self.get('/contributionMethods')
    if(response.status_code != 200):
      raise Exception('Failed to get contribution methods')
    for method in response.json():
      methods.append(method)
    return methods
  
  def getContributionMethodNamesByType(self, type):
    methods = []
    response = self.get('/contributionMethods')
    if(response.status_code != 200):
      raise Exception('Failed to get contribution methods')
    for method in response.json():
      if(method['contributionMethodType'] == type):
        methods.append(method['name'])
    return methods
  
  def getCollectionLogItems(self):
    items = []
    response = self.get('/collectionLogItems')
    if(response.status_code != 200):
      raise Exception('Failed to get collection log items')
    for item in response.json():
      if(len(item['itemOptions']) > 0):
        for option in item['itemOptions']:
          items.append(option)
      else:
        items.append(item['name'])
    return items
  
  def getRecords(self):
    records = []
    response = self.get('/records')
    if(response.status_code != 200):
      raise Exception('Failed to get records')
    for record in response.json():
      records.append({'nameAndHandicap': record['name'].title(), 'name': record['name'].title(), 'handicap': None})
      if(len(record['handicaps']) > 0):
        for handicap in record['handicaps']:
          records.append({'nameAndHandicap': record['name'].title() + ' - ' + handicap['name'], 'name': record['name'].title(), 'handicap': handicap['name']})
    return records
  
  def getChallenges(self):
    challenges = []
    response = self.get('/challenges')
    if(response.status_code != 200):
      raise Exception('Failed to get challenges')
    for challenge in response.json():
      if(len(challenge['relayComponents']) > 0):
        for component in challenge['relayComponents']:
          challenges.append({'nameAndRelayComponent': challenge['name'] + ' - ' + component['name'], 'name': challenge['name'], 'relayComponent': component['name']})
      else:
        challenges.append({'nameAndRelayComponent': challenge['name'], 'name': challenge['name'], 'relayComponent': None})
    return challenges
  
  def approveSubmission(self, id, reviewer):
    body = {
      'state': 'APPROVED',
      'reviewer': reviewer
    }
    response = self.patch('/submissions/' + str(id), body)
    if(response.status_code == 400):
      raise Exception('Submission has already been approved or denied')
    if(response.status_code != 200):
      raise Exception('Failed to approve decision, got status code: ' + str(response.status_code))
    return response.json()
    
  def denySubmission(self, id, reviewer):
    body = {
      'state': 'DENIED',
      'reviewer': reviewer
    }
    response = self.patch('/submissions/' + str(id), body)
    if(response.status_code == 400):
      raise Exception('Submission has already been approved or denied')
    if(response.status_code != 200):
      raise Exception('Failed to deny decision, got status code: ' + str(response.status_code))
    return response.json()
  
  def undoDecision(self, id):
    response = self.patch('/submissions/' + str(id) + '/undo', None)
    if(response.status_code == 400):
      raise Exception('Submission is already open')
    if(response.status_code != 200):
      raise Exception('Failed to undo decision, got status code: ' + str(response.status_code))
    return response.json()
    
  def submitContribution(self, rsn, method, value, urls, description):
    body = {
      'rsn': rsn,
      'methodName': method,
      'value': value,
      'screenshotURLs': urls,
      'description': description
    }
    response = self.post('/submissions/contribution', body)
    if(response.status_code != 200):
      raise Exception('Failed to submit contribution')
    return response.json()['id']
  
  def submitContributionIncrement(self, rsn, method, amount, urls, description):
    body = {
      'rsn': rsn,
      'methodName': method,
      'amount': amount,
      'screenshotURLs': urls,
      'description': description
    }
    response = self.post('/submissions/contribution/increment', body)
    if(response.status_code != 200):
      raise Exception('Failed to submit contribution increment')
    return response.json()['id']
  
  def submitContributionPurchase(self, rsn, method, amount, urls, description):
    body = {
      'rsn': rsn,
      'methodName': method,
      'amount': amount,
      'screenshotURLs': urls,
      'description': description
    }
    response = self.post('/submissions/contribution/purchase', body)
    if(response.status_code != 200):
      raise Exception('Failed to submit contribution purchase')
    return response.json()['id']
  
  def submitCollectionLogItem(self, rsn, item, urls, description):
    body = {
      'rsn': rsn,
      'itemName': item,
      'screenshotURLs': urls,
      'description': description
    }
    response = self.post('/submissions/collectionlog', body)
    if(response.status_code != 200):
      raise Exception('Failed to submit collection log item')
    return response.json()['id']
  
  def submitChallenge(self, rsn, challengeNameAndRelayComponent, seconds, urls, description):
    challengeName = challengeNameAndRelayComponent.split('|')[0]
    relayComponentName = None
    if('|' in challengeNameAndRelayComponent):
      relayComponentName = challengeNameAndRelayComponent.split('|')[1]
    if(relayComponentName == 'None'):
      relayComponentName = None
    body = {
      'rsn': rsn,
      'challengeName': challengeName,
      'relayComponentName': relayComponentName,
      'seconds': float(seconds),
      'screenshotURLs': urls,
      'description': description
    }
    response = self.post('/submissions/challenge', body)
    if(response.status_code != 200):
      raise Exception('Failed to submit challenge')
    return response.json()['id']
  
  def submitRecord(self, rsn, recordNameAndHandicap, value, videoUrl, description):
    recordName = recordNameAndHandicap.split('|')[0]
    handicap = recordNameAndHandicap.split('|')[1]
    if(handicap == 'None'):
      handicap = None
    body = {
      'rsn': rsn,
      'recordName': recordName.upper(),
      'handicapName': handicap,
      'rawValue': value,
      'videoUrl': videoUrl,
      'description': description
    }
    response = self.post('/submissions/record', body)
    if(response.status_code != 200):
      raise Exception('Failed to submit record')
    return response.json()['id']
