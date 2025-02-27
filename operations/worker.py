from .person import PersonPayload
from enum import Enum


class WorkerPayload(PersonPayload):
    RELATIONAL_PROPS = ['hasOrganization']
    PROPS_TO_EXCLUDE = ['context', 'headers', 'url', 'id', 'type', 'link_headers', 'vat']

    class Shifts(Enum):
        MORNING = 'Morning'
        AFTERNOON = 'Afternoon'
        NIGHT = 'Night'

    def __init__(self, **kwargs):
        super(WorkerPayload, self).__init__(**kwargs)
        self.type = kwargs.get('type', 'Worker')
        self.image = kwargs.get('image', '')
        self.hasOrganization = kwargs.get('hasOrganization', '')
        self.performanceRole = kwargs.get('performanceRole', '')

    @property
    def image(self) -> str:
        return self._image

    @image.setter
    def image(self, image: str) -> None:
        self._image = image

    @property
    def performanceRole(self) -> int:
        return self._performanceRole

    @performanceRole.setter
    def performanceRole(self, performanceRole: int) -> None:
        self._performanceRole = performanceRole

    @property
    def hasOrganization(self) -> str:
        return self._hasOrganization

    @hasOrganization.setter
    def hasOrganization(self, hasOrganization: str) -> None:
        self._hasOrganization = hasOrganization
