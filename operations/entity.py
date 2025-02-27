from .core import BasePayload


class EntitiesPayload(BasePayload):

    def __init__(self, **kwargs):
        super(EntitiesPayload, self).__init__(**kwargs)
        self.email = kwargs.get('email', '')
        self.vat = kwargs.get('vat', '')

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, email: str) -> None:
        self._email = email

    @property
    def vat(self) -> float:
        return self._vat

    @vat.setter
    def vat(self, vat: float) -> None:
        self._vat = vat
