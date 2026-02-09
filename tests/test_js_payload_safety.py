"""
JavaScript Payload Safety Test - State Snapshot Enforcement

【このテストの目的】
fetch() のペイロード構築時に、変更可能な window.App プロパティを
直接参照していないことを検証します。

ベストプラクティス (2024):
  - State Snapshotting Pattern の強制
  - CI/CD統合で自動実行
  - 明確なエラーメッセージでチーム教育

デグレッション検出対象:
  - fetch ペイロード内で window.App.image.generationMode などを直接参照
  - 状態クリア後の値が送信されるパターン
"""

import re
from pathlib import Path
from typing import List, Dict
import pytest


# 変更される可能性のあるプロパティ (Mutable State)
MUTABLE_STATE_PATTERNS = [
    r"window\.App\.image\.data",
    r"window\.App\.image\.mimeType",
    r"window\.App\.image\.generationMode",
    r"window\.App\.chat\.session(?!\.\w+\()",  # .slice() などのメソッド呼び出しは許可
]

# 読み取り専用プロパティ (許可リスト)
# これらは変更されないため、直接参照してもOK
ALLOWED_READONLY_PATTERNS = [
    r"window\.App\.target\.id",
    r"window\.App\.target\.type",
    r"window\.App\.target\.systemPrompt",
    r"window\.App\.model\.current",
    r"window\.App\.defaultPrompt",
]


@pytest.mark.regression
def test_fetch_payloads_snapshot_mutable_state():
    """
    fetch のペイロード構築時に mutable state を直接参照せず、
    ローカル変数にスナップショットしていることを検証

    検出例:
      - ❌ fetch(..., {body: JSON.stringify({value: window.App.image.data})})
      - ✅ const data = window.App.image.data; fetch(..., {body: JSON.stringify({value: data})})
    """
    js_dir = Path("public/js")
    if not js_dir.exists():
        pytest.skip(f"JavaScript directory not found: {js_dir}")

    js_files = list(js_dir.glob("*.js"))
    violations: List[Dict[str, any]] = []

    for js_file in js_files:
        content = js_file.read_text(encoding="utf-8")

        # fetch 呼び出しを検索
        for match in re.finditer(r"fetch\s*\([^)]+\)", content):
            # fetch 前後のコンテキストを含むスニペットを抽出
            start = max(0, match.start() - 800)
            end = min(len(content), match.end() + 200)
            snippet = content[start:end]

            # ペイロード構築部分を含むか確認
            if "JSON.stringify" not in snippet and "body:" not in snippet:
                continue

            # Mutable state の直接参照をチェック
            for pattern in MUTABLE_STATE_PATTERNS:
                if re.search(pattern, snippet):
                    line_number = content[: match.start()].count("\n") + 1
                    violations.append(
                        {
                            "file": js_file.name,
                            "pattern": pattern,
                            "line": line_number,
                            "context": snippet[
                                max(0, match.start() - start - 100) : match.end()
                                - start
                                + 100
                            ],
                        }
                    )

    if violations:
        error_lines = [
            "❌ Mutable state が fetch payload で直接参照されています:",
            "",
            "【ベストプラクティス】",
            "非同期処理前に状態をローカル変数にスナップショットしてください",
            "",
        ]

        for v in violations:
            error_lines.append(f"  📄 {v['file']}:L{v['line']}")
            error_lines.append(f"     パターン: {v['pattern']}")

        error_lines.extend(
            [
                "",
                "【修正例】",
                "  ❌ NG:",
                "    clearState();",
                "    fetch('/api/...', {",
                "      body: JSON.stringify({ value: window.App.some.state })",
                "    });",
                "",
                "  ✅ OK:",
                "    const capturedValue = window.App.some.state;  // スナップショット",
                "    clearState();",
                "    fetch('/api/...', {",
                "      body: JSON.stringify({ value: capturedValue })",
                "    });",
                "",
                "詳細: public/js/AGENTS.md の 'State Management Best Practices' を参照",
            ]
        )

        pytest.fail("\n".join(error_lines))


@pytest.mark.regression
def test_state_snapshot_pattern_documented():
    """
    AGENTS.md に State Snapshot Pattern が文書化されていることを確認
    """
    agents_md = Path("public/js/AGENTS.md")

    if not agents_md.exists():
        pytest.skip(f"AGENTS.md not found: {agents_md}")

    content = agents_md.read_text(encoding="utf-8")

    # 重要なキーワードが含まれているか確認
    required_keywords = [
        "State Management",
        "Snapshot",
        "fetch",
    ]

    missing = [kw for kw in required_keywords if kw not in content]

    if missing:
        pytest.fail(
            f"AGENTS.md に State Management のドキュメントが不足しています:\n"
            f"不足キーワード: {', '.join(missing)}"
        )
