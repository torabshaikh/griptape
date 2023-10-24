from typing import Callable, Optional, Any
from griptape.drivers import BaseSqlDriver
from attr import Factory, define, field
from sqlalchemy import create_engine, text, MetaData, Table
from sqlalchemy.engine import Engine
from sqlalchemy.exc import NoSuchTableError
from snowflake.connector import SnowflakeConnection


@define
class SnowflakeSqlDriver(BaseSqlDriver):
    connection_func: Callable[[], SnowflakeConnection] = field(kw_only=True)
    engine: Engine = field(
        default=Factory(
            # Creator bypasses the URL param
            # https://docs.sqlalchemy.org/en/14/core/engines.html#sqlalchemy.create_engine.params.creator
            lambda self: create_engine(
                "snowflake://not@used/db", creator=self.connection_func
            ),
            takes_self=True,
        ),
        kw_only=True,
    )

    @connection_func.validator
    def validate_connection_func(
        self, _, connection_func: Callable[[], SnowflakeConnection]
    ) -> None:
        snowflake_connection = connection_func()
        if not isinstance(snowflake_connection, SnowflakeConnection):
            raise ValueError(
                "The connection_func must return a SnowflakeConnection"
            )
        if not snowflake_connection.schema or not snowflake_connection.database:
            raise ValueError(
                "Provide a schema and database for the Snowflake connection"
            )

    @engine.validator
    def validate_engine_url(self, _, engine: Engine) -> None:
        if not engine.url.render_as_string().startswith("snowflake://"):
            raise ValueError("Provide a Snowflake connection")

    def execute_query(
        self, query: str
    ) -> Optional[list[BaseSqlDriver.RowResult]]:
        rows = self.execute_query_raw(query)

        if rows:
            return [BaseSqlDriver.RowResult(row) for row in rows]
        else:
            return None

    def execute_query_raw(self, query: str) -> Optional[list[dict[str, Any]]]:
        with self.engine.connect() as con:
            results = con.execute(text(query))

            if results.returns_rows:
                return [
                    {column: value for column, value in result.items()}
                    for result in results
                ]
            else:
                return None

    def get_table_schema(
        self, table: str, schema: Optional[str] = None
    ) -> Optional[str]:
        try:
            metadata_obj = MetaData()
            metadata_obj.reflect(bind=self.engine)
            table = Table(
                table,
                metadata_obj,
                schema=schema,
                autoload=True,
                autoload_with=self.engine,
            )
            return str([(c.name, c.type) for c in table.columns])
        except NoSuchTableError:
            return None
