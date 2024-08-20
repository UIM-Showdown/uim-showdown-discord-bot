from abc import ABC, abstractmethod

class ApprovalHandler(ABC):

  @abstractmethod
  def requestApproved(self, request):
    pass