"""
API Contract Test - フロントエンド↔バックエンド間のAPIエンドポイント整合性を検証

【このテストの目的】
このプロジェクトは個人用ツールのため、チーム開発のようなコードレビューがありません。
最大のリスクは「Python (Backend) ↔ JavaScript (Frontend) の不整合」です。

- APIエンドポイントのパスやHTTPメソッドを変更したとき
- フロントエンドで新しいAPI呼び出しを追加したとき
- バックエンドで新しいルートを追加したとき

これらの変更時に**静的解析で自動検出**することで、実行時エラーを未然に防ぎます。

デグレッション検出対象:
  - JSがfetchするAPIパスがバックエンドに存在しない
  - バックエンドのAPIルートがJSから呼ばれていない（デッドAPI）
  - HTTPメソッド（GET/POST等）の不一致

実装戦略:
  1. JSのfetch()引数を正規表現で抽出（文字列 + テンプレートリテラル + HTTPメソッド）
  2. FastAPIのapp.routesからルート一覧とメソッドを動的に取得
  3. パスパラメータを正規化して照合（/api/content/${id} ↔ /api/content/{page_id}）
  4. HTTPメソッドを照合（JS: POST ↔ Backend: POST）
"""

import re
from pathlib import Path
from typing import Dict, Set, Tuple


JS_DIR = Path("public/js")


def _extract_js_api_calls_with_methods() -> Dict[Tuple[str, str], Set[str]]:
    """
    JS内の全fetch()呼び出しからAPIパスとHTTPメソッドを抽出。

    Returns:
        {(path, method): {file1.js, file2.js}} の辞書
        例: {('/api/save', 'POST'): {'main.js', 'chat.js'}}
    """
    api_calls = {}

    for js_file in JS_DIR.glob("*.js"):
        content = js_file.read_text(encoding="utf-8")
        filename = js_file.name

        # パターン1: 文字列リテラル fetch('/api/...') または fetchWithCache('/api/...')
        for match in re.finditer(
            r"(?:fetch|fetchWithCache)\s*\(\s*['\"](/api/[^'\"?]+)", content
        ):
            path = match.group(1)
            # この位置からfetch呼び出し全体を探して method を抽出
            start_pos = match.start()
            # fetch(...) の閉じカッコを探す（簡易版：次の行まで）
            snippet = content[start_pos : start_pos + 500]

            method = "GET"  # デフォルト
            method_match = re.search(r"method:\s*['\"](\w+)", snippet)
            if method_match:
                method = method_match.group(1).upper()

            key = (path, method)
            if key not in api_calls:
                api_calls[key] = set()
            api_calls[key].add(filename)

        # パターン2: テンプレートリテラル fetch(`/api/...${var}...`)
        for match in re.finditer(
            r"(?:fetch|fetchWithCache)\s*\(\s*`([^`]+)`", content, re.DOTALL
        ):
            raw_template = match.group(1)
            if "/api/" in raw_template:
                cleaned = re.sub(r"\s+", "", raw_template)
                api_match = re.search(r"(/api/[^?#,]+)", cleaned)
                if api_match:
                    raw_path = api_match.group(1)
                    normalized_path = re.sub(r"\$\{[^}]+\}", "{param}", raw_path)

                    # メソッド抽出
                    start_pos = match.start()
                    snippet = content[start_pos : start_pos + 500]
                    method = "GET"
                    method_match = re.search(r"method:\s*['\"](\w+)", snippet)
                    if method_match:
                        method = method_match.group(1).upper()

                    key = (normalized_path, method)
                    if key not in api_calls:
                        api_calls[key] = set()
                    api_calls[key].add(filename)

    return api_calls


