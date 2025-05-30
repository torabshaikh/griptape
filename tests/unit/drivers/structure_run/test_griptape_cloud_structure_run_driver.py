import json
from unittest.mock import MagicMock, Mock

import pytest

from griptape.artifacts import InfoArtifact, TextArtifact
from griptape.artifacts.error_artifact import ErrorArtifact
from griptape.drivers.structure_run.griptape_cloud import GriptapeCloudStructureRunDriver
from griptape.events import EventBus
from griptape.events.event_listener import EventListener


class TestGriptapeCloudStructureRunDriver:
    @pytest.fixture(autouse=True)
    def mock_requests_get(self, mocker):
        mock_response = mocker.Mock()
        mock_response.iter_lines.return_value = [
            *[
                f"data: {json.dumps(event)}".encode()
                for event in [
                    {
                        "origin": "USER",
                        "type": "FooBarEvent",
                        "payload": {
                            "type": "FooBarEvent",
                            "span_id": "1",
                        },
                    },
                    {
                        "origin": "USER",
                        "type": "FinishStructureRunEvent",
                        "payload": {
                            "type": "FinishStructureRunEvent",
                            "span_id": "1",
                            "output_task_input": {
                                "type": "TextArtifact",
                                "value": "foo bar",
                            },
                            "output_task_output": {
                                "type": "TextArtifact",
                                "value": "foo bar",
                            },
                            "meta": {
                                "foo": "bar",
                            },
                        },
                    },
                    {"origin": "FOO", "type": "BAR"},
                    {
                        "origin": "SYSTEM",
                        "type": "StructureRunError",
                        "payload": {
                            "status_detail": {
                                "error": "foo bar",
                            },
                        },
                    },
                    {
                        "origin": "SYSTEM",
                        "type": "StructureRunCompleted",
                        "payload": {
                            "status": "SUCCEEDED",
                            "started_at": "2024-09-11T23:15:47",
                            "completed_at": "2024-09-11T23:15:50",
                            "status_detail": {"reason": "Completed", "message": None, "exit_code": 0},
                        },
                    },
                ]
            ],
            "",
            "title:",
        ]
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock()

        return mocker.patch(
            "requests.get",
            return_value=mock_response,
        )

    @pytest.fixture(autouse=True)
    def mock_requests_post(self, mocker):
        mock_response = mocker.Mock()
        mock_response.json.return_value = {"structure_run_id": "1"}

        return mocker.patch(
            "requests.post",
            return_value=mock_response,
        )

    @pytest.fixture()
    def driver(self):
        return GriptapeCloudStructureRunDriver(
            base_url="https://cloud-foo.griptape.ai",
            api_key="foo bar",
            structure_id="1",
            env={"key": "value"},
            structure_run_wait_time_interval=0,
        )

    def test_run(self, driver):
        mock_on_event = Mock()
        EventBus.add_event_listener(EventListener(on_event=mock_on_event))
        result = driver.run(TextArtifact("foo bar"))

        events = mock_on_event.call_args[0]
        assert len(events) == 1
        assert events[0].type == "FinishStructureRunEvent"
        assert events[0].meta == {
            "foo": "bar",
            "span_id": "1",
        }

        assert isinstance(result, ErrorArtifact)
        assert result.value == "foo bar"

    def test_async_run(self, driver):
        driver.async_run = True
        result = driver.run(TextArtifact("foo bar"))
        assert isinstance(result, InfoArtifact)
        assert result.value == "Run started successfully"

    def test_run_timeout(self, driver, mocker):
        mock_response = mocker.Mock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock()
        mock_response.iter_lines.return_value = []
        mocker.patch("requests.get", return_value=mock_response)

        with pytest.raises(ValueError, match="Output not found."):
            driver.run(TextArtifact("foo bar"))
