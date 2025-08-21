# pipeline.py
# from typing import Dict
from schemas import ResearchRequest, ResearchResponse
from graph import build_graph
from memory import get_history, append_brief

graph = build_graph(get_history)


def run_research_pipeline(req: ResearchRequest) -> ResearchResponse:
    # Seed graph state
    inputs = {
        "topic": req.topic,
        "follow_up": req.follow_up,
        "conversation_id": req.conversation_id,
        "user_id": req.user_id,  # add this only if you have it
        "prior_context": None,
        "docs": [],
        "brief": None,
    }
    # synchronous; use .astream for streaming
    result = graph.invoke(
        inputs,
        config={
            "configurable": {
                "thread_id": req.conversation_id,  # used to resume from checkpoints
                "checkpoint_id": req.conversation_id
            }
        }
    )
    brief = result["brief"]

    # Persist for future follow-ups
    append_brief(req.conversation_id, brief)

    # Validate + return
    return ResearchResponse(**brief.model_dump())

