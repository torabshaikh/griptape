import pytest

from tests.utils.structure_tester import StructureTester


class TestFileManager:
    @pytest.fixture(
        autouse=True,
        params=StructureTester.TOOLKIT_TASK_CAPABLE_PROMPT_DRIVERS,
        ids=StructureTester.generate_prompt_driver_id,
    )
    def structure_tester(self, request):
        from griptape.structures import Agent
        from griptape.tools import FileManagerTool

        return StructureTester(Agent(tools=[FileManagerTool()], conversation_memory=None, prompt_driver=request.param))

    def test_save_content_to_disk(self, structure_tester):
        structure_tester.run('Write the content "Hello World!" to a file called "poem.txt".')

    def test_load_files_from_disk(self, structure_tester):
        structure_tester.run("Read the content of the file called 'poem.txt'.")
