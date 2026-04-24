# e-stat-wrangling-skills

e-Statを本当に実務で使うためのAgent Skills

[English version →](README.en.md)

---

## Why and What

[e-Stat (政府統計の総合窓口)](https://www.e-stat.go.jp/) は日本の公的統計を扱うなら避けて通れない一方で、検索性と機械判読性はとにかく厳しい状況です。

この repo はe-Statからデータを分析可能な状態にするまでの工数をできる限り減らすことを目的に、数々の知見を Claude Code セッションに直接 install できるように plugin の形でまとめたものです。

## こんな人に

- 自治体 DX 担当者 / 監査: 水道料金・介護給付・地方税など、公営企業決算や行政データを分析したい
- 研究者・大学院生: 高齢化率・人口・経済統計を時系列で継続的に取りたい
- データエンジニア / アナリスト: e-Stat を一次情報源にしてデータパイプラインを組みたい

---

## できること

| Plugin | 何ができるか | ステータス |
|---|---|---|
| [`paper-excel-to-table`](plugins/paper-excel-to-table/) | 紙様式 Excel を PDF 化したものから、Opus 4.7 の vision で構造化 CSV を取り出す。低確度セルは自動トリミングで再観察 | MVP (macOS) |
| [`estat-file-search`](plugins/estat-file-search/) | e-Stat のファイル提供データ (xlsx/csv/pdf) を curl + jq で探索・ダウンロード | 仕様 + recipes |
| [`estat-api-data-search`](plugins/estat-api-data-search/) | e-Stat API/DB 提供の統計表を探索し、`statsDataId` を特定 | 仕様 + recipes |

---

## Install

```
/plugin marketplace add K-Oxon/e-stat-wrangling-skills
/plugin install paper-excel-to-table@e-stat-wrangling
/plugin install estat-file-search@e-stat-wrangling
/plugin install estat-api-data-search@e-stat-wrangling
```

Claude Code の使用が前提です。

### 初回 install 時の注意

subagent を同梱する plugin (現状 `paper-excel-to-table`) は、**初回 install 直後に認識されないことがあります**。その場合は:

```
/reload-plugins
```

を 1 回実行してから試してください。

### 推奨 permissions (任意)

頻出の Bash 呼び出しで permission プロンプトを抑えたいとき、`~/.claude/settings.json` に次を追加すると快適です:

```json
{
  "permissions": {
    "allow": [
      "Bash(uv run --script *)",
      "Bash(swift --version)",
      "Bash(xcode-select -p)",
      "Bash(mdls -name kMDItemNumberOfPages *)"
    ]
  }
}
```

あくまで自己責任で権限設定はお願いします。

---

## ユースケース — 紙帳票 PDF から CSV を取り出す

`paper-excel-to-table` は最も「痛みに効く」plugin です。水道事業業務年報のような **セル結合だらけの紙様式 Excel** を CSV に落とせます。

### 1. xlsx を PDF に変換 (利用者側の作業)

Excel / Numbers / LibreOffice のいずれかで開いて「**ファイル → 名前を付けて保存 → PDF**」。xlsx の直接変換を自動化しなかったのは意図的で、詳細は [詳細設計 §4.1](docs/dev/plugins/paper-excel-to-table.md) を参照してください。

### 2. Claude Code セッションで依頼

```
この PDF を CSV 化して: /path/to/your.pdf

これは◯◯市の水道事業業務年報のレイアウト (2025 年度)。項目コード (item_code)
は各行の右端にあり、インデントで親子関係を表現している。脚注は ※印で分離して。
```

`paper-excel-to-table` の SKILL.md が自動で発火し、Opus 4.7 の subagent が:

1. PDF を高解像度 PNG にラスタライズ (300 DPI, macOS PDFKit 経由)
2. ページ全体を観察し、抽出プラン (列位置・ID 列の側・階層表現) を策定
3. 初回抽出 → 低確度セルを検出 → 該当領域を **自動でトリミング** して native 解像度で再観察 → CSV に上書き
4. (オプション) YAML スキーマがあれば Pydantic で validate
5. 「何行抽出した / 低確度セルはどこ / ID 列は左右どちらだったか」の短いレポートを返す

確信が持てなかったセルは空欄ではなく **`?`** でマークされます。重要な分析の前には、必ず元 PDF と突き合わせてください。

---

## 前提と制約

| 項目 | 現状 |
|---|---|
| 対応 OS | macOS のみ (PDF ラスタライズに PDFKit を使うため) |
| xlsx → PDF 変換 | 利用者が事前に手動で実施。skill では自動化していない |
| API キー | e-Stat 系: `ESTAT_APP_ID` 必須 / paper-excel-to-table: 不要 (Claude Code セッション内で完結) |
| Claude Code バージョン | 0.124.0 以降で動作確認 |
| 精度 | vision LLM の出力につき不確実性あり。`?` マーク運用で保険 |

---

## 開発

Markdown の検査には markdownlint と textlint を使います。textlint は `@textlint-ja/textlint-rule-preset-ai-writing` を有効にしています。

```shell
npm install
npm run lint:md
```

commit 前に staged Markdown だけ検査したい場合は、ローカル hooks を有効化してください。

```shell
npm run hooks:install
```

無効化する場合は次を実行します。

```shell
npm run hooks:uninstall
```

---

## ロードマップ

MVP はここまで動いています。先の予定:

- e-Stat API関連のskills追加
- **Linux / Windows 対応** — PDF ラスタライザの PyMuPDF 代替実装 (現状 PDFKit 依存で macOS 限定)

興味のある方向性があれば [Issues](https://github.com/K-Oxon/e-stat-wrangling-skills/issues) にどうぞ。

---

## ライセンス

[MIT](LICENSE)