def _extract_backend_routes_with_methods() -> Dict[Tuple[str, str], str]:
    """
    FastAPIのルート定義からAPIパスとHTTPメソッドを抽出。

    Returns:
        {(path, method): decorator_line} の辞書
        例: {('/api/save', 'POST'): '@router.post("/api/save")'}
    """
    from api.index import app

    routes = {}
    for route in app.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            path = route.path
            if path.startswith("/api/"):
                # FastAPIのrouteは複数メソッドを持つ場合がある（例: GET, HEAD）
                # 主要メソッドのみを対象にする
                for method in route.methods:
                    if method in {"GET", "POST", "PUT", "DELETE", "PATCH"}:
                        key = (path, method)
                        # デコレータ情報は実際にはファイルを読まないと取得できないが、
                        # ここではpath情報として代用
                        routes[key] = f"@router.{method.lower()}({path})"

    return routes


def _normalize_path_params(path: str) -> str:
    """
    パスパラメータを正規化して照合しやすくする。

    例:
      /api/schema/{target_id} → /api/schema/{param}
      /api/content/{page_id}  → /api/content/{param}
    """
    return re.sub(r"\{[^}]+\}", "{param}", path)


def test_js_api_calls_have_backend_routes_with_methods():
    """
    JSがfetchする全APIパス＋メソッドがバックエンドに存在することを確認。

    検出例:
      - JS: fetch('/api/save', {method: 'POST'}) があるのに、
        Backend に @router.post('/api/save') がない
      - JS: fetch('/api/save', {method: 'PUT'}) なのに、
        Backend は @router.post('/api/save') → メソッド不一致
    """
    js_calls = _extract_js_api_calls_with_methods()
    backend_routes = _extract_backend_routes_with_methods()

    # パスパラメータを正規化して比較
    js_normalized = {}
    for (path, method), files in js_calls.items():
        norm_path = _normalize_path_params(path)
        key = (norm_path, method)
        if key not in js_normalized:
            js_normalized[key] = []
        js_normalized[key].append((path, files))

    backend_normalized = {}
    for (path, method), decorator in backend_routes.items():
        norm_path = _normalize_path_params(path)
        key = (norm_path, method)
        backend_normalized[key] = (path, decorator)

    # 不一致検出
    missing = set(js_normalized.keys()) - set(backend_normalized.keys())

    if missing:
        error_lines = ["以下のAPIパス+メソッドがバックエンドに存在しません:"]
        for path, method in sorted(missing):
            error_lines.append(f"\n  [{method}] {path}")
            for orig_path, files in js_normalized[(path, method)]:
                error_lines.append(f"      JS files: {', '.join(sorted(files))}")
                if orig_path != path:
                    error_lines.append(f"      Original: {orig_path}")

        assert False, "\n".join(error_lines)


def test_backend_routes_are_called_by_js():
    """
    バックエンドの /api/* ルートがJSから少なくとも1箇所呼ばれているか確認（デッドAPI検出）。

    注: インフラ系(/api/health, /api/debug...)は除外。
    """
    js_calls = _extract_js_api_calls_with_methods()
    backend_routes = _extract_backend_routes_with_methods()

    # インフラ系エンドポイントは除外
    INFRASTRUCTURE_ENDPOINTS = {"/api/health", "/api/debug5075378"}
    backend_api_only = {
        (path, method): decorator
        for (path, method), decorator in backend_routes.items()
        if path not in INFRASTRUCTURE_ENDPOINTS
    }

    # パスパラメータを正規化して比較
    js_normalized = set()
    for (path, method), files in js_calls.items():
        norm_path = _normalize_path_params(path)
        js_normalized.add((norm_path, method))

    backend_normalized = set()
    for (path, method), decorator in backend_api_only.items():
        norm_path = _normalize_path_params(path)
        backend_normalized.add((norm_path, method))

    unused = backend_normalized - js_normalized

    if unused:
        # 警告として出力（テスト失敗にはしない）
        warning_lines = ["[WARNING] 以下のバックエンドAPIがJSから呼ばれていません:"]
        for path, method in sorted(unused):
            warning_lines.append(f"  [{method}] {path}")
        print("\n".join(warning_lines))
