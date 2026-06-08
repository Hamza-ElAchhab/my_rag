import uuid
from typing import List, Optional
from pydantic import BaseModel, Field






class MinimalSource(BaseModel):
    """Represents a source location in the codebase."""
  
    file_path: str
    first_character_index: int
    last_character_index: int





class UnansweredQuestion(BaseModel):
    """Represents a question without an answer."""

    question_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str





class AnsweredQuestion(UnansweredQuestion):
    """Represents a question with an answer and sources."""

    sources: List[MinimalSource]
    answer: str


class RagDataset(BaseModel):
    """Represents a dataset of RAG questions."""

    rag_questions: List[AnsweredQuestion | UnansweredQuestion]





class MinimalSearchResults(BaseModel):
    """Represents search results for a single question."""

    question_id: str
    question: str
    retrieved_sources: List[MinimalSource]





class MinimalAnswer(MinimalSearchResults):
    """Represents search results with a generated answer."""

    answer: str





class StudentSearchResults(BaseModel):
    """Represents all search results from the student system."""

    search_results: List[MinimalSearchResults]
    k: int





class StudentSearchResultsAndAnswer(BaseModel):
    """Represents all search results with generated answers."""

    search_results: List[MinimalAnswer]
    k: int





class Chunk(BaseModel):
    """Represents a chunk of text from a file."""

    file_path: str
    content: str
    first_character_index: int
    last_character_index: int
    chunk_type: str = "text"  # "python" or "text"





class ChunkIndex(BaseModel):
    """Represents the indexed chunks."""

    chunks: List[Chunk]
    file_type_map: Optional[dict] = None
