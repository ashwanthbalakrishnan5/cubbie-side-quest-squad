"""Claude wrapper. Task 4 adds the LLM class here."""


class LLMError(Exception):
    """Claude failed, refused, or returned nothing usable."""
