# graph.py
from typing import List, Optional
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.documents import Document
# from langchain_core.runnables import RunnableLambda
from memory import append_brief
from langgraph.checkpoint.memory import MemorySaver
from schemas import ResearchBrief
from tools import retrieve_evidence
from dotenv import load_dotenv
import os


load_dotenv()

google_api_key = os.getenv("GOOGLE_API_KEY")
os.getenv("TAVILY_API_KEY")

# ---- LLMs (Gemini) ----
# Use a smaller/faster model for summarization and a stronger model for brief synthesis.
summarizer_llm = ChatGoogleGenerativeAI(
    google_api_key=google_api_key, model="gemini-1.5-flash"
)
llm = ChatGoogleGenerativeAI(
    google_api_key=google_api_key, model="gemini-2.0-flash"
)
brief_llm = llm.with_structured_output(ResearchBrief)

# ---- Graph State ----


class GraphState(TypedDict):
    topic: str
    follow_up: bool
    conversation_id: Optional[str]
    prior_context: Optional[str]        # summarized earlier briefs (if any)
    docs: List[Document]
    brief: Optional[ResearchBrief]

# ---- Node: incorporate previous context (summary step) ----


def summarize_previous_briefs(prior_briefs: List[ResearchBrief]) -> str:
    if not prior_briefs:
        return ""
    # Small on-the-fly summarizer using the dedicated summarizer LLM
    bullets = []
    for b in prior_briefs[-3:]:
        bullets.append(f"- {b.topic}: {b.summary[:300]}...")
    prompt = (
        "Summarize the following prior research briefs into ~4 concise bullets, "
        "focusing on insights relevant to a new query.\n"
        + "\n".join(bullets)
    )
    return summarizer_llm.invoke(prompt).content


def node_incorporate_previous(state: GraphState, get_history) -> GraphState:
    # get_history is injected at compile-time; returns List[ResearchBrief]
    prior = get_history(state.get("conversation_id"))
    state["prior_context"] = summarize_previous_briefs(prior)
    return state

# ---- Node: retrieve evidence ----


def node_retrieve(state: GraphState) -> GraphState:
    ctx = state.get("prior_context") or ""
    query = f"{state['topic']} {('context: ' + ctx) if ctx else ''}".strip()
    state["docs"] = retrieve_evidence(query)
    return state

# ---- Node: generate structured brief ----


def node_generate(state: GraphState) -> GraphState:
    # Convert docs → compact evidence list for the model
    refs = []
    for i, d in enumerate(state["docs"][:12]):
        refs.append(
            f"[{i+1}] {d.metadata.get('title','')} — {d.metadata.get('source','')}\n{d.page_content[:500]}"
        )

    sys = (
        "You are a research assistant. Produce a concise, evidence-linked research brief.\n"
        "Cite sources by including them in the 'references' field with title+URL.\n"
        "Only include claims supported by the evidence text or standard facts.\n"
    )
    prompt = (
        f"{sys}\nTopic: {state['topic']}\n"
        f"Prior context:\n  {state['prior_context'] if state.get('prior_context') else ''}\n\n"
        "Evidence:\n" + "\n\n".join(refs)
    )
    brief: ResearchBrief = brief_llm.invoke(prompt)
    state["brief"] = brief
    return state

# ---- Node: end ----


def node_end(state: GraphState) -> GraphState:
    brief = state.get('brief')

    if brief:
        append_brief(("conversation_id"), brief)
        brief.context_used = state.get("prior_context") or ""
    return state

# ---- Graph factory ----


def build_graph(get_history):

    checkpoint_store = MemorySaver()
    g = StateGraph(GraphState)
    g.add_node("IncorporatePreviousBriefs", lambda s: node_incorporate_previous(s, get_history))
    g.add_node("RetrieveEvidence", node_retrieve)
    g.add_node("GenerateBrief", node_generate)
    g.add_node("Finish", node_end)

    # Always incorporate context (if any), then retrieve → generate → finish
    g.set_entry_point("IncorporatePreviousBriefs")
    g.add_edge("IncorporatePreviousBriefs", "RetrieveEvidence")
    g.add_edge("RetrieveEvidence", "GenerateBrief")
    g.add_edge("GenerateBrief", "Finish")
    g.add_edge("Finish", END)
    return g.compile(checkpointer=checkpoint_store)

