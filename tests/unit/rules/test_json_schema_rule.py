import json

import schema

from griptape.rules import JsonSchemaRule


class TestJsonSchemaRule:
    def test_init(self):
        json_schema = schema.Schema({"type": "string"}).json_schema("test")
        rule = JsonSchemaRule(json_schema)
        assert rule.value == {
            "type": "object",
            "properties": {"type": {"const": "string"}},
            "required": ["type"],
            "additionalProperties": False,
            "$id": "test",
            "$schema": "http://json-schema.org/draft-07/schema#",
        }

    def test_to_text(self):
        json_schema = schema.Schema({"type": "string"}).json_schema("test")
        rule = JsonSchemaRule(json_schema)
        assert (
            rule.to_text()
            == f"Output valid JSON that matches this schema: {json.dumps(json_schema)}\nNo markdown, code snippets, code blocks, or backticks."
        )

    def test___str__(self):
        json_schema = schema.Schema({"type": "string"}).json_schema("test")
        rule = JsonSchemaRule(json_schema)
        assert str(rule) == rule.to_text()
