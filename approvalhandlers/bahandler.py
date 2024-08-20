from approvalhandlers.approvalhandler import ApprovalHandler

class BAHandler(ApprovalHandler):
  def requestApproved(self, request):
    print('Request approved:\n' + str(request))