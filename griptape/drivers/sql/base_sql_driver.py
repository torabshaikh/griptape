from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Any
from attr import define


@define
class BaseSqlDriver(ABC):
    @dataclass
    class RowResult:
        cells: dict[str, Any]

    @abstractmethod
    def execute_query(self, query: str) -> Optional[list[RowResult]]:
        ...

    @abstractmethod
    def execute_query_raw(self, query: str) -> Optional[list[dict[str, Any]]]:
        ...

    @abstractmethod
    def get_table_schema(
        self, table: str, schema: Optional[str] = None
    ) -> Optional[str]:
        ...
