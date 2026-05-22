from typing import TypedDict


class PipelineState(TypedDict):
    topic: str
    research: str
    outline: str
    content: str
    script: str
    current_stage: str
