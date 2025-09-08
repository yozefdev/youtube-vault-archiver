from logging import getLogger, StreamHandler, Formatter, DEBUG, INFO, ERROR
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime
import pytz


def configure_logging(app_path: Path, DEBUG_MODE: bool) -> None:
    """
    ロギングシステムを設定する

    Args:
        app_path (Path): アプリケーションのルートパス
        DEBUG_MODE (bool): デバッグモードの有効/無効
    """

    # ログディレクトリの作成
    log_dir = app_path / "logs"
    log_dir.mkdir(exist_ok=True)

    # タイムスタンプ付きファイル名の生成
    JST = pytz.timezone("Asia/Tokyo")
    timestamp = datetime.now(JST).strftime("%Y%m%d_%H%M%S")

    # 古いログファイルを削除（最新3件のみ保持）
    existing_logs = sorted(
        log_dir.glob("*.log"), key=lambda x: x.stat().st_mtime, reverse=True
    )
    for log_file in existing_logs[4:]:
        log_file.unlink()

    # フォーマッタの設定
    formatter = Formatter("[%(levelname)s] %(asctime)s - %(message)s (%(filename)s)")

    # ルートロガーの設定
    root_logger = getLogger()
    root_logger.setLevel(DEBUG)

    # 既存のハンドラをクリア（重複防止）
    root_logger.handlers.clear()

    # コンソール出力用ハンドラ
    stream_handler = StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(DEBUG if DEBUG_MODE else INFO)

    # 通常ログファイル用ハンドラ
    file_handler = RotatingFileHandler(
        log_dir / f"{timestamp}_log.log",
        maxBytes=1024 * 1024,  # 1MB
        backupCount=0,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(DEBUG)

    # エラーログファイル用ハンドラ
    error_handler = RotatingFileHandler(
        log_dir / f"{timestamp}_error.log",
        maxBytes=1024 * 1024,  # 1MB
        backupCount=0,
        encoding="utf-8",
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(ERROR)

    # ハンドラをルートロガーに追加
    root_logger.addHandler(stream_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
