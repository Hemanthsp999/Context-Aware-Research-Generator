# cli.py
import json
import typer
from schemas import ResearchRequest
from pipeline import run_research_pipeline

app = typer.Typer(add_completion=False)


@app.command()
def brief(topic: str, conversation_id: str = "local", follow_up: bool = False, max_sources: int = 8):
    req = ResearchRequest(topic=topic, follow_up=follow_up,
                          conversation_id=conversation_id, max_sources=max_sources)
    out = run_research_pipeline(req)
    typer.echo(json.dumps(out.model_dump(), indent=2))


if __name__ == "__main__":
    app()

