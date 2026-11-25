# 紙帳票の構造化品質評価

公開の [水道事業調査票](../samples/paper-excel-to-table/tk46-010-001/context.md) から2ケースを採点する。1ページ目は左右2段に印刷された72項目。6ページ目は企業債表の列 (1)・(13)・(16) の36項目で、繰り返し見出し、階層、記入不可欄、矢印付き注記を含む。

採点用 CSV は原本の欄番号と見出しを照合して作った。1ページ目は既存のサンプル CSV を出発点とし、親見出し、末端のラベル、記入不可欄の扱いを評価用に整理した。両ケースの出力列と評価対象は [評価データ](../samples/paper-excel-to-table/tk46-010-001/evaluation/) にある。

## 評価を実行する

リポジトリのルートから、ケースごと・試行ごとに空の作業ディレクトリを用意する。

```sh
eval_script="$PWD/scripts/evaluate_paper_excel.py"
work_dir="$(mktemp -d)"
uv run --script "$eval_script" prepare --case page-01 --work-dir "$work_dir"
```

作業ディレクトリには公開 PDF、スキーマ、依頼文だけが入る。そのディレクトリに評価対象のスキルを導入し、`prompt.txt` を新規セッションに渡す。モデルは明示指定し、同じケースを高推論設定で3回ずつ実行する。基準は変更前の Claude Code プラグインの Opus 4.7 で、変更前のプラグインだけをロードする。依頼文を渡す際は作業ディレクトリ外の採点用データ、サンプル CSV、他の試行結果へのパスを渡さない。

```sh
uv run --script "$eval_script" score --case page-01 --csv "$work_dir/result.csv" > trial.json
uv run --script "$eval_script" compare --case page-01 \
  --baseline baseline-1.json baseline-2.json baseline-3.json \
  --candidate candidate-1.json candidate-2.json candidate-3.json
```

6ページ目は `--case page-06` で繰り返す。比較結果はケースごとの3指標の中央値を示す。すべての中央値が基準以上なら `at_least_baseline`、下回る指標があれば `below_baseline`、採点可能な試行が不足すれば `unverified`。試行ごとにモデルのID、CLIのバージョン、推論設定と採点結果を記録する。

## 採点の考え方

- キーの F1 は一意に対応した行を、期待行数と出力行数を使って評価する。余分な行や重複は得点を下げる。
- 構造化正答率は階層、属する区分、行・列見出し、単位、入力欄の種別を評価する。欠落行も分母に含む。行順、全角・半角、空白、採点データで明示した表記ゆれを許容する。
- 重要注記の保持率は、あらかじめ指定した選択肢、表示単位、列に付く記入上の指示を確認する。注記全体の逐語一致は求めない。

結果はこの2ケースに対する、モデルと利用クライアントを組み合わせた評価。ケースごとの原本に対する得点も残す。
