from griptape.artifacts import CsvRowArtifact
from tests.mocks.mock_embedding_driver import MockEmbeddingDriver


class TestCsvRowArtifact:
    def test_value_type_conversion(self):
        assert CsvRowArtifact({"foo": "bar"}).value == {"foo": "bar"}
        assert CsvRowArtifact({"foo": {"bar": "baz"}}).value == {
            "foo": {"bar": "baz"}
        }
        assert CsvRowArtifact('{"foo": "bar"}').value == {"foo": "bar"}

    def test___add__(self):
        assert (
            CsvRowArtifact({"test1": "foo"}) + CsvRowArtifact({"test2": "bar"})
        ).value == {"test1": "foo", "test2": "bar"}

    def test_generate_embedding(self):
        assert CsvRowArtifact({"test1": "foo"}).generate_embedding(
            MockEmbeddingDriver()
        ) == [0, 1]

    def test_to_text(self):
        assert (
            CsvRowArtifact(
                {"test1": "foo|bar", "test2": 1}, delimiter="|"
            ).to_text()
            == '"foo|bar"|1'
        )

    def test_to_dict(self):
        assert CsvRowArtifact({"test1": "foo"}).to_dict()["value"] == {
            "test1": "foo"
        }

    def test_name(self):
        artifact = CsvRowArtifact({})

        assert artifact.name == artifact.id
        assert CsvRowArtifact({}, name="bar").name == "bar"

    def test___bool__(self):
        assert not bool(CsvRowArtifact({}))
        assert bool(CsvRowArtifact({"foo": "bar"}))
