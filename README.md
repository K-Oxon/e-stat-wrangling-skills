# e-stat-wrangling-skills

e-Statを本当に実務で使うためのAgent Skills

---

## Why and What

[e-Stat (政府統計の総合窓口)](https://www.e-stat.go.jp/) は日本の公的統計を扱うなら避けて通れない一方で、検索性と機械判読性はとにかく厳しい状況です。

このリポジトリはe-Statからデータを分析可能な状態にするまでの工数をできる限り減らすことを目的に、数々の知見を Claude Code セッションに直接 install できるように plugin の形でまとめたものです。

## こんな人に

- 人口データや自治体決算などの行政データを分析したい人
- 研究者・大学院生: 人口・経済統計を時系列で継続的に取りたい人
- データエンジニア / データアナリスト: e-Stat を一次情報源にしてデータパイプラインを組みたい人

---

## できること

| Plugin | Skill | 何ができるか | Status |
| --- | --- | --- | --- |
| [`paper-excel-to-table`](plugins/paper-excel-to-table/) | [`paper-excel-to-table`](plugins/paper-excel-to-table/skills/paper-excel-to-table/) | 紙様式 Excel を PDF 化したものから、Opus 4.7 の vision で構造化 CSV を取り出す。低確度セルは自動トリミングで再観察 | Alpha (macOSのみ) |
| [`estat-api`](plugins/estat-api/) | [`estat-file-search`](plugins/estat-api/skills/estat-file-search/) | e-Stat のファイル提供データ (xlsx/csv/pdf) を探索・ダウンロード | MVP |
| [`estat-api`](plugins/estat-api/) | [`estat-api-data-search`](plugins/estat-api/skills/estat-api-data-search/) | e-Stat API/DB 提供の統計表を探索し、`statsDataId` を特定 | MVP |

---

## Install

```
/plugin marketplace add K-Oxon/e-stat-wrangling-skills
/plugin install paper-excel-to-table@e-stat-wrangling
/plugin install estat-api@e-stat-wrangling
```

Claude Code の使用が前提です。

### 初回 install 時の注意

subagent を同梱する plugin (現状 `paper-excel-to-table`) は、**初回 install 直後に認識されないことがあります**。その場合は次を実行します。

```
/reload-plugins
```

を 1 回実行してから試してください。

### 推奨 permissions (任意)

頻出の Bash 呼び出しで permission プロンプトを抑えたいときは、`~/.claude/settings.json` に次を追加すると快適です。

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

`paper-excel-to-table` は最も「痛みに効く」plugin です。
公営企業決算状況調査の調査票のような **印刷前提の紙様式 Excel** を構造化したcsvに抽出します。従来のLLMでは意味推論が難しかった部分もClaude Opus 4.7の高画質対応と高推論モードを使うことでかなり精度高く構造化可能です。
（現在はAlpha版 MacOS * Claude codeの環境のみ）

### 1. xlsx を PDF に変換 (利用者側の作業)

Excel / Numbers / LibreOffice のいずれかで開いて「**ファイル → 名前を付けて保存 → PDF**」。xlsx PDFの直接変換はこのskillsの対象外です。

### 2. Claude Code セッションで依頼

```
この PDF を CSV 化して: /path/to/your.pdf

これは地方財政決算状況調査の水道事業の調査票レイアウト (2025 年度)。列番号が各行の右端にあり、インデントで親子関係を表現している。
```

`paper-excel-to-table` の SKILL.md が自動で発火し、Opus 4.7 の subagent が次を実行します。

1. PDF を高解像度 PNG にラスタライズ (300 DPI, macOS PDFKit 経由)
2. ページ全体を観察し、抽出プラン (列位置・ID 列の側・階層表現) を策定
3. 初回抽出 → 低確度セルを検出 → 該当領域を自動でトリミングして native 解像度で再観察 → CSV に上書き
4. (オプション) YAML スキーマがあれば Pydantic で validate
5. 「何行抽出した / 低確度セルはどこ / ID 列は左右どちらだったか」の短いレポートを返す

確信が持てなかったセルは空欄ではなく`?`でマークされます。重要な分析の前には、必ず元 PDF と突き合わせてください。

## ユースケース — e-Stat APIでe-Statから統計データを自然言語で検索

自然言語でe-Statに登録されている統計データを検索できます。
ファイルとAPI提供データ、どちらも検索対象です。

※ e-Stat APIの利用が前提になります。skillの利用までに環境変数などで以下をsetしておいてください。
`ESTAT_APP_ID` は <https://www.e-stat.go.jp/mypage/user/preregister> から取得できます。

```
export ESTAT_APP_ID=[YOUR KEY]
```

### 検索例

```text
政府統計:地方財政状況調査の中から地方公営企業決算状況調査の水道の調査票を探して
最新年がいつかも知りたい
```

---

## 前提と制約

| 項目 | 現状 |
| --- | --- |
| 対応 OS | macOS のみ (PDF ラスタライズに PDFKit を使うため) |
| xlsx → PDF 変換 | 利用者が事前に手動で実施。skill では自動化していない |
| API キー | e-Stat 系: `ESTAT_APP_ID` 必須 / paper-excel-to-table: 不要 (Claude Code セッション内で完結) |
| Claude Code バージョン | 0.124.0 以降で動作確認 |
| 精度 | vision LLM の出力につき不確実性あり。`?` マーク運用で保険 |

---

## ライセンス

[MIT](LICENSE)

## for Developer

lint:

```shell
npm install
npm run lint:md
```

If you want to check only staged Markdown before committing, please enable local hooks.

```shell
npm run hooks:install
```

To disable, follow the steps below:

```shell
npm run hooks:uninstall
```
