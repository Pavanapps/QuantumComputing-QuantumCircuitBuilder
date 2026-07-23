"""
History manager for Quantum Circuit Builder Pro.
"""

from copy import deepcopy

MAX_HISTORY = 50
class CircuitHistory:

    def __init__(self):

        self.undo_stack = []

        self.redo_stack = []

    def save(self, circuit):

        self.undo_stack.append(deepcopy(circuit))

        if len(self.undo_stack) > MAX_HISTORY:
            self.undo_stack.pop(0)

        self.redo_stack.clear()

    def undo(self, current):

        if not self.undo_stack:
            return deepcopy(current)

        self.redo_stack.append(deepcopy(current))

        return deepcopy(self.undo_stack.pop())

    def redo(self, current):

        if not self.redo_stack:
            return deepcopy(current)

        self.undo_stack.append(deepcopy(current))

        return deepcopy(self.redo_stack.pop())

    def clear(self):

        self.undo_stack.clear()

        self.redo_stack.clear()

    @property
    def can_undo(self):
        return len(self.undo_stack) > 0

    @property
    def can_redo(self):
        return len(self.redo_stack) > 0