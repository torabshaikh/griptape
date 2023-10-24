import pytest
from griptape.artifacts import (
    ListArtifact,
    TextArtifact,
    BlobArtifact,
    CsvRowArtifact,
)


class TestListArtifact:
    def test_to_text(self):
        assert (
            ListArtifact([TextArtifact("foo"), TextArtifact("bar")]).to_text()
            == "foo\n\nbar"
        )
        assert (
            ListArtifact(
                [TextArtifact("foo"), TextArtifact("bar")],
                item_separator="test",
            ).to_text()
            == "footestbar"
        )

    def test_to_dict(self):
        assert (
            ListArtifact([TextArtifact("foobar")]).to_dict()["value"][0][
                "value"
            ]
            == "foobar"
        )

    def test___add__(self):
        artifact = ListArtifact([TextArtifact("foo")]) + ListArtifact(
            [TextArtifact("bar")]
        )

        assert isinstance(artifact, ListArtifact)
        assert len(artifact.value) == 2
        assert artifact.value[0].value == "foo"
        assert artifact.value[1].value == "bar"

    def test_validate_value(self):
        with pytest.raises(ValueError):
            ListArtifact([TextArtifact("foo"), BlobArtifact(b"bar")])

    def test_child_type(self):
        assert ListArtifact([TextArtifact("foo")]).child_type == TextArtifact

    def test_is_type(self):
        assert ListArtifact([TextArtifact("foo")]).is_type(TextArtifact)
        assert ListArtifact([CsvRowArtifact({"foo": "bar"})]).is_type(
            TextArtifact
        )
        assert ListArtifact([CsvRowArtifact({"foo": "bar"})]).is_type(
            CsvRowArtifact
        )

    def test_has_items(self):
        assert not ListArtifact().has_items()
        assert ListArtifact([TextArtifact("foo")]).has_items()
