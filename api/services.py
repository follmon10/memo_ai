"""
サービス層関数 (Business Logic Helpers)

エンドポイントから呼ばれる共通ロジックを定義します。
"""

import re
from datetime import datetime


def sanitize_image_data(text: str) -> str:
    """
    テキストコンテンツからBase64形式の画像データを除去します。

    Notionに送信する際、長大なBase64文字列が含まれているとエラーやパフォーマンス低下の原因になるため、
    正規表現を使ってこれらを削除または置換します。
    Markdown形式の画像リンクとHTML形式のimgタグの両方に対応しています。
    """
    # Markdown形式の画像 (data URIスキーム) を削除: ![alt](data:image/png;base64,...)
    text = re.sub(r"!\[.*?\]\(data:image\/.*?\)", "", text, flags=re.DOTALL)
    # HTML形式のimgタグ (data URIスキーム) を削除: <img src="data:image/..." ...>
    text = re.sub(
        r'<img[^>]+src=["\']data:image\/[^"\']+["\'][^>]*>', "", text, flags=re.DOTALL
    )
    # 特定のマーカー文字列を除去
    text = text.replace("[画像送信]", "").strip()
    return text


def get_current_jst_str() -> str:
    """
    現在時刻をJST（日本標準時）の文字列で取得

    AIに現在時刻の情報を与えることで、日時に関する回答の精度を向上させます。
    """
    import zoneinfo

    jst = zoneinfo.ZoneInfo("Asia/Tokyo")
    now = datetime.now(jst)
    return now.strftime("%Y-%m-%d %H:%M:%S JST")


def extract_property_value(prop_data: dict) -> any:
    """
    Notionプロパティオブジェクトから表示用の値を抽出

    Notionのプロパティは型により異なる構造を持つため、型に応じて
    適切な値を取り出します。

    Args:
        prop_data: Notionプロパティオブジェクト（"type"キーと型別のデータを含む）

    Returns:
        抽出された値（文字列、リスト、数値、None等）
    """
    if not isinstance(prop_data, dict):
        return None

    p_type = prop_data.get("type")

    if p_type == "title":
        return "".join(t.get("plain_text", "") for t in prop_data.get("title", []))
    elif p_type == "rich_text":
        return "".join(t.get("plain_text", "") for t in prop_data.get("rich_text", []))
    elif p_type == "select":
        select_obj = prop_data.get("select")
        return select_obj.get("name") if select_obj else None
    elif p_type == "multi_select":
        options = prop_data.get("multi_select", [])
        return [o.get("name", "") for o in options]
    elif p_type == "status":
        status_obj = prop_data.get("status")
        return status_obj.get("name") if status_obj else None
    elif p_type == "date":
        date_obj = prop_data.get("date")
        return date_obj.get("start") if date_obj else None
    elif p_type == "checkbox":
        return prop_data.get("checkbox")
    elif p_type == "number":
        return prop_data.get("number")
    elif p_type == "url":
        return prop_data.get("url")
    elif p_type == "email":
        return prop_data.get("email")
    elif p_type == "phone_number":
        return prop_data.get("phone_number")
    else:
        return None


def chunk_rich_text_items(
    items: list, text_key: str = "rich_text", limit: int = 2000
) -> list:
    """
    rich_text/title配列の各アイテムを指定文字数で分割

    Notion APIはrich_textやtitleの各アイテムに2000文字の制限があります。
    この関数は長いテキストを持つアイテムを分割して、制限内に収めます。

    Args:
        items: rich_text/title配列
        text_key: 処理対象のキー（"rich_text" or "title"）
        limit: 1アイテムあたりの文字数上限（デフォルト2000）

    Returns:
        分割後のアイテム配列
    """
    result = []
    for item in items:
        if "text" not in item:
            result.append(item)
            continue

        content = item["text"].get("content", "")
        if len(content) <= limit:
            result.append(item)
        else:
            # 長いコンテンツを分割
            for i in range(0, len(content), limit):
                chunk_item = {
                    "type": "text",
                    "text": {"content": content[i : i + limit]},
                }
                # 元のアイテムにannotationsがあれば引き継ぐ
                if "annotations" in item:
                    chunk_item["annotations"] = item["annotations"]
                result.append(chunk_item)

    return result


def _sanitize_rich_text_field(items: list, sanitize_fn) -> list:
    """
    rich_text/title配列のテキストをサニタイズし、文字数制限で分割する。

    既存の chunk_rich_text_items を内部で再利用する実装。
    sanitize_fn は sanitize_image_data などのテキスト変換関数を想定。

    Args:
        items: rich_text/title配列
        sanitize_fn: テキストサニタイズ関数

    Returns:
        サニタイズ & 分割済み配列
    """
    # Step 1: サニタイズ（Base64画像除去等）
    for item in items:
        if "text" in item and "content" in item["text"]:
            item["text"]["content"] = sanitize_fn(item["text"]["content"])

    # Step 2: 文字数制限による分割（既存関数を再利用）
    return chunk_rich_text_items(items)


def sanitize_notion_properties(properties: dict) -> dict:
    """
    Notionプロパティ値をサニタイズ（画像データ除去 + 文字数分割）。

    rich_text と title フィールドを検出し、それぞれを
    _sanitize_rich_text_field で処理する。

    Args:
        properties: Notionプロパティ辞書

    Returns:
        サニタイズ済みプロパティ辞書
    """
    sanitized = properties.copy()

    for key, val in sanitized.items():
        if not isinstance(val, dict):
            continue

        if "rich_text" in val and val["rich_text"]:
            val["rich_text"] = _sanitize_rich_text_field(
                val["rich_text"], sanitize_image_data
            )

        if "title" in val and val["title"]:
            val["title"] = _sanitize_rich_text_field(val["title"], sanitize_image_data)

    return sanitized


def ensure_title_property(properties: dict, fallback_text: str) -> dict:
    """
    タイトルプロパティが存在しない場合、コンテンツから自動生成する。

    Args:
        properties: サニタイズ済みプロパティ
        fallback_text: タイトル生成のフォールバックテキスト

    Returns:
        タイトルが保証されたプロパティ辞書
    """
    # タイトルの存在チェック
    has_title = any(
        "title" in val for val in properties.values() if isinstance(val, dict)
    )

    if not has_title:
        safe_title = (fallback_text or "Untitled").split("\n")[0][:100]
        properties["Name"] = {"title": [{"text": {"content": safe_title}}]}

    return properties


def create_content_blocks(text: str, chunk_size: int = 2000) -> list:
    """
    テキストをNotionのparagraphブロック配列に変換する。

    Notion APIのブロックサイズ制限(2000文字)に従い自動分割。

    Args:
        text: 変換するテキスト
        chunk_size: 分割サイズ（デフォルト2000）

    Returns:
        Notion APIのchildrenブロック配列
    """
    if not text:
        return []

    return [
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"type": "text", "text": {"content": text[i : i + chunk_size]}}
                ]
            },
        }
        for i in range(0, len(text), chunk_size)
    ]
