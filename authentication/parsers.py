from typing import Iterator
from langchain.document_loaders.base import BaseBlobParser
from langchain.document_loaders.blob_loaders import Blob
from langchain.schema import Document
from deepgram import Deepgram
import asyncio

class DeepgramParser(BaseBlobParser):
    """Transcribe and parse audio files.
    Audio transcription is with Deepgram."""

    DEEPGRAM_API_KEY = '81d68bde45651fc7c1f0bb8e67cc59571520e732'

    async def parse(self, audio_file):
        deepgram = Deepgram(self.DEEPGRAM_API_KEY)
        response = await asyncio.create_task(
            deepgram.transcription.prerecorded(
                {
                    'buffer': open(audio_file, 'rb'),
                    'mimetype': 'audio/wav'  # change this to match your audio file format
                },
                {
                    'punctuate': True,
                    'model': 'general',  # change this to match your use case
                }
            )
        )
        return response["results"]["channels"][0]["alternatives"][0]["transcript"]

    def lazy_parse(self, blob: Blob) -> Iterator[Document]:
        """Lazily parse the blob."""
        transcript = asyncio.run(self.parse(blob.path))
        yield Document(
            page_content=transcript,
            metadata={"source": blob.source},
        )
