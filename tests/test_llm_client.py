"""
LLM Client テスト

llm_client.py の generate_json および prepare_multimodal_prompt のテスト。
外部API呼び出しはモックします。
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock


class TestGenerateJson:
    """generate_json 関数のテスト"""

    @pytest.mark.asyncio
    async def test_generate_json_success(self):
        """
        正常なレスポンスが返されること
        """
        from api.llm_client import generate_json

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"result": "success"}'
        mock_response.usage = MagicMock()
        mock_response.usage.model_dump.return_value = {"total_tokens": 100}

        with patch("api.llm_client.acompletion", new_callable=AsyncMock) as mock_acomp:
            mock_acomp.return_value = mock_response

            with patch("api.llm_client.completion_cost", return_value=0.001):
                result = await generate_json("test prompt", "gemini/gemini-2.0-flash")

        assert result["content"] == '{"result": "success"}'
        assert result["model"] == "gemini/gemini-2.0-flash"
        assert "usage" in result

    @pytest.mark.asyncio
    async def test_generate_json_empty_response(self):
        """
        空のレスポンスで RuntimeError が発生すること
        """
        from api.llm_client import generate_json

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = ""  # 空レスポンス

        with patch("api.llm_client.acompletion", new_callable=AsyncMock) as mock_acomp:
            mock_acomp.return_value = mock_response

            with pytest.raises(RuntimeError) as exc_info:
                await generate_json("test", "model", retries=0)

            assert "Empty AI response" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_json_retry_on_failure(self):
        """
        失敗時にリトライが実行されること
        """
        from api.llm_client import generate_json

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"ok": true}'
        mock_response.usage = MagicMock()
        mock_response.usage.model_dump.return_value = {}

        call_count = 0

        async def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Temporary failure")
            return mock_response

        with patch("api.llm_client.acompletion", new_callable=AsyncMock) as mock_acomp:
            mock_acomp.side_effect = side_effect

            with patch("api.llm_client.completion_cost", return_value=0.0):
                with patch("asyncio.sleep", new_callable=AsyncMock):
                    result = await generate_json("test", "model", retries=2)

        assert result["content"] == '{"ok": true}'
        assert call_count == 2  # 1回失敗 + 1回成功

    @pytest.mark.asyncio
    async def test_generate_json_max_retries_exceeded(self):
        """
        最大リトライ回数を超えると RuntimeError が発生すること
        """
        from api.llm_client import generate_json

        with patch("api.llm_client.acompletion", new_callable=AsyncMock) as mock_acomp:
            mock_acomp.side_effect = Exception("Persistent failure")

            with patch("asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(RuntimeError) as exc_info:
                    await generate_json("test", "model", retries=1)

            assert "AI generation failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_json_skips_response_format_for_unsupported_models(self):
        """
        supports_response_schema=False のモデルでは response_format を渡さないこと
        """
        from api.llm_client import generate_json

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"result": "ok"}'
        mock_response.usage = MagicMock()
        mock_response.usage.model_dump.return_value = {}

        with patch("api.llm_client.supports_response_schema", return_value=False):
            with patch("api.llm_client.acompletion", new_callable=AsyncMock) as mock_ac:
                mock_ac.return_value = mock_response
                with patch("api.llm_client.completion_cost", return_value=0.0):
                    await generate_json("test", "gemini/gemini-2.5-flash-image")

                # acompletion が response_format なしで呼ばれたことを確認
                call_kwargs = mock_ac.call_args.kwargs
                assert "response_format" not in call_kwargs
                assert call_kwargs["drop_params"] is True

    @pytest.mark.asyncio
    async def test_generate_json_includes_response_format_for_supported_models(self):
        """
        supports_response_schema=True のモデルでは response_format を渡すこと
        """
        from api.llm_client import generate_json

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"result": "ok"}'
        mock_response.usage = MagicMock()
        mock_response.usage.model_dump.return_value = {}

        with patch("api.llm_client.supports_response_schema", return_value=True):
            with patch("api.llm_client.acompletion", new_callable=AsyncMock) as mock_ac:
                mock_ac.return_value = mock_response
                with patch("api.llm_client.completion_cost", return_value=0.0):
                    await generate_json("test", "gemini/gemini-2.5-flash")

                # acompletion が response_format 付きで呼ばれたことを確認
                call_kwargs = mock_ac.call_args.kwargs
                assert call_kwargs["response_format"] == {"type": "json_object"}
                assert call_kwargs["drop_params"] is True


class TestPrepareMultimodalPrompt:
    """prepare_multimodal_prompt 関数のテスト"""

    def test_prepare_multimodal_prompt_format(self):
        """
        マルチモーダルプロンプトが正しい形式で生成されること
        """
        from api.llm_client import prepare_multimodal_prompt

        result = prepare_multimodal_prompt(
            text="Describe this image",
            image_data="base64encodeddata",
            image_mime_type="image/jpeg",
        )

        assert len(result) == 2
        assert result[0]["type"] == "text"
        assert result[0]["text"] == "Describe this image"
        assert result[1]["type"] == "image_url"
        assert (
            "data:image/jpeg;base64,base64encodeddata" in result[1]["image_url"]["url"]
        )
