from typing import TypedDict


class PipelineState(TypedDict):
    topic: str
    direction: str
    clarify: str
    research: str
    outline: str
    content: str
    script: str
    current_stage: str
