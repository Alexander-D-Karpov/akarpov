from abc import ABC

from akarpov.pipeliner.models import Block


class BlockRunner(ABC):
    def __init__(self, block: Block, data: dict):
        self.block = block
        self.data = data
        self.context = self._get_context_data()

    def _get_context_data(self):
        context = self.block.context  # type: dict
        if context:
            for key, val in context.items():
                if val.strarswith("$"):
                    if key not in self.data:
                        raise KeyError(
                            f"No context data found for {key} in block {self.block.id}"
                        )
                    context[key] = self.data[key]
            return context
        return {}
