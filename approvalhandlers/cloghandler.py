from approvalhandlers.approvalhandler import ApprovalHandler

class ClogHandler(ApprovalHandler):
  def requestApproved(self, request):
    print('Request approved:\n' + str(request))