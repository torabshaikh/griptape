# OpenWeatherClient

The [OpenWeatherClient](../../reference/griptape/tools/openweather_client/tool.md) enables LLMs to use [OpenWeatherMap](https://openweathermap.org/).

```python
import os
from griptape.structures import Agent
from griptape.tools import OpenWeatherClient

agent = Agent(
    tools=[
        OpenWeatherClient(
            api_key=os.environ["OPENWEATHER_API_KEY"],
        ),
    ]
)

agent.run("What's the weather currently like in San Francisco?")
```
