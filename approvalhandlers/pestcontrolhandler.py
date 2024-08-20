from approvalhandlers.approvalhandler import ApprovalHandler

class PestControlHandler(ApprovalHandler):
  def requestApproved(self, request):
    print('Request approved:\n' + str(request))