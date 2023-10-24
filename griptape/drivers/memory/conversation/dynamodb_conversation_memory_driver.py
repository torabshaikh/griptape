import boto3
from attr import define, field, Factory
from typing import Optional
from griptape.drivers import BaseConversationMemoryDriver
from griptape.memory.structure import ConversationMemory


@define
class DynamoDbConversationMemoryDriver(BaseConversationMemoryDriver):
    session: boto3.Session = field(
        default=Factory(lambda: boto3.Session()), kw_only=True
    )
    table_name: str = field(kw_only=True)
    partition_key: str = field(kw_only=True)
    value_attribute_key: str = field(kw_only=True)
    partition_key_value: str = field(kw_only=True)

    table: any = field(init=False)

    def __attrs_post_init__(self) -> None:
        dynamodb = self.session.resource("dynamodb")

        self.table = dynamodb.Table(self.table_name)

    def store(self, memory: ConversationMemory) -> None:
        self.table.update_item(
            Key={self.partition_key: self.partition_key_value},
            UpdateExpression="set #attr = :value",
            ExpressionAttributeNames={"#attr": self.value_attribute_key},
            ExpressionAttributeValues={":value": memory.to_json()},
        )

    def load(self) -> Optional[ConversationMemory]:
        response = self.table.get_item(
            Key={self.partition_key: self.partition_key_value}
        )

        if "Item" in response and self.value_attribute_key in response["Item"]:
            memory_value = response["Item"][self.value_attribute_key]

            memory = ConversationMemory.from_json(memory_value)

            memory.driver = self

            return memory
        else:
            return None
