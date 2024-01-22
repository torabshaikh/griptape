from __future__ import annotations

from attr import define

from griptape.artifacts import ImageArtifact
from griptape.rules import Ruleset
from griptape.engines import BaseImageGenerationEngine


@define
class OutpaintingImageGenerationEngine(BaseImageGenerationEngine):
    def run(
        self,
        prompts: list[str],
        image: ImageArtifact,
        mask: ImageArtifact,
        negative_prompts: list[str] | None = None,
        rulesets: list[Ruleset] | None = None,
        negative_rulesets: list[Ruleset] | None = None,
    ) -> ImageArtifact:
        prompts = self._ruleset_to_prompts(prompts, rulesets)
        negative_prompts = self._ruleset_to_prompts(negative_prompts, negative_rulesets)

        return self.image_generation_driver.run_image_outpainting(
            prompts, image=image, mask=mask, negative_prompts=negative_prompts
        )