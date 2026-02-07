# Tests - Agent Instructions

このディレクトリは **pytest** によるテストスイートです。

---

## Test-Specific Rules

### Do
- `pytest` + `unittest.mock` を使用する
- テストファイル名は `test_*.py` の命名規則に従う
- `conftest.py` の共有フィクスチャを活用する
- テスト追加時はマーカー (`smoke`, `regression`, `security`, `integration`) を付与する
- **API契約テスト**: `test_api_contract.py` がJS↔Backend整合性を自動検証（エンドポイント追加/削除時に必ず実行）

### Don't
- 本番の API キーや秘密情報をテストに含めない
- 外部APIへの実際のリクエストを送信しない（モックを使用する）
- `conftest.py` の UTF-8 設定コードを削除・移動しない（Windows 環境で必須）
- コマンド実行時のリダイレクトの使用禁止 (2>&1など)　使用許可を自動化できないため。

---

## モックパス規則（重要）

エンドポイントを別モジュールに移行した場合、モックパスも更新が必要:

```python
# 移行前: api/index.py にある場合
@patch("api.index.some_function")

# 移行後: api/endpoints.py に移行した場合
@patch("api.endpoints.some_function")
```

**原則**: モック対象は「関数が定義された場所」ではなく「import されている場所」をパッチする。

---

## テスト実行コマンド

```bash
# 単一ファイル
pytest tests/test_specific.py -v --tb=short

# 全テスト
pytest -v --tb=short

# 失敗テストのみ再実行
pytest --lf

# マーカー別
pytest -m smoke
pytest -m regression
```

---

## エラー詳細出力フック

`conftest.py` にテスト失敗時の自動デバッグ情報出力を実装済み。
`ImportError`, `AttributeError`, `NameError` 等のエラー種別に応じて適切な対処法を提示する。
