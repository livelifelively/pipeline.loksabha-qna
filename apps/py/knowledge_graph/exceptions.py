class KnowledgeGraphError(Exception):
    """Base exception for knowledge graph errors"""

    pass


class QuestionNotFoundError(KnowledgeGraphError):
    """Raised when question doesn't exist"""

    pass


class InvalidMetadataError(KnowledgeGraphError):
    """Raised when metadata is invalid"""

    pass


class StepNotFoundError(KnowledgeGraphError):
    """Raised when required step is not found"""

    pass
