from .entity import EntitiesPayload


# noinspection PyPep8Naming
class PersonPayload(EntitiesPayload):
    def __init__(self, **kwargs):
        super(PersonPayload, self).__init__(**kwargs)
        self.givenName = kwargs.get('givenName', '')
        self.familyName = kwargs.get('familyName', '')
        self.image = kwargs.get('image', '')
        self.active = kwargs.get('active', False)

    @property
    def givenName(self) -> str:
        return self._givenName

    @givenName.setter
    def givenName(self, givenName: str) -> None:
        self._givenName = givenName

    @property
    def familyName(self) -> str:
        return self._familyName

    @familyName.setter
    def familyName(self, familyName: str) -> None:
        self._familyName = familyName

    @property
    def active(self) -> bool:
        return self._active

    @active.setter
    def active(self, active: bool) -> None:
        self._active = active
