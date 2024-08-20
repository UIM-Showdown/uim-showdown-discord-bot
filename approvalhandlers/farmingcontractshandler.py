from approvalhandlers.approvalhandler import ApprovalHandler

class FarmingContractsHandler(ApprovalHandler):
  def requestApproved(self, request):
    print('Request approved:\n' + str(request))