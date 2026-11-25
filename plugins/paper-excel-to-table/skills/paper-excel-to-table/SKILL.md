---
name: paper-excel-to-table
description: Extract structured CSV from paper-style form PDFs, including surveys, scanned forms, and Excel forms exported to PDF. Use when asked to convert a complex form or 調査票レイアウト・紙様式の帳票 into structured table data.
license: MIT
compatibility: PDF rasterization requires macOS with Xcode Command Line Tools, uv, and Python 3.12+. Extraction requires image viewing, shell execution, and local file writing.
---

# paper-excel-to-table

細かい文字や複雑な階層のある帳票には、画像入力に対応したフロンティアモデルと高めの推論設定を推奨する。

1. 確認するのは、入力 PDF、対象ページ、出力 CSV の保存先、帳票の用途や既知の項目、任意の YAML スキーマ。依頼に含まれる情報を使い、帳票の解釈に必要な不足情報を尋ねる。入力が xlsx のときは、Excel・Numbers・LibreOffice で PDF に書き出してもらう。
2. このスキルのディレクトリを基準に [rasterize.py](scripts/rasterize.py) を `uv run --script` で呼び、対象ページを300 DPIで出力する。stdout の JSON から対象画像の絶対パス、ページ番号、寸法を取得する。
3. [抽出手順](references/extraction.md) に従って、画像の観察、CSV への抽出、裁断と再観察、任意のスキーマ検証を行う。
   - Claude Code プラグイン経由では、Agent ツール（バージョンによっては Task）で `paper-excel-to-table:paper-excel-extractor` を呼ぶ。手順にある入力と手順ファイルの絶対パスを渡す。モデルや推論レベルはセッション側の設定に任せ、サブエージェント側で画像を観察・抽出する。
   - スキル単体の導入など、専用サブエージェントが利用できない場合は、現在のセッションの画像閲覧、シェル、ファイル書き込みツールで手順を実行する。
4. 出力 CSV のパス、行数、未読セル、スキーマ検証結果を伝える。`INSUFFICIENT_CONTEXT:` なら必要な情報を尋ね、`MISSING_INPUT:` なら呼び出し側のパラメーターを補う。

CLI の引数と抽出手順は [抽出手順](references/extraction.md) を参照する。繰り返し処理のスキーマ例は [水道事業調査票のスキーマ](scripts/schemas/suido_gyomu_nenpo.yaml) にある。
