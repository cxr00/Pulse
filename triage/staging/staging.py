import abc


class Staging(abc.ABC):

    def __init__(self):
        pass

    @abc.abstractmethod
    def gating(self, prompt):
        return prompt

    @abc.abstractmethod
    def annotation_verification(self, prompt, lr, log=False):
        return prompt

    @abc.abstractmethod
    def layering(self, prompt):
        return prompt

    @abc.abstractmethod
    def vaccination(self, prompt):
        return prompt
