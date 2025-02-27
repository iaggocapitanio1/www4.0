from .person import PersonPayload


class GenericPayload(PersonPayload):
    RELATIONAL_PROPS = []

    def __init__(self, typ: str, **kwargs):
        super(GenericPayload, self).__init__(**kwargs)
        self.type = typ





