import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
import cli
from typer.testing import CliRunner
import json
from dotenv import load_dotenv

load_dotenv()
os.getenv("TAVILY_API_KEY")

runner = CliRunner()


@pytest.mark.integration
def test_cli_brief_integration():
    """
    Integration test for the CLI 'brief' command.
    Runs the real pipeline (requires API keys set in environment).
    """

    # Skip test if API keys are not available
    if not (os.getenv("TAVILY_API_KEY") or os.getenv("GOOGLE_API_KEY")):
        pytest.skip("No API keys configured for Tavily/Google search")

    topic = "AI in healthcare"

    # Run CLI: equivalent to `python cli.py brief "AI in healthcare"`
    result = runner.invoke(cli.app, ["brief", topic, "--conversation-id", "test_cli"])

    # CLI should succeed
    assert result.exit_code == 0, f"CLI failed: {result.stdout}"

    # Output should be valid JSON
    data = json.loads(result.stdout)

    # Validate schema
    assert "topic" in data
    assert "summary" in data
    assert "references" in data
    assert isinstance(data["references"], list)

    # Topic should reflect the input
    assert "ai" in data["topic"].lower()

