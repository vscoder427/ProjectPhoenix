"""
Test data factories for Dave service.

Factories generate realistic test data without hitting the database.
Use these for unit tests and to set up integration test scenarios.

Available Factories:
- ConversationFactory: Create test conversations
- MessageFactory: Create test messages
- KnowledgeArticleFactory: Create test knowledge base articles
- PromptFactory: Create test prompt records
- PromptVersionFactory: Create test prompt versions
"""
from .conversation import ConversationFactory, MessageFactory
from .knowledge import KnowledgeArticleFactory
from .prompt import PromptFactory, PromptVersionFactory

__all__ = [
    "ConversationFactory",
    "MessageFactory",
    "KnowledgeArticleFactory",
    "PromptFactory",
    "PromptVersionFactory",
]
