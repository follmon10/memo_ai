# Memo AI

**Notion をメモリとして使用するステートレス AI 秘書**です。
ユーザーの入力（テキスト、画像）を AI で解析し、構造化された Notion エントリに変換します。

> **必読**: 新しいタスクを開始する前に、必ずこのファイルを読んでください。
> 英語で思考し、ユーザーの言語で返答する。Implementation Plan、コードコメントはユーザーの言語で記述する。

---

## Do (必ず行う)

- `.env` で設定管理。APIキーのハードコード禁止
- `DEBUG_MODE` を尊重。`False` の場合はデバッグ機能を隠す
- コード変更後は**手動リグレッションテスト**を実施（主要機能: Chat、Save、Content、Settings）
- **作業完了時のチェックリスト**を必ず実行:
  - Python: `pytest -v --tb=short` 全パス確認
  - JavaScript: `jsconfig.json` の型チェック有効時、IDE問題パネルでエラー0件確認
  - 意図した変更がすべて適用されているか確認
  - やり残しがないか、不要なものが残ってないか確認
  - 似た問題が他のファイルにないか確認（横断確認の原則）
- **横断確認の原則**: 1ファイルの問題を修正したら、同種の全ファイルを確認する
- ベストプラクティスを調査してから実装する

## Ask (事前確認が必要)

- `requirements.txt` への新パッケージ追加
- Notion データベーススキーマや API 呼び出しの変更
- コアモジュール (`main.js`, `chat.js`, `index.py`) の大規模リファクタリング
- API エンドポイントのシグネチャ変更

## Don't (禁止事項)

- 秘密情報のコミット (`.env`, API キー)
- SQLite, Postgres 等のローカル DB 追加提案 (Notion のみ使用)
- Webpack, Vite 等のビルドツール導入
- React, Vue, Next.js への移行提案
- リダイレクトの使用禁止 (npm run type-check > tsc_errors.txt 2>&1 など)　使用許可を自動化できないため。

---

## Commands (ファイルスコープ優先)

```bash
# Python: 単一ファイルのテスト
pytest tests/test_specific.py -v --tb=short

# Python: 単一ファイルのlint
ruff check api/specific_file.py

# 全テスト（コミット前のみ）
pytest -v --tb=short

# 開発サーバー起動
python -m uvicorn api.index:app --reload --host 0.0.0.0
```

---

## Project Structure (ポインタ)

```
memo_ai/
├── AGENTS.md           # このファイル (全体ルール)
├── api/
│   ├── AGENTS.md       # Backend固有ルール
│   ├── index.py        # FastAPI アプリケーション
│   └── endpoints.py    # API ルート定義
├── public/
│   ├── AGENTS.md       # HTML/CSS固有ルール
│   ├── index.html      # エントリHTML
│   ├── style.css       # グローバルスタイル
│   └── js/             # JavaScript モジュール
│       ├── AGENTS.md   # JavaScript固有ルール
│       ├── main.js     # エントリポイント
│       └── types.d.ts  # グローバル型定義
├── tests/
│   ├── AGENTS.md       # テスト固有ルール
│   └── test_*.py       # pytest テストスイート
└── docs/
    └── AGENTS.md       # 開発環境問題の詳細ガイド
```

**参照**:
- トラブルシューティング・デバッグパターン → `docs/AGENTS.md`
- 環境変数テンプレート → `.env.example`

---

## When Stuck (行き詰まった時)

- 推測で大きな変更をしない。まず計画を提示して確認を求める
- 2回パッチを当てても直らない場合はフロー全体を図示する
- ベストプラクティスを調査してから対処する
- 対症療法は最大2回まで

---

## Key Patterns (重要パターン)

### 設計方針
| 原則 | 説明 |
| :--- | :--- |
| **ステートレス** | 内部DBなし。永続化は Notion API 経由のみ |
| **ローカル優先** | `uvicorn` + `.env` でのローカル開発に最適化 |
| **クロスプラットフォーム** | 起動コマンドはOS共通、設定は `.env` に集約 |

### リグレッション予防
- **API契約テスト**: `test_api_contract.py` がJS↔Backend整合性を自動検証（`pytest`実行時）
- API エンドポイント変更前に `public/` 内で該当文字列を検索し、全参照箇所を更新する
- CSS 変更時は**デスクトップ**と**モバイル**の両方で確認する
- AGENTS.mdが500行を超えたら、重要度の低い項目を要約または `docs/` に移動する

---

## 技術スタック

**Backend**: Python 3.9+, FastAPI, Uvicorn, LiteLLM  
**Frontend**: Vanilla JavaScript (ES6+), Vanilla CSS  
**禁止**: React, Vue, Webpack, Vite (軽量・シンプルを維持)

---

## 設計原則

### コード品質
- **デッドコード削除**: テスト専用関数は本番に不要。`grep_search`で使用箇所0件なら削除
- **DRY原則**: 3回以上の重複→ヘルパー関数に抽出（例：スキーマ整形、プロパティ値抽出）
- **ロギング統一**: バックエンドは `logger.info()`、フロントエンドは `App.debug.enabled` でガード
- **関数の責務**: 1関数50行超→分割検討。重複コードは即座にヘルパー化
