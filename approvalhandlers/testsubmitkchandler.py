from approvalhandlers.approvalhandler import ApprovalHandler

class TestSubmitKCHandler(ApprovalHandler):
  def requestApproved(self, request):
    print('Request approved:\n' + str(request))