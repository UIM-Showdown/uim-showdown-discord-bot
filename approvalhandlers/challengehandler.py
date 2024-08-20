from approvalhandlers.approvalhandler import ApprovalHandler

'''
Note: For time logic, the timedelta type may be useful

e.g. `delta = timedelta(minutes=request.params['minutes'], seconds=request.params['seconds'], milliseconds=request.params['tenths_of_seconds']*100)`

then you can do math with them

e.g. `if(delta > firstPlaceDelta * 2): awardNoPoints()`
'''

class ChallengeHandler(ApprovalHandler):
  def requestApproved(self, request):
    print('Request approved:\n' + str(request))