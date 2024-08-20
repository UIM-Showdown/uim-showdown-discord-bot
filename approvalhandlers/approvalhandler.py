from abc import ABC, abstractmethod

# ABC for approval handlers. The requestApproved method on the extending class should 
# handle all bot-external actions to take upon a request's approval (e.g. modifying a 
# spreadsheet)
class ApprovalHandler(ABC):

  @abstractmethod
  def requestApproved(self, request):
    pass