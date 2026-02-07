"""
AI Internal Logic テスト

ai.py の内部関数（validate_and_fix_json等）のテスト。
プロンプト構築ロジックとJSON修復ロジックを検証します。
"""


class TestValidateAndFixJson:
    """validate_and_fix_json 関数のテスト"""

    def test_json_cleanup_markdown_blocks(self):
        """
        Markdownコードブロック内のJSONが正しく抽出されること
        """
        from api.ai import validate_and_fix_json

        # Markdownコードブロックを含むレスポンス（AI出力形式）
        json_str = """```json
{
    "Name": "テストタスク"
}
```"""

        schema = {"Name": {"type": "title"}}
        result = validate_and_fix_json(json_str, schema)

        # validate_and_fix_json は Notion API形式のプロパティ辞書を返す
        assert "Name" in result
        assert "title" in result["Name"]
        assert result["Name"]["title"][0]["text"]["content"] == "テストタスク"

    def test_json_cleanup_backticks(self):
        """
        バッククォートのみのケースも処理できること
        """
        from api.ai import validate_and_fix_json

        json_str = '```{"Status": "進行中"}```'
        schema = {"Status": {"type": "status"}}
        result = validate_and_fix_json(json_str, schema)

        assert "Status" in result
        assert result["Status"]["status"]["name"] == "進行中"

    def test_json_type_casting_number_string(self):
        """
        数値型プロパティに文字列が来た場合、キャストされること
        """
        from api.ai import validate_and_fix_json

        json_str = '{"Priority": "5"}'
        schema = {"Priority": {"type": "number"}}
        result = validate_and_fix_json(json_str, schema)

        # 文字列 "5" → 数値 5.0 に変換されること
        assert result["Priority"]["number"] == 5.0

    def test_json_type_casting_checkbox_string(self):
        """
        checkbox型にtruthyな値が来た場合、booleanに変換されること
        """
        from api.ai import validate_and_fix_json

        json_str = '{"Done": "true"}'
        schema = {"Done": {"type": "checkbox"}}
        result = validate_and_fix_json(json_str, schema)

        assert result["Done"]["checkbox"] is True

    def test_json_invalid_returns_empty(self):
        """
        完全に不正なJSONは空辞書を返すこと
        """
        from api.ai import validate_and_fix_json

        json_str = "This is not JSON at all"
        schema = {}
        result = validate_and_fix_json(json_str, schema)

        assert result == {}


class TestConstructPrompt:
    """construct_prompt 関数のテスト"""

    def test_construct_prompt_includes_schema(self):
        """
        プロンプトにスキーマ情報が含まれること
        """
        from api.ai import construct_prompt

        schema = {
            "Name": {"type": "title"},
            "Status": {"type": "status"},
        }
        recent_examples = []
        system_prompt = "テストプロンプト"

        result = construct_prompt(
            "新しいタスク", schema, recent_examples, system_prompt
        )

        # 結果は文字列プロンプト
        assert isinstance(result, str)
        assert "Name" in result
        assert "title" in result
        assert "新しいタスク" in result

    def test_construct_prompt_includes_examples(self):
        """
        プロンプトに過去の例が含まれること
        """
        from api.ai import construct_prompt

        schema = {"Name": {"type": "title"}}
        recent_examples = [
            {
                "properties": {
                    "Name": {"type": "title", "title": [{"plain_text": "例示タスク1"}]}
                }
            }
        ]
        system_prompt = "テスト"

        result = construct_prompt("新規タスク", schema, recent_examples, system_prompt)

        # 例示データがプロンプトに含まれている
        assert isinstance(result, str)
        assert "例示タスク1" in result
