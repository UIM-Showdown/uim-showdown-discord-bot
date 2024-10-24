from abc import ABC, abstractmethod

# ABC for approval handlers. The requestApproved method on the extending class should 
# handle all bot-external actions to take upon a request's approval (e.g. modifying a 
# spreadsheet)
class ApprovalHandler(ABC):

  @abstractmethod
  def requestApproved(self, request):
    pass

class BAHandler(ApprovalHandler):
  def requestApproved(self, request):
    print('Request approved:\n' + str(request))

class ChallengeHandler(ApprovalHandler):
  def requestApproved(self, request):
    print('Request approved:\n' + str(request))

class ClogHandler(ApprovalHandler):
  def requestApproved(self, request):
    print('Request approved:\n' + str(request))

class FarmingContractsHandler(ApprovalHandler):
  def requestApproved(self, request):
    print('Request approved:\n' + str(request))

class FarmingContractsHandler(ApprovalHandler):
  def requestApproved(self, request):
    print('Request approved:\n' + str(request))

class LMSHandler(ApprovalHandler):
  def requestApproved(self, request):
    print('Request approved:\n' + str(request))

class MonsterKCHandler(ApprovalHandler):
  def requestApproved(self, request):
    print('Request approved:\n' + str(request))

class MTAHandler(ApprovalHandler):
  def requestApproved(self, request):
    print('Request approved:\n' + str(request))

class PestControlHandler(ApprovalHandler):
  def requestApproved(self, request):
    print('Request approved:\n' + str(request))

class TitheFarmHandler(ApprovalHandler):
  def requestApproved(self, request):
    print('Request approved:\n' + str(request))