from __future__ import annotations

from textwrap import dedent
from typing import Union
from schema import Schema, Literal
from attr import define, field
from griptape.tools import BaseTool
from griptape.utils.decorators import activity
from griptape.artifacts import TextArtifact, ErrorArtifact, ListArtifact


@define
class ShopifyClient(BaseTool):
    storename: str = field(kw_only=True)
    access_token: str = field(kw_only=True)
    schema_endpoint: str = field(
        kw_only=True, default="myshopify.com/api/2023-07/graphql.json"
    )
    timeout: int = field(kw_only=True, default=30)


    @activity(
        config={
            "description": "Can be used to search for Shopify products",
            "schema": Schema(
                {
                    Literal(
                        "product_count",
                        description="How many products to retrieve.",
                    ): str,
                }
            ),
        }
    )
    def search(self, params: dict) -> ListArtifact | ErrorArtifact:
        from requests import post, exceptions
        values = params["values"]
        first = values.get("product_count", 10)

        url = f"https://{self.storename}.{self.schema_endpoint}"
        body = {
            "query": dedent(
                """
                        query getProducts($first: Int, $after: String) { 
                            products(first: $first, after: $after) { 
                                edges { 
                                    cursor node { 
                                        title 
                                    } 
                                },
                                pageInfo { 
                                    hasNextPage endCursor 
                                } 
                            } 
                        }
            """
            ),
            "variables": {"first": first},
        }

        try:
            response = post(
                url,
                json=body,
                headers={"X-Shopify-Storefront-Access-Token": self.access_token},
                timeout=self.timeout,
            ).json()
            if "errors" in response:
                return ErrorArtifact(response["errors"])
            else:
                print(response)
                return ListArtifact([
                    TextArtifact(edge["node"]["title"])
                    for edge in response["data"]["products"]["edges"]
                ])
        except exceptions.RequestException as err:
            return ErrorArtifact(str(err))

    @activity(
        config={
            "description": "Can be used to provide description of a product",
            "schema": Schema(
                {
                    Literal(
                        "product_description",
                        description="What is the description of the product.",
                    ): str,
                    Literal(
                        "first",
                        description="Returns up to the first n elements from the list.",
                    ): int,
                }
            ),
        }
    )
    def description(self, params: dict) -> ListArtifact | ErrorArtifact:
        from requests import post, exceptions
        values = params["values"]
        query = values.get("product_details")
        first = values.get("first", 3)

        url = f"https://{self.storename}.{self.schema_endpoint}"
        body = {
            "query": dedent(
                """
                        query searchProducts($query: String!, $first: Int) {
                            search(query: $query, first: $first, types: PRODUCT) {
                                edges {
                                    node {
                                        ...on Product {
                                            id
                                            title
                                            description
                                        }
                                    }
                                }
                            }
                        }
            """
            ),
            "variables": {"query": query, "first": first}
        }

        try:
            response = post(
                url,
                json=body,
                headers={"X-Shopify-Storefront-Access-Token": self.access_token},
                timeout=self.timeout,
            ).json()
            if "errors" in response:
                return ErrorArtifact(response["errors"])
            else:
                print(response)
                return ListArtifact([
                    TextArtifact(edge["node"]["title"])
                    for edge in response["data"]["search"]["edges"]
                ])
        except exceptions.RequestException as err:
            return ErrorArtifact(str(err))
