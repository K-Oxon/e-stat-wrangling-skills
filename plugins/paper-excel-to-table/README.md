# paper-excel-to-table

紙の帳票に合わせた Excel を PDF に書き出し、そのレイアウトから分析用の構造化 CSV を作るスキルです。結合セルや複数段の見出しを調べ、細かい箇所は元の画像を裁断して見直します。

## 導入と前提

[リポジトリのインストール手順](../../README.md#インストール)を参照してください。Claude Code プラグインは、画像の確認と抽出を親セッションから分けるためにサブエージェントを使います。モデルは通常、親セッションの選択を継承します。Codex や Antigravity CLI では、セッションで選んだモデルがスキルを直接実行します。

- PDF ラスタライズには macOS、Xcode Command Line Tools、`uv`、Python 3.12 以上が必要です。
- エージェントは画像を表示し、シェルを実行し、作業ディレクトリに書き込める必要があります。
- 入力は PDF です。Excel・Numbers・LibreOffice から事前に PDF に書き出してください。
- 複雑な帳票には、画像入力に対応したフロンティアモデルと高めの推論設定を推奨します。

## 依頼例

```text
/path/to/form.pdf の1ページ目を result.csv に構造化して。
地方公営企業決算状況調査の水道事業の調査票です。「行」と「列番号」の組が項目のキーです。
```

帳票名、対象ページ、識別子の位置や階層の付け方、保存先を伝えると抽出時の確認が減ります。読めなかったセルは `?` で示し、抽出後の報告に残します。

列が決まった帳票を繰り返し扱う場合は、依頼に YAML スキーマのパスを添えてください。スキルは抽出した CSV をそのスキーマで検証します。[水道事業のスキーマ例](skills/paper-excel-to-table/scripts/schemas/suido_gyomu_nenpo.yaml)をベースにできます。

## 詳細

- [CLI と抽出手順](skills/paper-excel-to-table/references/extraction.md)
- [公開帳票の構造化品質評価と再現手順](../../docs/paper-excel-evaluation.md)
