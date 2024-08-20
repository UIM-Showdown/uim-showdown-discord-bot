from approvalhandlers.approvalhandler import ApprovalHandler

class TitheFarmHandler(ApprovalHandler):
  def requestApproved(self, request):
    print('Request approved:\n' + str(request))