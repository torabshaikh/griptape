import pytest

from griptape.tools import ComputerTool
from tests.mocks.docker.fake_api_client import make_fake_client


class TestComputer:
    @pytest.fixture()
    def computer(self):
        return ComputerTool(docker_client=make_fake_client())

    def test_execute_code(self, computer):
        assert computer.execute_code({"values": {"code": "print(1)", "filename": "foo.py"}}).value == "hello world"

    def test_execute_command(self, computer):
        assert computer.execute_command({"values": {"command": "ls"}}).value == "hello world"
