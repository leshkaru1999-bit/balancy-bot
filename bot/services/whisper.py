import openai
import tempfile
import os
import aiohttp
from bot.config import OPENAI_API_KEY

client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)


async def download_voice(file_url: str) -> str:
    """Скачивает .ogg файл из Telegram и сохраняет во временный файл."""
    async with aiohttp.ClientSession() as session:
        async with session.get(file_url) as resp:
            resp.raise_for_status()
            suffix = ".ogg"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
                f.write(await resp.read())
                return f.name


async def transcribe_audio(file_path: str) -> str:
    """
    Отправляет аудиофайл в OpenAI Whisper и возвращает расшифрованный текст.
    Whisper отлично понимает русский язык, сленг и акценты.
    """
    try:
        with open(file_path, "rb") as audio_file:
            transcript = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
        return transcript.strip()
    finally:
        # Удаляем временный файл в любом случае
        if os.path.exists(file_path):
            os.unlink(file_path)


async def voice_to_text(file_url: str) -> str:
    """Полный пайплайн: URL → скачать → расшифровать → текст."""
    file_path = await download_voice(file_url)
    return await transcribe_audio(file_path)
