from fuzzywuzzy import fuzz
from tests.utils.structure_runner import (
    TOOLKIT_TASK_CAPABLE_PROMPT_DRIVERS,
    run_structure,
    OUTPUT_RULESET,
    prompt_driver_id_fn,
)
import pytest


class TestToolkitTask:
    @pytest.fixture(autouse=True, params=TOOLKIT_TASK_CAPABLE_PROMPT_DRIVERS, ids=prompt_driver_id_fn)
    def agent(self, request):
        import os
        from griptape.structures import Agent
        from griptape.tools import WebScraper
        from griptape.tools import WebSearch

        return Agent(
            tools=[
                WebSearch(
                    google_api_key=os.environ["GOOGLE_API_KEY"],
                    google_api_search_id=os.environ["GOOGLE_API_SEARCH_ID"],
                ),
                WebScraper(),
            ],
            memory=None,
            prompt_driver=request.param,
            rulesets=[OUTPUT_RULESET],
        )

    def test_multi_step_cot(self, agent):
        result = run_structure(agent, "Search for parrot facts and summarize one of the results.")

        assert fuzz.partial_ratio(result["result"], "python framework")
