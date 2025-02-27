from django.db.models import Manager


class TagManager(Manager):
    pass


class TagResultManager(Manager):
    def create_tag_result(self, tag, pdf):
        return self.create(tag=tag, pdf=pdf)
