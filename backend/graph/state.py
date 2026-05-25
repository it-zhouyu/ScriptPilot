from typing import TypedDict


class PipelineState(TypedDict):
    topic: str
    direction: str
    direction_analysis: str
    style: str
    style_analysis: str
    research: str
    outline: str
    content: str
    script: str
    current_stage: str
