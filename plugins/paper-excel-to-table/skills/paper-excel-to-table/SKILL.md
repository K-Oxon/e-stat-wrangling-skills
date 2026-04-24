---
name: paper-excel-to-table
description: Use this when the user wants to turn a paper-style Excel workbook (already exported as PDF) into a structured CSV. Triggers on requests like "紙様式の帳票を CSV 化したい" / "複雑なセル結合の Excel を構造化したい" / "調査票レイアウト PDF から表を取り出したい" / "e-Stat の調査票レイアウトを機械判読可能にしたい". macOS only in MVP.
---

# paper-excel-to-table

紙様式の Excel 帳票 (人間の記入しやすさを最適化したレイアウト) を PDF 化したものから、構造化 CSV を取り出すワークフロー。

## いつこの skill を使うか

- 「水道事業業務年報みたいな **紙帳票 Excel** を CSV にしたい」
- 「セル結合・装飾だらけの調査票レイアウトを機械判読可能にしたい」
- 「e-Stat の調査票レイアウト PDF を構造化したい」

## 入力前提 (重要)

- **入力は PDF 固定**。xlsx を渡された場合は、ユーザーに以下を案内して中断する:
  - Excel の「ファイル → 名前を付けて保存 → PDF」
  - Numbers の「書き出す → PDF」
  - LibreOffice の「ファイル → エクスポート → PDF」
  - xlsx → 画像の自動化は意図的に非対応 (見た目の再現性・安定性の問題。詳細は `docs/dev/plugins/paper-excel-to-table.md` §4.1)
- **macOS のみ**。rasterize.swift が PDFKit を使うため、Darwin 以外では fail-fast

## 抽出ワークフロー

以下を必ず順番に踏む。各ステップを飛ばさない。

### 1. ユーザーコンテキストの確認 (省略しない)

抽出の精度はユーザーから得られる前提情報で大きく変わる。ユーザーに以下を尋ねる (既に提供されていれば繰り返さない):

- この帳票は何の調査票・年報か (正式名称、発行元)
- 既知の列・項目・語彙 (「item_code は右端にある」「※印は脚注番号」など)
- 対象ページ (複数ページ PDF の場合)
- スキーマ (YAML) を持っているか — 持っていれば絶対パスを受け取る
- 出力 CSV の保存先

コンテキストが薄いまま進めない。抽出精度を律速する。

### 2. PDF を画像化

`scripts/rasterize.py` を `uv run --script` で呼ぶ (単一 PDF は 1 コマンドで全ページを出す):

```bash
uv run --script <PLUGIN_ROOT>/skills/paper-excel-to-table/scripts/rasterize.py \
  <INPUT_PDF> <OUT_DIR> [--dpi 300] [--pages 1-]
```

- デフォルト `--dpi 300` (A4 縦 ~2481×3508 px)。**下げない**。高解像度を保ったまま後段の crop で自然に API 入力上限に収まる設計
- 出力は `OUT_DIR/page-001.png`, `page-002.png`, ...
- stdout に Backend Contract の JSON (ページごとの px サイズ等) が出る。次ステップで渡すパスはここから拾う

### 3. サブエージェント `paper-excel-to-table:paper-excel-extractor` で抽出

**重要**: 画像 Read や抽出ロジックは subagent 側で行う。main セッションでは画像を直接 Read しない — コンテキスト汚染を避けるため。

`Agent` tool で `subagent_type=paper-excel-to-table:paper-excel-extractor` を起動し、prompt に以下を **プレーンテキストで** 詰める:

```
image_paths:
  - <abs path to page-001.png>
  - (必要なら追加ページ)
output_csv_path: <abs path to out.csv>
user_context: |
  - 帳票名: 地方公営企業決算状況調査 (水道事業) レイアウト
  - 年度: 2025
  - 既知の列: ...
schema_path: <abs path to schema yaml, 省略可>
workdir: <abs path for crop outputs, 省略可>
```

subagent は内部で観察プラン策定 → CSV 書き出し → 低確度箇所の crop → 再観察 → (schema があれば) validate まで回し、main には短いレポートだけを返す。

### 4. subagent の応答を処理

返答パターン別に対応:

