from .entity import EntitiesPayload


class OrganizationPayload(EntitiesPayload):

    def __init__(self, **kwargs):
        super(OrganizationPayload, self).__init__(**kwargs)
        self.type = kwargs.get('type', 'Organization')
        self.legalName = kwargs.get('legalName', '')
        self.telephone = kwargs.get('telephone', '')
        self.vat = kwargs.get('vat', '')

    @property
    def legalName(self) -> str:
        return self._legalName

    @legalName.setter
    def legalName(self, legalName: str) -> None:
        self._legalName = legalName

    @property
    def vat(self) -> str:
        return self._vat

    @vat.setter
    def vat(self, vat: str) -> None:
        self._vat = vat

