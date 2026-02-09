import os
import time
from typing import Dict, List
from collections import defaultdict
from fastapi import Request, HTTPException
from api.logger import setup_logger

logger = setup_logger(__name__)


class SimpleRateLimiter:
    """
    シンプルなグローバルレート制限（1時間1000リクエスト）

    Vercel環境では各関数インスタンスが独立して動作するため、
    完全な制限は保証されませんが、AI API乱用防止には有効です。
    """

    def __init__(self):
        self.enabled = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
        self.global_per_hour = int(os.getenv("RATE_LIMIT_GLOBAL_PER_HOUR", "1000"))

        # グローバルカウンター
        self.global_log: Dict[str, List[float]] = defaultdict(list)
        self.last_cleanup = time.time()

        if self.enabled:
            logger.info("✅ Enabled - %d requests/hour (global)", self.global_per_hour)

    async def check_rate_limit(
        self, request: Request, endpoint: str = "default", custom_limit: int = None
    ) -> dict:
        """グローバルレート制限をチェック（1000 req/時間）"""
        if not self.enabled:
            return {}

        self._cleanup_old_entries()
        self._check_global_limit(endpoint, custom_limit)
        return {}

    def _check_global_limit(self, endpoint: str, custom_limit: int = None):
        """グローバルレート制限チェック（1時間1000リクエスト、またはカスタム制限）"""
        if self.global_per_hour <= 0:
            return

        window = 3600  # 1時間
        now = time.time()
        key = f"global:{endpoint}"

        # 古いエントリを削除
        self.global_log[key] = [t for t in self.global_log[key] if t > now - window]
        count = len(self.global_log[key])

        limit = custom_limit if custom_limit is not None else self.global_per_hour
        if count >= limit:
            logger.warning(
                "⚠️ Global limit reached for %s: %d/%d",
                endpoint,
                count,
                limit,
            )
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "レート制限を超えました",
                    "message": f"1時間あたり{limit}リクエストまでです。しばらく待ってから再試行してください。",
                    "retry_after": 3600,
                },
            )

        self.global_log[key].append(now)

    def _cleanup_old_entries(self):
        """古いエントリを定期的に削除してメモリを節約（1時間ごと）"""
        now = time.time()
        cleanup_interval = 3600  # 1時間ごとにクリーンアップ
        if now - self.last_cleanup < cleanup_interval:
            return

        # 2時間以上古いデータを削除
        for key in list(self.global_log.keys()):
            self.global_log[key] = [t for t in self.global_log[key] if t > now - 7200]
            if not self.global_log[key]:
                del self.global_log[key]

        self.last_cleanup = now


# グローバルインスタンス
rate_limiter = SimpleRateLimiter()
