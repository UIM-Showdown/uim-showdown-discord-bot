from approvalhandlers.approvalhandler import ApprovalHandler

class MonsterKCHandler(ApprovalHandler):
  def requestApproved(self, request):
    print('Request approved:\n' + str(request))