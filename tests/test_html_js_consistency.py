"""
HTML-JavaScript Consistency Test
Verifies that all JavaScript selectors match the actual HTML structure
"""

import re
from pathlib import Path


def test_html_js_consistency():
    """HTMLとJavaScriptのセレクター整合性をテスト"""

    # Paths
    html_file = Path("public/index.html")
    js_dir = Path("public/js")

    # Read HTML
    html_content = html_file.read_text(encoding="utf-8")

    # Extract IDs from HTML
    html_ids = set(re.findall(r'id="([^"]+)"', html_content))

    # Extract classes from HTML (individual classes)
    html_classes = set()
    for match in re.findall(r'class="([^"]+)"', html_content):
        html_classes.update(match.split())

    # Scan JavaScript files
    js_ids_used = {}
    js_classes_used = {}

    for js_file in js_dir.glob("*.js"):
        js_content = js_file.read_text(encoding="utf-8")

        # Find getElementById calls
        for match in re.finditer(r"getElementById\(['\"](\w+)['\"]\)", js_content):
            id_name = match.group(1)
            if id_name not in js_ids_used:
                js_ids_used[id_name] = []
            js_ids_used[id_name].append(js_file.name)

        # Find querySelector/querySelectorAll with class selectors
        for match in re.finditer(
            r"querySelector(?:All)?\(['\"]\.([a-zA-Z0-9_-]+)", js_content
        ):
            class_name = match.group(1)
            if class_name not in js_classes_used:
                js_classes_used[class_name] = []
            js_classes_used[class_name].append(js_file.name)

    # Check for mismatches
    missing_ids = set(js_ids_used.keys()) - html_ids
    missing_classes = set(js_classes_used.keys()) - html_classes

    # Build detailed error message if mismatches found
    error_messages = []

    if missing_ids:
        error_messages.append(
            f"\n⚠️  IDs used in JavaScript but NOT found in HTML ({len(missing_ids)}):"
        )
        for id_name in sorted(missing_ids):
            files = ", ".join(set(js_ids_used[id_name]))
            error_messages.append(f"  ❌ {id_name} (used in {files})")

    if missing_classes:
        error_messages.append(
            f"\n⚠️  Classes used in JavaScript but NOT found in HTML ({len(missing_classes)}):"
        )
        for class_name in sorted(missing_classes):
            files = ", ".join(set(js_classes_used[class_name]))
            error_messages.append(f"  ❌ {class_name} (used in {files})")

    # Assert no mismatches
    assert not missing_ids and not missing_classes, "\n".join(error_messages)


def test_html_exists():
    """HTMLファイルが存在することを確認"""
    html_file = Path("public/index.html")
    assert html_file.exists(), f"HTML file not found: {html_file}"


def test_js_directory_exists():
    """JavaScriptディレクトリが存在することを確認"""
    js_dir = Path("public/js")
    assert js_dir.exists(), f"JavaScript directory not found: {js_dir}"
    assert js_dir.is_dir(), f"Not a directory: {js_dir}"
