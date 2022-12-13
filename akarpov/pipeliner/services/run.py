from akarpov.pipeliner.models import BaseBlock


class BlockRunner:
    """iterates over block in tree order"""

    def __init__(self, parent_block: BaseBlock):
        self.parent_block = parent_block
        self.root = self.get_root()
        self.order = self.get_order(self.root)

    def __iter__(self):
        self.block = self.parent_block.get_root()
        return self

    def __str__(self):
        return f"block runner for {self.root}, currently running {self.block}"

    def get_order(self, block: BaseBlock) -> list[BaseBlock]:
        order = []
        for children in block.children.all():
            order.extend(self.get_order(children))
        return order

    def get_root(self):
        root = self.parent_block
        if root.parent:
            while root.parent:
                root = root.parent
        return root

    def __next__(self):
        yield from self.order
