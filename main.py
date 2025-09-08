import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, List

import dotenv

from src import config
from src.gemini_api import generate_transcript, generate_article
from src.logger import configure_logging
from src.youtube import get_playlist_video_infos, remove_from_playlist
from src.md_writer import save_transcript_to_markdown
from src.file_mover import move_files_to_vault, cleanup_empty_directories

dotenv.load_dotenv()

logger = logging.getLogger(__name__)
GEMINI_API_KEY = config.GEMINI_API_KEY
if not GEMINI_API_KEY:
    logger.error("環境変数 GEMINI_API_KEY が設定されていません。")
    sys.exit(1)


async def process_video(
    video: Dict[str, str], index: int, total: int, semaphore: asyncio.Semaphore
) -> bool:
    """
    動画を非同期で処理する

    Args:
        video: 動画情報
        index: 処理順番
        total: 総動画数
        semaphore: 同時実行数制限

    Returns:
        処理成功の可否
    """
    async with semaphore:
        logger.info(f"[{index}/{total}] 処理中: {video['title']}")

        try:
            # 文字起こし
            transcript = await generate_transcript(config.GEMINI_API_KEY, video["url"])
            if not transcript:
                logger.warning(f"[{index}/{total}] 文字起こしに失敗: {video['title']}")
                return False

            # 記事生成
            article = await generate_article(config.GEMINI_API_KEY, transcript)
            if not article:
                logger.warning(f"[{index}/{total}] 記事生成に失敗: {video['title']}")
                return False

            # マークダウンファイルに保存（同期処理）
            saved_path = save_transcript_to_markdown(video, transcript, article)
            logger.info(f"[{index}/{total}] 保存完了: {saved_path}")

            # 再生リストから削除（同期処理）
            remove_from_playlist(video["playlist_item_id"])

            return True

        except Exception as e:
            logger.error(f"[{index}/{total}] エラー発生: {video['title']} - {e}")
            return False


async def main_async() -> None:
    """非同期メイン処理"""
    # 再生リストから動画情報一覧を取得
    video_infos = get_playlist_video_infos()
    if not video_infos:
        logger.info("処理する動画がありません。")
        sys.exit(0)
    logger.debug(f"対象の動画数: {len(video_infos)}")

    # 同時実行数の制限（APIレート制限対策）
    semaphore = asyncio.Semaphore(config.MAX_CONCURRENT)

    # 非同期タスクの作成
    tasks = [
        process_video(video, i, len(video_infos), semaphore)
        for i, video in enumerate(video_infos, 1)
    ]

    # すべてのタスクを並行実行
    logger.info(f"並行処理を開始します（最大同時実行数: {config.MAX_CONCURRENT}）")
    results = await asyncio.gather(*tasks)

    # 処理成功数をカウント
    processed_count = sum(1 for result in results if result)

    if not config.OBSIDIAN_VAULT_PATH:
        logger.info(
            "OBSIDIAN_VAULT_PATHが設定されていません。ファイル移動をスキップします。"
        )
        return

    # 全処理完了後、ObsidianVaultへファイル移動
    if processed_count > 0:
        logger.info("全ての処理が完了しました。ファイル移動を開始します。")
        moved_count = move_files_to_vault("output", config.OBSIDIAN_VAULT_PATH)
        if moved_count > 0:
            logger.info(f"{moved_count}個のファイルをObsidianVaultに移動しました。")
            cleanup_empty_directories("output")
        else:
            logger.info("移動対象のファイルがありませんでした。")
    else:
        logger.info("処理されたファイルがないため、移動処理をスキップします。")


def main() -> None:
    """同期的なエントリーポイント"""
    asyncio.run(main_async())


if __name__ == "__main__":
    configure_logging(Path(__file__).parent, DEBUG_MODE=config.DEBUG_MODE)
    main()
