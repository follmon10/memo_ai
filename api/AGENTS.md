# Backend (API) - Agent Instructions

このディレクトリは **FastAPI + Python** によるバックエンド実装です。

---

## Backend-Specific Rules

### Do
- Pydantic モデルを使用してリクエスト/レスポンスを型定義する
- `api/config.py` から環境変数を読み込む（直接 `os.getenv()` しない）
- 構造化ログを使用（`api/logger.py` 経由）
- 非同期処理には `async`/`await` を使用する
- テストには `pytest` + モック (`unittest.mock`) を使用する

### Don't
- `api/index.py` に新しいエンドポイントを追加しない → `api/endpoints.py` に追加する
- グローバル変数で状態を保持しない（ステートレス原則）
- ハードコードされたタイムアウト値を使用しない → 設定ファイルから取得する
- コマンド実行時のリダイレクトの使用禁止 (2>&1など)　使用許可を自動化できないため。

---

## Testing Rules

### テストファイル構成
| ファイル | 目的 |
| :--- | :--- |
| `conftest.py` | 共通フィクスチャ、マーカー登録、UTF-8出力設定 |
| `test_current_api.py` | 現API仕様のスモークテスト |
| `test_enhanced.py` | 境界値・ロジックテスト |
| `test_gap_coverage.py` | エラー処理・タイムアウト |
| `test_advanced_scenarios.py` | セキュリティ・並行性 |
| `test_critical_paths.py` | 統合フロー |
| `test_regression_schemas.py` | スキーマ整合性 |
| `test_rate_limiter.py` | レート制限機能 |
| `test_llm_client.py` | LLM API連携・リトライ |
| `test_ai_internal.py` | プロンプト構築・JSON修復 |
| `test_model_discovery.py` | モデル検出・キャッシュ |
| `test_html_js_consistency.py` | HTML/JSセレクター整合性 |
| `test_api_contract.py` | JS↔Backend API契約整合性 |

### モックパス規則（重要）
エンドポイントを別モジュールに移行した場合、テストのモックパスも更新が必要:

```python
# 移行前: api/index.py にエンドポイントがある場合
@patch("api.index.some_function")

# 移行後: api/endpoints.py に移行した場合
@patch("api.endpoints.some_function")
```

### ベストプラクティス (pytest + PowerShell)
- `pytest --lf` - 失敗テストのみ再実行
- `pytest -rf` - 失敗サマリー表示
- `pytest --tb=short` - 短いトレースバック
- PowerShell パイプより **直接 pytest オプション** を推奨

---

## Vercel デプロイの注意点

**ローカルとの主な違い**:
- Vercel は `uv` + `pyproject.toml` を使用（ローカルは `pip` + `requirements.txt`）
- `pyproject.toml` の `[project]` テーブルは必須（`uv` の要件）
- 依存関係は `pyproject.toml` と `requirements.txt` の両方に同期する
- サーバーレス関数は**ステートレス**（インメモリのレート制限はリクエスト間でリセット）
- コールドスタートあり（LiteLLM等の大パッケージは初回遅延に影響）
- `vercel.json` の `builds` キーは**非推奨**。Vercelが FastAPI を自動検出する（ゼロコンフィグ）
- `excludeFiles` で `tests/`, `venv/` 等を除外しないとバンドル250MB上限に抵触する可能性あり

---

## Debugging Patterns

| 問題 | 調査場所 |
| :--- | :--- |
| API で 404 | `api/index.py` – ルート定義を確認 |
| Notion 保存失敗 | `api/notion.py` – ペイロードと API レスポンスを確認 |
| AI モデル未検出 | `api/config.py`, `.env` – API キーとモデル名を確認 |
