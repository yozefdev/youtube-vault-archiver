import asyncio
import logging

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


async def generate_transcript(API_KEY: str, video_url: str) -> str:
    """非同期で動画の文字起こしを生成"""
    client = genai.Client(api_key=API_KEY)

    # 同期的なAPI呼び出しを非同期で実行
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=types.Content(
                parts=[
                    types.Part(file_data=types.FileData(file_uri=video_url)),
                    types.Part(text="Transcribe this video."),
                ]
            ),
        ),
    )

    if response.text:
        logger.debug(f"Transcript: {response.text[:20]}...")
        return response.text
    else:
        logger.error("Transcriptが生成されませんでした。")
        return ""


async def generate_article(API_KEY: str, transcript: str) -> str:
    """非同期で記事を生成"""
    client = genai.Client(api_key=API_KEY)

    contents = f"""
    Please execute the following workflow:\n
    1. Create a summary article based on the transcript provided below.\n
    2. Extract keywords from the article and add them as hashtags at the bottom.\n\n
    
    - Create the article in Japanese.\n
    - Create the article in markdown format.\n
    - Focus on key points and include as much information as possible.\n
    - **Important**: Output only the article. No additional explanatory text is needed.\n
    - Hashtags start with "#" and multiple hashtags can be specified separated by half-width spaces.\n
    - Please note that including "." after "#" will prevent recognition as hashtags.\n
    - Select main keywords for hashtags to summarize the content of the file.\n
    - Use company names, product names, service names, specific person names, and specific technical terms mentioned in the article as hashtags.\n\n
    
    ====Transcript below====\n
    {transcript}
    """

    # 同期的なAPI呼び出しを非同期で実行
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: client.models.generate_content(
            model="models/gemini-2.5-pro", contents=contents
        ),
    )

    if response.text:
        logger.debug(f"Article: {response.text[:20]}...")
        return response.text
    else:
        logger.error("Articleが生成されませんでした。")
        return ""
