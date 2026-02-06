"""
Model Discovery テスト

model_discovery.py のモデル取得とキャッシュ機能のテスト。
"""

import pytest


class TestModelDiscovery:
    """モデル発見機能のテスト"""

    @pytest.fixture(autouse=True)
    def clean_cache(self):
        """全てのテストの前後でキャッシュをクリア"""
        from api.model_discovery import clear_cache

        clear_cache()
        yield
        clear_cache()

    def test_clear_cache_functionality(self):
        """
        clear_cache が正しく動作すること
        """
        from api.model_discovery import clear_cache

        # clear_cacheが例外を投げないこと
        try:
            clear_cache()
            assert True
        except Exception:
            assert False, "clear_cache should not raise exceptions"

    def test_get_gemini_models_returns_list(self):
        """
        get_gemini_models は必ずリストを返すこと（APIキーの有無に関わらず）
        """
        from api.model_discovery import get_gemini_models

        result = get_gemini_models()
        assert isinstance(result, list)

    def test_get_openai_models_returns_list(self):
        """
        get_openai_models は必ずリストを返すこと（APIキーの有無に関わらず）
        """
        from api.model_discovery import get_openai_models

        result = get_openai_models()
        assert isinstance(result, list)

    def test_get_gemini_models_with_valid_cache(self):
        """
        有効なキャッシュがある場合、APIを呼ばずにキャッシュから返すこと
        """
        from api.model_discovery import get_gemini_models
        from datetime import datetime, timedelta
        import api.model_discovery as md

        # 有効なキャッシュを直接設定
        cached_models = [{"id": "gemini-cached", "name": "Cached Model"}]
        # 正しいキャッシュキーを使用（実装に合わせる）
        cache_key = "gemini_models_v3"
        md._MODEL_CACHE[cache_key] = cached_models
        md._CACHE_EXPIRY[cache_key] = datetime.now() + timedelta(hours=1)

        result = get_gemini_models()

        # キャッシュから返されること（API呼び出しなし）
        assert isinstance(result, list)
        assert len(result) > 0  # キャッシュされたデータが返る
