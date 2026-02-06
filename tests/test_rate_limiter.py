"""
Rate Limiter テスト

SimpleRateLimiter クラスの動作を検証します。
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException


class TestRateLimiter:
    """レート制限機能のテスト"""

    def test_rate_limiter_disabled(self):
        """
        RATE_LIMIT_ENABLED=false の場合、制限がスキップされること
        """
        with patch.dict("os.environ", {"RATE_LIMIT_ENABLED": "false"}):
            from api.rate_limiter import SimpleRateLimiter

            # クラスを直接インスタンス化してテスト（グローバル汚染を回避）
            limiter = SimpleRateLimiter()
            assert limiter.enabled is False

    @pytest.mark.asyncio
    async def test_rate_limiter_allows_requests_when_enabled(self):
        """
        有効時はリクエストを許可すること（リミット内）
        """
        from api.rate_limiter import SimpleRateLimiter

        # デフォルト（環境変数指定なし）または明示的有効化
        with patch.dict("os.environ", {"RATE_LIMIT_ENABLED": "true"}):
            limiter = SimpleRateLimiter()
            mock_request = MagicMock()

            # リミット内であれば通過する
            result = await limiter.check_rate_limit(mock_request, "test")
            assert result == {}  # 正常時は空辞書を返す

    @pytest.mark.asyncio
    async def test_rate_limiter_exceed_limit(self):
        """
        リミット超過時に 429 HTTPException が発生すること
        """
        from api.rate_limiter import SimpleRateLimiter

        # 制限値を低く設定
        with patch.dict(
            "os.environ",
            {"RATE_LIMIT_ENABLED": "true", "RATE_LIMIT_GLOBAL_PER_HOUR": "2"},
        ):
            limiter = SimpleRateLimiter()
            mock_request = MagicMock()

            # 設定値が正しく読み込まれているか確認
            assert limiter.enabled is True
            assert limiter.global_per_hour == 2

            # 1回目 (ok)
            await limiter.check_rate_limit(mock_request, "test_exceed")

            # 2回目 (ok: count=1 -> 2)
            # countはappend後に増えるため、ここではまだ制限にかからないはずだが、
            # 実装によっては判定タイミングが異なる可能性があるため確認
            await limiter.check_rate_limit(mock_request, "test_exceed")

            # 3回目 (error: count=2 >= limit)
            with pytest.raises(HTTPException) as exc_info:
                await limiter.check_rate_limit(mock_request, "test_exceed")

            assert exc_info.value.status_code == 429
            assert "レート制限" in exc_info.value.detail["error"]

    def test_rate_limiter_cleanup_old_entries(self):
        """
        古いエントリがクリーンアップされること
        """
        import time
        from api.rate_limiter import SimpleRateLimiter

        limiter = SimpleRateLimiter()

        # 古いタイムスタンプを直接挿入
        old_time = time.time() - 8000  # 2時間以上前
        limiter.global_log["test:endpoint"] = [old_time]
        limiter.last_cleanup = time.time() - 4000  # クリーンアップ間隔を超過

        # クリーンアップを実行
        limiter._cleanup_old_entries()

        # 古いエントリが削除されていること
        assert "test:endpoint" not in limiter.global_log
