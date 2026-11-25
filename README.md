# e-stat-wrangling-skills

[e-Stat (政府統計の総合窓口)](https://www.e-stat.go.jp/) の検索から、分析に使えるデータの取得・構造化までを支援する Agent Skills です。人口・自治体決算を調べたい人、統計を時系列で収集する研究者、e-Stat を一次情報源にするデータエンジニアを想定しています。

| スキル | できること |
| --- | --- |
| [estat-file-search](plugins/estat-api/skills/estat-file-search/) | e-Stat の Excel・CSV・PDF などを検索し、確認したファイルをダウンロード |
| [estat-api-data-search](plugins/estat-api/skills/estat-api-data-search/) | e-Stat API で提供される統計表を検索し、`statsDataId` を特定 |
| [paper-excel-to-table](plugins/paper-excel-to-table/) | 紙様式の Excel を PDF に書き出した帳票やスキャンから、構造化 CSV を抽出 |

## インストール

### Codex・Antigravity CLI

GitHub にログイン済みの GitHub CLI で、利用する Git プロジェクトに3スキルをインストールできます。`gh skill` は GitHub CLI 2.105.0 で確認しました。両クライアントはプロジェクトの `.agents/skills/` を読み込みます。

```sh
gh skill install K-Oxon/e-stat-wrangling-skills --all --agent codex --scope project
```

特定のリビジョンを使う場合は、コマンドに `--pin` と対象のフルコミット SHA を追加します。導入後にプロジェクトで新しいセッションを開始してください。

Node.js の環境では、Vercel の CLI も使えます。

```sh
npx skills add K-Oxon/e-stat-wrangling-skills --agent codex antigravity-cli --skill '*' --copy
```

### Claude Code

Claude Code では同梱プラグインをインストールできます。帳票抽出には、通常は親セッションのモデルを継承する専用サブエージェントを使います。

```text
/plugin marketplace add K-Oxon/e-stat-wrangling-skills
/plugin install estat-api@e-stat-wrangling
/plugin install paper-excel-to-table@e-stat-wrangling
```

初回インストール直後に帳票のサブエージェントが見つからないときは、`/reload-plugins` を実行します。スキル単体を導入する場合は、`gh skill install` の `--agent claude-code` を使えます。

## 使い方

### e-Stat を検索する

ライブ検索には e-Stat のアプリケーション ID が必要です。[e-Stat のユーザー登録画面](https://www.e-stat.go.jp/mypage/user/preregister)から取得し、セッションの環境変数 `ESTAT_APP_ID` に設定します。

```text
地方公営企業決算状況調査の水道事業の調査票を探して。最新年も知りたい。
```

詳しい使い方は [estat-api](plugins/estat-api/) を参照してください。

### 帳票 PDF を CSV にする

Excel・Numbers・LibreOffice のいずれかで帳票を PDF に書き出し、対象ページと、分かっている帳票の用途や項目を伝えます。macOS、Xcode Command Line Tools、`uv`、画像を確認できるエージェントが必要です。複雑な帳票には、画像入力に対応したフロンティアモデルを推奨します。

```text
このPDFの1ページ目をCSVにして。地方公営企業決算状況調査の水道事業の調査票です。
「行」と「列番号」の組で項目を識別します。出力は result.csv にしてください。
```

公開帳票2ケースの比較では、Claude Opus 5.5、GPT-6.2 Astra、Gemini 4 Neon がいずれも Opus 4.7 以上の構造化品質でした。

抽出手順と YAML スキーマによる検証は [paper-excel-to-table](plugins/paper-excel-to-table/)、モデル別の品質と再現手順は [紙帳票の構造化品質評価](docs/paper-excel-evaluation.md) を参照してください。

## 開発

```sh
npm ci
npm run lint:md
```

ステージした Markdown をコミット前に検査するには `npm run hooks:install` を実行します。解除は `npm run hooks:uninstall` です。

## ライセンス

[MIT](LICENSE)
