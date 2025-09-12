#!/usr/bin/env python3
"""
YouTube再生リストから動画URL一覧を取得し、
処理後に再生リストから削除するスクリプト
"""

import logging
import os
from pathlib import Path
from typing import Dict, List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from . import config

logger = logging.getLogger(__name__)

# スコープの定義（再生リスト操作に必要な権限）
SCOPES = ["https://www.googleapis.com/auth/youtube"]


def authenticate():
    """
    YouTube API の認証を行う

    Returns:
        認証済みのYouTube APIクライアント
    """
    project_root = Path(__file__).parent.parent
    creds = None

    # token.json ファイルから既存の認証情報を読み込み
    if os.path.exists(project_root / "token.json"):
        try:
            creds = Credentials.from_authorized_user_file(
                project_root / "token.json", SCOPES
            )
        except Exception as e:
            logger.error("認証トークンの読み込みに失敗: %s", e)

    # 認証情報が無効な場合は再認証
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                logger.error("トークンのリフレッシュに失敗: %s", e)
                creds = None

        # 新規認証フローの実行
        if not creds:
            if not (project_root / "client_secret.json").exists():
                raise FileNotFoundError(
                    "client_secret.json が見つかりません。"
                    "Google Cloud Console から OAuth 2.0 クライアントIDをダウンロードしてください。"
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                project_root / "client_secret.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        # 認証情報を保存
        with open(project_root / "token.json", "w") as token:
            token.write(creds.to_json())

    # YouTube API クライアントを作成
    youtube = build("youtube", "v3", credentials=creds)
    logger.info("YouTube API 認証成功")
    return youtube


def get_playlist_video_infos() -> List[Dict[str, str]]:
    """
    再生リストから動画情報一覧を取得

    Args:
        playlist_id: YouTube再生リストID

    Returns:
        動画情報のリスト（URL、タイトル、playlist_item_id等を含む辞書のリスト）
    """
    youtube = authenticate()
    videos = []
    next_page_token = None

    try:
        while True:
            # 再生リストの動画を取得
            request = youtube.playlistItems().list(
                part="snippet,contentDetails",
                playlistId=config.PLAYLIST_ID,
                maxResults=50,
                pageToken=next_page_token,
            )
            response = request.execute()

            # 動画IDを収集
            video_ids = []
            playlist_items = {}

            for item in response.get("items", []):
                video_id = item["contentDetails"]["videoId"]
                video_ids.append(video_id)
                playlist_items[video_id] = item

            # 動画の詳細情報を取得（公開日時を含む）
            if video_ids:
                video_request = youtube.videos().list(
                    part="snippet", id=",".join(video_ids)
                )
                video_response = video_request.execute()

                # 動画情報を結合
                for video in video_response.get("items", []):
                    video_id = video["id"]
                    playlist_item = playlist_items[video_id]

                    video_info = {
                        "playlist_item_id": playlist_item[
                            "id"
                        ],  # 再生リストからの削除に必要
                        "video_id": video_id,
                        "title": video["snippet"]["title"],
                        "channel": video["snippet"].get("channelTitle", "Unknown"),
                        "published_at": video["snippet"].get(
                            "publishedAt", ""
                        ),  # 動画の公開日時
                        "url": f"https://www.youtube.com/watch?v={video_id}",
                    }
                    videos.append(video_info)

            # 次のページがあるか確認
            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break

        logger.info("再生リストから %d 件の動画を取得しました", len(videos))
        return videos

    except HttpError as e:
        logger.error("動画リストの取得に失敗: %s", e)
        return []


def remove_from_playlist(playlist_item_id: str) -> bool:
    """
    再生リストから動画を削除

    Args:
        playlist_item_id: 再生リスト内の動画ID

    Returns:
        削除成功の可否
    """
    # 環境変数から削除設定を確認
    if not config.DELETE_FROM_PLAYLIST:
        logger.info("  → 再生リストからの削除はスキップ（設定により無効）")
        return False

    try:
        youtube = authenticate()
        request = youtube.playlistItems().delete(id=playlist_item_id)
        request.execute()
        logger.info("  → 再生リストから削除しました")
        return True
    except HttpError as e:
        logger.error("  → 再生リストからの削除に失敗: %s", e)
        return False
