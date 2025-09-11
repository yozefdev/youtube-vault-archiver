# YouTube Vault Archiver

YouTube再生リストの動画を自動で文字起こし・記事生成し、処理済み動画を再生リストから削除する自動化ツール。
## 作成背景

YouTubeで見た動画の内容をObsidianのVaultに保存し、知識管理システムに組み込むことを目的として作成。再生リストに追加した動画を自動的に文字起こしして、記事を生成し、マークダウン形式で出力することで、Obsidianでの管理を容易にする。

## 使用シーン

1. **再生リストへ追加**: 専用の再生リスト（例：「ノート化する」）に動画を追加
2. **自動処理**: 本システムを実行すると、再生リスト内の動画を並行処理
   - 動画の文字起こしを実行
   - 日本語の要約記事を自動生成
   - マークダウンファイルとして保存
   - 処理済み動画を再生リストから自動削除
3. **Obsidianへ自動移動**: 生成されたマークダウンファイルを自動でObsidianのVaultに移動
4. **知識管理**: ハッシュタグ付きの記事として知識管理システムに組み込む

## 機能

- YouTube再生リストから動画情報を取得
- Gemini APIによる音声文字起こし（ダウンロード不要）
- Gemini APIによる日本語記事の自動生成（要約とハッシュタグ付き）
- **非同期処理による並行実行**（同時処理数は環境変数で設定可能）
- 文字起こし結果と記事をマークダウンファイルとして保存
- ObsidianVaultへの自動ファイル移動
- 処理成功後、自動的に再生リストから削除（オプション）
- OAuth認証による安全な再生リスト操作
- 型ヒント対応による開発効率向上

## 必要要件

- Python 3.13以上
- [uv](https://docs.astral.sh/uv/) パッケージマネージャー
- Google Cloud Platform アカウント
- YouTube Data API v3 有効化
- Gemini API キー

## セットアップ

### 1. 依存関係のインストール

```bash
uv sync
```

### 2. APIの設定

1. [Google Cloud Console](https://console.cloud.google.com/)でYouTube Data API v3を有効化し、OAuth 2.0クライアントIDを作成
2. [Google AI Studio](https://aistudio.google.com/)でGemini APIキーを取得

### 3. 環境設定

```bash
cp .env.example .env
```

`.env`ファイルを編集：

```env
# YouTube再生リストID（必須）
PLAYLIST_ID=PLxxxxxxxxxxxxxx

# Gemini APIキー（必須）
GEMINI_API_KEY=AIxxxxxxxxxxxxxxxxxx

# 再生リストから動画を削除するか
DELETE_FROM_PLAYLIST=true  # falseで削除無効

# ObsidianVaultのパス（オプション）
OBSIDIAN_VAULT_PATH=/path/to/obsidian/vault

# デバッグモード
DEBUG_MODE=false  # trueでデバッグログ出力

# 同時処理する動画の最大数（デフォルト: 3）
MAX_CONCURRENT=3  # APIレート制限に注意
```

## 使用方法

```bash
uv run python main.py
```

初回実行時はブラウザでGoogle認証が必要です。

## 処理の流れ

1. 指定された再生リストの動画URLを取得
2. **非同期処理で複数動画を並行処理**（MAX_CONCURRENTで設定可能）
3. 各動画URLをGemini APIに送信して文字起こし
4. 文字起こし結果から日本語の要約記事を生成
5. 結果をマークダウンファイルとして保存
6. 処理成功時、設定により再生リストから削除
7. すべての処理完了後、ObsidianVaultへファイルを自動移動
8. エラー時はスキップして次の動画を処理

## 出力形式

各動画の文字起こし結果は以下の形式で保存されます：

```markdown
---
title: 動画タイトル
channel: チャンネル名
source: https://youtube.com/watch?v=...
uploaded: YYYY-MM-DD HH:MM:SS
---

# 動画タイトル

<iframe 
src="https://www.youtube.com/embed/VIDEO_ID?autoplay=0&mute=1" 
frameborder="0" allowfullscreen style="width: 100%; aspect-ratio: 16/9;"></iframe>

（日本語の要約記事）

#ハッシュタグ1 #ハッシュタグ2 #ハッシュタグ3

## 文字起こし結果

（Gemini APIによる文字起こし結果）
```

## ファイル構成

```
youtube-vault-archiver/
├── main.py                 # メインスクリプト（非同期処理対応）
├── pyproject.toml          # プロジェクト設定・依存関係
├── uv.lock                 # 依存関係ロックファイル
├── .python-version         # Pythonバージョン指定
├── .env.example           # 環境変数テンプレート
├── .env                   # 環境変数（要作成）
├── .gitignore            # Git除外設定
├── client_secret.json    # OAuth認証情報（要配置）
├── token.json            # 認証トークン（自動生成）
├── src/                   # ソースコードディレクトリ
│   ├── config.py          # 設定管理
│   ├── gemini_api.py      # Gemini API処理（非同期対応）
│   ├── logger.py          # ロギング設定
│   ├── md_writer.py       # マークダウン保存処理
│   ├── file_mover.py      # ファイル移動処理
│   └── youtube.py         # YouTube API処理
├── output/                # マークダウン出力先（自動生成）
├── log/                   # ログファイル出力先（自動生成）
└── docs/                  # ドキュメント
    └── requirements.md    # 要件定義
```