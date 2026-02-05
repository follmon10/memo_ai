# Memo AI

Notionを記憶媒体として使用する、シンプルでカスタマイズ可能なAIアシスタントです。
ローカル環境で動作し、あなたの入力をNotionに構造化して保存します。

## 🚀 クイックスタート

Python 3.8以上が必要です。

### 1. セットアップ

ターミナルで以下を実行して、準備を整えます。

```bash
# 仮想環境の作成
python -m venv venv

# 仮想環境の有効化 (Windows)
venv\Scripts\activate
# 仮想環境の有効化 (Mac/Linux)
source venv/bin/activate

# 必要なパッケージのインストール
pip install -r requirements.txt
```

### 2. 設定 (.env)

プロジェクト直下に `.env` ファイルを作成し、APIキーを設定します。

1.  `.env.example` をコピーして `.env` にリネームします。
2.  以下の項目を入力します。

```env
# Google Gemini APIキー (必須)
# https://aistudio.google.com/app/apikey から取得
GEMINI_API_KEY=your_key_here

# Notion APIキー (Notion連携用)
# https://www.notion.so/my-integrations から取得
NOTION_API_KEY=your_key_here

# Notion ルートページID
# 共有設定　notionページの３点メニュー 接続 から上記で作成した integrations の名前を探す。
# ブラウザでNotionページを開き、URL末尾の32桁の英数字をコピー
# 例: https://notion.so/my-page-1234567890abcdef1234567890abcdef -> 1234567890abcdef1234567890abcdef
NOTION_ROOT_PAGE_ID=your_page_id_here
```

### 3. 起動

以下のコマンドでサーバーを立ち上げます。

```bash
python -m uvicorn api.index:app --reload
```

ブラウザで `http://localhost:8000` にアクセスすれば完了です！

---

## 🛠️ カスタマイズ

コードを少し編集するだけで、自分だけのAIを作れます。
AIに改造アイデアを提案させることも可能。

### AIの性格を変える
`public/script.js` の `DEFAULT_SYSTEM_PROMPT` を編集します。
```javascript
// 例: 関西弁のAIにする
const DEFAULT_SYSTEM_PROMPT = `あなたは大阪出身の陽気なアシスタントです。`;
```

### デザインを変える
`public/style.css` で色や配置を調整できます。
```css
/* 例: 自分の吹き出しを青色にする */
.chat-bubble.user {
    background-color: #0084ff;
}
```

---

## 📚 AI開発 実践ガイド（初心者〜中級者向け）

このアプリのコードは、AI開発の重要なコンセプトを学ぶための教材としても機能します。

### 🔑 1. APIキーの管理
APIキーは大切な「鍵」です。他人に知られないように管理しましょう。

-   **コードに書かない**: キーは `.env` ファイルに書きます。これでGitへの誤送信を防げます。
-   **もし公開してしまったら**: キーを無効化し、再発行すれば大丈夫です。

### 🤖 2. エラーが出たらAIに聞こう
エラーでつまづいたら、エラーメッセージをそのままAI（ChatGPT, Gemini, Claudeなど）に貼り付けて質問するのが一番の近道です。

### 🛡️ 3. 実践的なセキュリティ対策
本番環境（インターネット公開）で運用する場合、以下の3つは「推奨」ではなく**「必須」**です。

| 対策 | 理由 |
|------|------|
| **認証を追加** | 現状は誰でもアクセス可能です。Basic認証やトークン認証を実装して、利用者を制限してください。 |
| **CORS設定** | `ALLOWED_ORIGINS` 環境変数を設定し、自分の公開ドメイン（例: `https://your-domain.com`）以外からの通信をブロックしてください。 |
| **コスト管理** | 従量課金API（OpenAI等）を利用する場合は、各サービスの管理画面で利用上限金額（Budget）を設定し、予期せぬ課金を防いでください。 |


### 🐛 4. デバッグのコツ
動かないときは、「どこで止まっているか」を探します。

1.  **ブラウザの検証ツール (F12)**:
    *   `Console` タブ: JavaScriptのエラー（赤文字）が出ていませんか？
    *   `Network` タブ: APIリクエスト (`/api/chat` など) が `200 OK` 以外（404や500）になっていませんか？
2.  **サーバーログ**:
    *   ターミナルを確認してください。Pythonのエラー詳細（Traceback）が表示されているはずです。

