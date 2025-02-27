
class OrganizationQueries(object):

    def __init__(self, *args, **kwargs):
        self.url = args[0] if args else kwargs.get('url')

    @property
    def url(self) -> str:
        if self.url is None:
            raise ValueError("url is a required argument.")
        return self._url

    @url.setter
    def url(self, url: str) -> None:
        self._url = url