- **通常応答** (`csv_path`, `rows`, `id_column`, `hierarchy_signal`, `crops_used`, `low_confidence`, `schema_validation`, `notes_for_user`): ユーザーに要約を提示。`low_confidence` に項目があればその旨を明示
- **`INSUFFICIENT_CONTEXT:` から始まる応答**: 続く質問をユーザーに投げ、回答を受けて手順 3 をやり直す
- **`MISSING_INPUT:` から始まる応答**: 自分の prompt 組み立てが不完全。不足を補って再実行

### 5. (schema 未指定のときの提案)

schema 無しで走ったケースでは、最後に「この CSV から YAML schema を抽出して、次回以降は schema-driven モードで検証可能にしますか？」とユーザーに提案する (実装は別タスク)。

## 典型的な落とし穴 (必ず目を通す)

### インデントによる階層 → `level` 列に必ず落とす

紙帳票は **インデント幅・箇条書き記号・フォント太さ・段付けた番号 (`1 / 1.1 / 1.1.1`)** で階層を表現する。この情報は CSV では消えるので、整数 `level` 列 (0 始まり) に落とし込む。subagent にはこれを厳守させるよう明示する。

### レイアウトは左→右とは限らない

ID / 項目コード / 連番が **右端** にある帳票は珍しくない。左→右ルールを盲信しない。subagent のレポートに「ID 列の位置 (left/right)」を必ず書かせる。

### 視覚的なセル結合 ≠ 論理的なセル結合

- 枠線がなくても別項目の場合がある
- 枠線があっても親項目 + 子項目を合体表示している場合がある
- 「値が空のセル」と「そもそもセルが存在しないセル」を区別する

### 脚注・補足記号 (※, 注1), *)

CSV 化のときは必ず別列 (`notes` など) に分ける。値列に混ぜない。

### 確信が持てないセルは空欄にしない

subagent は読み取れない値を **必ず `?` でマーク**するルール。空欄と混同しないこと。ユーザーへのレポートでも `?` の残存を明示する。

### ユーザーコンテキストの提供を促す

帳票には「その組織・業界で自明の語彙」が大量に入っている。LLM が推測するより、ユーザーに聞く方が圧倒的に速く正確。1. のステップをショートカットしない。

## リソース / CLI 引数

### `scripts/rasterize.py`

```
uv run --script <...>/scripts/rasterize.py <pdf> <out_dir>
  [--dpi 300] [--box media|crop] [--colorspace sRGB|Gray]
  [--alpha] [--no-annots] [--pages 1-|1,3,5|2-4,7]
```

- Swift 側 (`rasterize.swift`) が Backend Contract (`docs/dev/plugins/paper-excel-to-table.md` §4.3) に従った JSON を stdout に 1 発出す
- 300 DPI で A4 縦 ~2481×3508 px。**意図的に** Claude Vision の API 入力上限 (~2576 px) を超え、後段 crop 時に native 解像度を温存する

### `scripts/crop.py`

```
uv run --script <...>/scripts/crop.py <image>
  [--box x,y,w,h | --rel-box x,y,w,h] -o <out.png>
  (--box/--rel-box と -o を同数ペアで繰り返して複数 crop 可)
```

- 原点は **左上**。`--box` は絶対 px、`--rel-box` は画像サイズに対する比率 0..1
- 出力 PNG は入力 PNG の DPI メタを引き継ぐ

### `scripts/schema.py`

```
uv run --script <...>/scripts/schema.py validate <csv> --schema <yaml>
uv run --script <...>/scripts/schema.py dump-json-schema --schema <yaml>
```

- YAML から Pydantic モデルを動的生成して CSV を validate
- `allow_unknown: true` の列では `?` (未読センチネル) を通す
- validate 失敗時は stderr に行単位の issue を列挙して non-zero exit

### 参考 schema

- `scripts/schemas/suido_gyomu_nenpo.yaml` — 水道事業決算状況調査レイアウト用の最小例

## 環境

- 必須: macOS + Xcode Command Line Tools (`swift` コマンド)
- **不要**: `ANTHROPIC_API_KEY` (MVP の抽出は Claude-native; subagent が Claude Code セッション内で動く)
- 将来 (Anthropic API 直叩き経路に昇格したとき): `ANTHROPIC_API_KEY`, `PAPER_EXCEL_MODEL` 等を追加 — `docs/dev/plugins/paper-excel-to-table.md` §9 参照
