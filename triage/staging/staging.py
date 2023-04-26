import abc


class Staging(abc.ABC):
    """
    The base class for staging, which is the backend
    process which a prompt goes through before it reaches the model

    Create a subclass of this to implement a staging strategy
    """

    def __init__(self):
        pass

    @abc.abstractmethod
    def gating(self, prompt):
        """
        The process of selectively allowing or blocking certain
        types of input based on their perceived level of risk potential
        for adversarial attacks.
        """
        return prompt

    @abc.abstractmethod
    def annotation_verification(self, prompt, lr, log=False):
        """
        The process through which a prompt's annotations are verified
        to be accurate.
        """
        return prompt

    @abc.abstractmethod
    def layering(self, prompt):
        """
        The act of subjecting a prompt to a series of meta-prompts
        to refine or sanitise it.
        """
        return prompt

    @abc.abstractmethod
    def vaccination(self, prompt):
        """
        The act of inserting default annotations and meta-prompts
        into a prompt to make it more reslient to attack.
        """
        return prompt
