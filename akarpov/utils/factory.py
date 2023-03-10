import factory


class M2MPostAddition(factory.PostGeneration):
    def __init__(self, rel_name):
        self.rel_name = rel_name
        super().__init__(self.handler)

    def handler(self, obj, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            rel_manager = getattr(obj, self.rel_name)
            for item in extracted:
                rel_manager.add(item)
