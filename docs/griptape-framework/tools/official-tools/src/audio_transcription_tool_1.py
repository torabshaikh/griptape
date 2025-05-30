from griptape.drivers.audio_transcription.openai import OpenAiAudioTranscriptionDriver
from griptape.structures import Agent
from griptape.tools.audio_transcription.tool import AudioTranscriptionTool

driver = OpenAiAudioTranscriptionDriver(model="whisper-1")

tool = AudioTranscriptionTool(
    off_prompt=False,
    audio_transcription_driver=driver,
)

Agent(tools=[tool]).run(
    "Transcribe the following audio file: /Users/andrew/code/griptape/tests/resources/sentences2.wav"
)
