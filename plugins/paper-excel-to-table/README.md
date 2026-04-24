# paper-excel-to-table

**紙様式 Excel を PDF 化したものから、Opus 4.7 の vision で構造化 CSV を取り出す Claude Code plugin。**

[English version →](README.en.md) / [プロジェクト全体 →](../../README.md)

---

## この plugin は何をしてくれるか

たとえば、水道事業業務年報のような **「セル結合だらけの紙様式 Excel」** を Claude Code にこう頼めるようになります:

```
この PDF を CSV 化して: /path/to/suido_nenpo.pdf

これは◯◯市の水道事業業務年報 (2025 年度) のレイアウト。item_code は各行の
右端にあり、インデントで親子関係を表現している。脚注は ※印。
```

裏で起きること:

1. PDF を高解像度 PNG (300 DPI) にラスタライズ
2. **専用の subagent** (`paper-excel-extractor`, Opus 4.7 / `effort: high`) が画像を読み、抽出プランを立てる
3. 初回抽出 → 低確度セルを検出 → 該当領域を **自動でトリミング** → native 解像度で再観察 → CSV に上書き
4. (オプション) YAML スキーマがあれば Pydantic で validate
5. 抽出行数・ID 列の位置 (左右)・低確度セル一覧などの短いレポートを返す

subagent 経由で走らせるので **main セッションの文脈に画像バイトや中間 CSV が流れ込まず**、long context を汚しません。

---

## 前提

| 項目 | 要求 |
|---|---|
| OS | macOS (PDF ラスタライズに PDFKit を使うため) |
| Xcode Command Line Tools | `xcode-select --install` 済み (`swift` コマンドが通ること) |
| Claude Code | 0.124.0 以降 |
| 入力 | **PDF のみ**。xlsx は利用者側で「ファイル → 名前を付けて保存 → PDF」しておく |
| API キー | 不要 (Claude Code セッション内の Opus 4.7 が vision をやる) |

xlsx → PDF を自動化しないのは、Excel/Numbers の「PDF として保存」経路が再現性で最も信頼できる / 代替 (LibreOffice headless 等) は崩れるケースが多い、という設計判断です ([詳細設計 §4.1](../../docs/dev/plugins/paper-excel-to-table.md))。

---

## Install

Claude Code のセッション内で:

```
/plugin marketplace add K-Oxon/e-stat-wrangling-skills
/plugin install paper-excel-to-table@e-stat-wrangling
```

### 初回 install 直後の注意

subagent が認識されないことがあるので、`/plugin install` の直後に:

```
/reload-plugins
```

を 1 回実行してください。2 回目以降の session ではこの手順は不要です。

### 推奨 permissions (任意)

頻出コマンドの permission プロンプトを抑えたいとき、`~/.claude/settings.json` に:

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

plugin 側で同梱する仕組みはまだ Claude Code 側が対応していないため、各自の settings に追加する運用です。

---

## 使い方

Claude Code セッションで自然言語で頼むだけで動きます:

```
/path/to/form.pdf を CSV にしたい。帳票は介護保険事業状況報告(月報)のレイアウト。
1 ページ目だけでよい。
```

SKILL.md の trigger が発火して、上の「何をしてくれるか」節の 5 ステップが実行されます。

### あらかじめ渡しておくと精度が上がる情報

subagent は最初に user_context を要求します。以下を先に伝えると「INSUFFICIENT_CONTEXT」による再質問ラウンドが省けます:

- **帳票の正式名称** (例: 地方公営企業決算状況調査 水道事業レイアウト)
- **年度 / 対象機関**
- **既知の列構成や語彙** (「item_code は右端」「※は脚注番号」「値の `-` は欠損」等)
- **対象ページ**
- **(あれば) YAML スキーマのパス**

---

## Schema-driven モード

列定義が決まっている帳票を繰り返し処理する場合、YAML スキーマを渡すと Pydantic で validate されます。依頼時に `--schema <path>` のような指定でなく、自然言語でパスを伝えれば SKILL.md のワークフローが subagent prompt に組み込んでくれます。

### サンプル: 水道事業業務年報用

同梱されている `scripts/schemas/suido_gyomu_nenpo.yaml` が最小例です:

```yaml
name: suido_gyomu_nenpo
description: 地方公営企業決算状況調査 (水道事業) レイアウト用のサンプルスキーマ。
primary_key: [item_code]
columns:
  - name: level
    type: int
    required: true
    description: インデントで表現された階層深さ (0 始まり)。
  - name: item_code
    type: str
    required: true
  - name: item_label
    type: str
    required: true
  - name: unit
    type: str
    required: false
  - name: value
    type: str           # 数値でない "-" や注記が混じるので str
    required: false
  - name: notes
    type: str
    required: false
```

スキーマの仕様は `scripts/schema.py` の docstring 参照。

---

## 同梱スクリプトを直接呼ぶ (デバッグ / 非 Claude Code 利用)

通常は Claude Code 経由ですが、個別の動作確認には直接 CLI でも呼べます。

### 1. PDF をラスタライズ

```bash
uv run --script plugins/paper-excel-to-table/skills/paper-excel-to-table/scripts/rasterize.py \
  input.pdf out_dir/ [--dpi 300] [--pages 1-]
```

stdout に `page_count` やページ毎の `width_px`/`height_px` を含む JSON が出ます。

### 2. 画像を切り出す

```bash
uv run --script plugins/paper-excel-to-table/skills/paper-excel-to-table/scripts/crop.py \
  out_dir/page-001.png --rel-box 0.0,0.15,1.0,0.25 -o crop.png
```

`--box` (絶対 px) と `--rel-box` (0-1 比率) が選べます。同一コマンド内では混ぜられない (Typer の制約) ので、両方使うときは 2 回呼んでください。

### 3. CSV をスキーマ検証

```bash
uv run --script plugins/paper-excel-to-table/skills/paper-excel-to-table/scripts/schema.py \
  validate out.csv --schema scripts/schemas/suido_gyomu_nenpo.yaml
```

失敗時は stderr に「どの行のどの列がなぜ NG か」が行単位で列挙されます。

---

## 落とし穴 (知っておくと事故りにくい)

| 項目 | 対処 |
|---|---|
| インデント階層が CSV では消える | subagent は必ず `level` 列 (0 始まり整数) を付ける。スキーマでも `level: int, required: true` を強制 |
| ID 列が右端にある帳票がそこそこある | 左→右を盲信しない。ID 列の side を subagent レポートの `id_column` で明示確認 |
| 視覚的なセル結合 ≠ 論理的なセル結合 | 枠線の有無だけで判断しない。元帳票の意味論をユーザー側コンテキストで渡す |
| 脚注 (※, 注1, `*`) | 値列に混ぜず `notes` 列に分離 |
| 確信が無いセル | 空欄にせず `?` でフラグ。subagent レポートの `low_confidence` に出る |
| Opus 4.7 の vision は入力 ~2576 px (長辺) に自動ダウンスケール | raw は 300 DPI で保存し、crop 後の部分画像で native 解像度を使う設計 |

---

## 関連ドキュメント

- [詳細設計 (design doc)](../../docs/dev/plugins/paper-excel-to-table.md) — なぜ subagent 構成か、backend contract、将来の package 化判断
- [プロジェクト全体の README](../../README.md)
- [SKILL.md](skills/paper-excel-to-table/SKILL.md) — Claude Code 向けのトリガー + ワークフロー (LLM が見る面)
- [agents/paper-excel-extractor.md](agents/paper-excel-extractor.md) — subagent の入力契約と厳守ルール

---

## ライセンス

[MIT](../../LICENSE) — プロジェクト全体と同じ。
