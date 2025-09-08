"""
ファイル移動モジュール
transcriptsディレクトリ内のマークダウンファイルをObsidianVaultに移動する
"""

import logging
import os
import shutil
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


def get_markdown_files(source_dir: str) -> List[str]:
    """
    指定ディレクトリ内のマークダウンファイル一覧を取得

    Args:
        source_dir: 検索対象ディレクトリ

    Returns:
        マークダウンファイルのパスリスト
    """
    if not os.path.exists(source_dir):
        logger.warning(f"ソースディレクトリが存在しません: {source_dir}")
        return []

    markdown_files = []
    for file_path in Path(source_dir).glob("*.md"):
        if file_path.is_file():
            markdown_files.append(str(file_path))

    return markdown_files


def move_files_to_vault(source_dir: str, vault_path: str) -> int:
    """
    transcriptsディレクトリ内のマークダウンファイルをObsidianVaultに移動

    Args:
        source_dir: 移動元ディレクトリ（transcripts）
        vault_path: 移動先ディレクトリ（ObsidianVault）

    Returns:
        移動したファイル数
    """
    if not vault_path:
        logger.info(
            "OBSIDIAN_VAULT_PATHが設定されていません。ファイル移動をスキップします。"
        )
        return 0

    if not os.path.exists(vault_path):
        logger.error(f"移動先ディレクトリが存在しません: {vault_path}")
        return 0

    if not os.path.isdir(vault_path):
        logger.error(f"移動先パスがディレクトリではありません: {vault_path}")
        return 0

    # マークダウンファイル一覧を取得
    markdown_files = get_markdown_files(source_dir)
    if not markdown_files:
        logger.info(f"移動対象のマークダウンファイルが見つかりません: {source_dir}")
        return 0

    moved_count = 0
    for file_path in markdown_files:
        try:
            file_name = os.path.basename(file_path)
            destination = os.path.join(vault_path, file_name)

            # 同名ファイルが存在する場合の処理
            if os.path.exists(destination):
                base_name, ext = os.path.splitext(file_name)
                counter = 1
                while True:
                    new_name = f"{base_name}_{counter}{ext}"
                    destination = os.path.join(vault_path, new_name)
                    if not os.path.exists(destination):
                        break
                    counter += 1
                logger.warning(
                    f"同名ファイルが存在するため名前を変更: {file_name} -> {os.path.basename(destination)}"
                )

            # ファイル移動
            shutil.move(file_path, destination)
            logger.info(f"ファイルを移動しました: {file_name} -> {vault_path}")
            moved_count += 1

        except Exception as e:
            logger.error(f"ファイル移動に失敗: {file_path} - {e}")

    return moved_count


def cleanup_empty_directories(directory: str) -> None:
    """
    空のディレクトリを削除

    Args:
        directory: 対象ディレクトリ
    """
    try:
        if os.path.exists(directory) and os.path.isdir(directory):
            if not os.listdir(directory):
                os.rmdir(directory)
                logger.info(f"空のディレクトリを削除しました: {directory}")
    except Exception as e:
        logger.error(f"ディレクトリ削除に失敗: {directory} - {e}")
