from approvalhandlers.approvalhandler import ApprovalHandler

class MTAHandler(ApprovalHandler):
  def requestApproved(self, request):
    print('Request approved:\n' + str(request))