from __future__ import annotations
from attrs import define, field, Factory
from typing import Optional, TYPE_CHECKING, Any
from griptape.utils import import_optional_dependency
from griptape.drivers import BaseConversationMemoryDriver
from griptape.memory.structure import BaseConversationMemory

if TYPE_CHECKING:
    import boto3


@define
class AmazonDynamoDbConversationMemoryDriver(BaseConversationMemoryDriver):
    session: boto3.Session = field(default=Factory(lambda: import_optional_dependency("boto3").Session()), kw_only=True)
    table_name: str = field(kw_only=True, metadata={"serializable": True})
    partition_key: str = field(kw_only=True, metadata={"serializable": True})
    value_attribute_key: str = field(kw_only=True, metadata={"serializable": True})
    partition_key_value: str = field(kw_only=True, metadata={"serializable": True})

    table: Any = field(init=False)

    def __attrs_post_init__(self) -> None:
        dynamodb = self.session.resource("dynamodb")

        self.table = dynamodb.Table(self.table_name)

    def store(self, memory: BaseConversationMemory) -> None:
        self.table.update_item(
            Key={self.partition_key: self.partition_key_value},
            UpdateExpression="set #attr = :value",
            ExpressionAttributeNames={"#attr": self.value_attribute_key},
            ExpressionAttributeValues={":value": memory.to_json()},
        )

    def load(self) -> Optional[BaseConversationMemory]:
        response = self.table.get_item(Key={self.partition_key: self.partition_key_value})

        if "Item" in response and self.value_attribute_key in response["Item"]:
            memory_value = response["Item"][self.value_attribute_key]

            memory = BaseConversationMemory.from_json(memory_value)

            memory.driver = self

            return memory
        else:
            return None
