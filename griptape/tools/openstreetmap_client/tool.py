import dataclasses
from typing import List
import overpy
from attr import define, field, Factory
from griptape.artifacts import ErrorArtifact, TextArtifact
from griptape.tools import BaseTool
from schema import Schema, Literal
from griptape.utils.decorators import activity


@define
class OpenStreetMapClient(BaseTool):
    api: overpy.Overpass = field(default=Factory(lambda: overpy.Overpass()), init=False)

    @activity(
        config={
            "description": "Can be used to fetch features around a latitude/longitude coordinate pair. Features"
                           "returned include roads, paths, railways, buildings, businesses, and points of interest.",
            "schema": Schema({
                Literal(
                    "latitude",
                    description="Floating-point latitude of the location's latitude-longitude coordinate pair."
                ): float,
                Literal(
                    "longitude",
                    description="Floating-point longitude of the location's latitude-longitude coordinate pair."
                ): float,
                Literal(
                    "radius",
                    description="Search radius in meters around the point described by the coordinate."
                ): int,
            }),
        }
    )
    def get_features_around_point(self, params: dict) -> TextArtifact | ErrorArtifact:
        latitude = params["values"].get("latitude")
        longitude = params["values"].get("longitude")
        radius = params["values"].get("radius")

        try:
            area_features = self._query_nearby_features(latitude, longitude, radius)
            return TextArtifact(area_features.describe(
                include_nodes=True,
                include_ways=True,
                include_relations=True,
                include_enclosing_features=True,
            ))

        except Exception as e:
            return ErrorArtifact(f"Error fetching features around point: {e}")

    def _query_nearby_features(self, lat: float, lon: float, radius: int) -> any:
        query = f"""
        [out:json];
        (
          nwr(around:{radius},{lat},{lon});
        );
        out body;
        out tags;
        >;
        out skel qt;
        """

        result = self.api.query(query)

        nearby_features = self.AreaFeatures(
            radius=radius,
            lat=lat,
            lon=lon,
            nodes=result.nodes,
            ways=result.ways,
            relations=result.relations,
            enclosing_features=self._query_enclosing_features(result.nodes[0]) if len(result.nodes) > 0 else None,
        )

        return nearby_features

    def _query_enclosing_features(self, node: overpy.Node) -> List[str]:
        query = f"""
        [out:json];
        (
            node({node.id}) -> .a;
            .a is_in -> .b;
            way(pivot.b);
            >;
        );
        out body;
        """

        result = self.api.query(query)
        return [area.tags.get("name") for area in result.areas]

    @dataclasses.dataclass
    class AreaFeatures:
        radius: int
        lat: float
        lon: float
        nodes: List[overpy.Node]
        ways: List[overpy.Way]
        relations: List[overpy.Relation]
        enclosing_features: List[str]

        def __str__(self):
            return self.describe(
                include_nodes=True,
                include_ways=True,
                include_relations=True,
                include_enclosing_features=True
            )

        def describe(
                self,
                include_nodes=False,
                include_ways=False,
                include_relations=False,
                include_enclosing_features=False
        ):
            desc = [f"the following features are within a {self.radius} meter "
                    f"radius of the coordinates {self.lat}, {self.lon}:"]
            if include_nodes:
                for node in self.nodes:
                    if len(node.tags) > 0:
                        desc.append(self._describe_feature(node))

            if include_ways:
                for way in self.ways:
                    if len(way.tags) > 0:
                        desc.append(self._describe_feature(way))

            if include_relations:
                for relation in self.relations:
                    if len(relation.tags) > 0:
                        desc.append(self._describe_feature(relation))

            if include_enclosing_features and self.enclosing_features:
                enclosing_desc = [f"this place is within the following regions:"]
                for enclosing_feature in self.enclosing_features:
                    enclosing_desc.append(f" - {enclosing_feature}")

                desc.append("\n".join(enclosing_desc))

            return "\n\n".join(desc)

        @staticmethod
        def _describe_feature(feature: overpy.Node | overpy.Way | overpy.Relation) -> str:
            feature_desc = [f"feature id: {feature.id}"]
            if "name" in feature.tags:
                feature_desc.append(f"name: {feature.tags['name']}")
                del(feature.tags["name"])

            # TODO: many tags returns lots of uninteresting data that
            # TODO: has a negative impact on cost and time performance.
            for tag in feature.tags:
                if len(feature_desc) >= 4:
                    break

                feature_desc.append(f"{tag}: {feature.tags[tag]}")

            return "\n".join(feature_desc)
