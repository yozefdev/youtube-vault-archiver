"""
マークダウンファイル作成モジュール
文字起こし結果をマークダウンファイルとして保存する
"""

import os
import re
from typing import Dict
from datetime import datetime

import logging

logger = logging.getLogger(__name__)


def sanitize_filename(filename: str, max_length: int = 200) -> str:
    """
    ファイル名として使用可能な文字列に変換

    Args:
        filename: サニタイズするファイル名
        max_length: ファイル名の最大長

    Returns:
        サニタイズされたファイル名
    """
    # 使用禁止文字を置換
    filename = re.sub(r'[<>:"/\\|?*]', "", filename)
    # 連続するスペースを1つに
    filename = re.sub(r"\s+", " ", filename)
    # 先頭と末尾の空白を削除
    filename = filename.strip()
    # ピリオドで終わる場合は削除（Windowsの制限）
    filename = filename.rstrip(".")

    # 空になった場合のデフォルト名
    if not filename:
        filename = "untitled"

    # 長さ制限
    if len(filename) > max_length:
        filename = filename[:max_length].rstrip()

    return filename


def get_unique_filename(base_path: str, filename: str, extension: str = ".md") -> str:
    """
    重複しないファイル名を生成

    Args:
        base_path: 保存先ディレクトリパス
        filename: 基本となるファイル名
        extension: ファイル拡張子

    Returns:
        重複しないファイルパス
    """
    # ファイル名をサニタイズ
    safe_filename = sanitize_filename(filename)

    # 基本のファイルパス
    file_path = os.path.join(base_path, f"{safe_filename}{extension}")

    # ファイルが存在しない場合はそのまま返す
    if not os.path.exists(file_path):
        return file_path

    # 重複する場合は番号を付与
    counter = 2
    while True:
        numbered_filename = f"{safe_filename}_{counter}"
        file_path = os.path.join(base_path, f"{numbered_filename}{extension}")
        if not os.path.exists(file_path):
            return file_path
        counter += 1


def save_transcript_to_markdown(
    video_info: Dict[str, str],
    transcript: str,
    article: str,
    output_dir: str = "output",
) -> str:
    """
    文字起こし結果をマークダウンファイルとして保存

    Args:
        video_info: 動画情報（title, channel, published_at, url等を含む辞書）
        transcript: 文字起こしテキスト
        output_dir: 出力ディレクトリ

    Returns:
        保存したファイルパス
    """
    # 出力ディレクトリを作成
    os.makedirs(output_dir, exist_ok=True)

    # ファイル名を動画タイトルから生成
    title = video_info.get("title", "untitled")
    filename = f"[YouTube]{title}"
    file_path = get_unique_filename(output_dir, filename)

    # マークダウンコンテンツを作成
    content = create_markdown_content(video_info, transcript, article)

    # ファイルに書き込み
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info("  → マークダウンファイルを保存: %s", file_path)
    return file_path


def create_markdown_content(
    video_info: Dict[str, str], transcript: str, article: str
) -> str:
    """
    マークダウンコンテンツを生成

    Args:
        video_info: 動画情報
        transcript: 文字起こしテキスト

    Returns:
        マークダウン形式の文字列
    """
    # タイトル
    title = video_info.get("title", "Untitled")

    # チャンネル名
    channel = video_info.get("channel", "Unknown")

    # 投稿日時をフォーマット
    published_at = video_info.get("published_at", "")
    if published_at:
        try:
            # ISO 8601形式をパース
            dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            published_date = dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            published_date = published_at[:10] if len(published_at) >= 10 else "Unknown"
    else:
        published_date = "Unknown"

    # URL
    url = video_info.get("url", "")

    # video_idを取得（URLまたは直接video_idから）
    video_id = video_info.get("video_id", "")
    if not video_id and url:
        # URLからvideo_idを抽出
        if "watch?v=" in url:
            video_id = url.split("watch?v=")[1].split("&")[0]
        elif "youtu.be/" in url:
            video_id = url.split("youtu.be/")[1].split("?")[0]

    # YouTube埋め込みiframeを生成
    embed_html = ""
    if video_id:
        embed_html = f"""<iframe 
src="https://www.youtube.com/embed/{video_id}?autoplay=0&mute=1" 
frameborder="0" allowfullscreen style="width: 100%; aspect-ratio: 16/9;"></iframe>"""

    # YAMLフロントマターとマークダウンコンテンツを構築
    markdown = f"""---
title: {title}
channel: {channel}
source: {url}
uploaded: {published_date}
---

# {title}

{embed_html}

{article}

## 文字起こし結果
{transcript}
"""

    return markdown


def append_processing_note(file_path: str, note: str) -> None:
    """
    マークダウンファイルに処理メモを追加

    Args:
        file_path: マークダウンファイルのパス
        note: 追加するメモ
    """
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(f"\n\n---\n\n*処理メモ: {note}*\n")
