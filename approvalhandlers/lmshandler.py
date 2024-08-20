from approvalhandlers.approvalhandler import ApprovalHandler

class LMSHandler(ApprovalHandler):
  def requestApproved(self, request):
    print('Request approved:\n' + str(request))