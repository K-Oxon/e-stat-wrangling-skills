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

### クライアント別の実行例

`prepare` の後、作業ディレクトリに移動して実行する。下の `repo` はこのリポジトリの絶対パス。エージェントが `uv` を実行できることを事前に確認する。ネットワークを制限したセッションでは、ラスタライズ・裁断・スキーマ検証の依存を先に取得しておく。

```sh
repo="$PWD"
cd "$work_dir"
git init -q
```

- **Opus 4.7**。基準はコミット `76e9109` のプラグイン。

  ```sh
  baseline="$(mktemp -d)"
  git -C "$repo" archive 76e9109 plugins/paper-excel-to-table | tar -xf - -C "$baseline"
  claude -p --model claude-opus-4-7 --effort high \
    --plugin-dir "$baseline/plugins/paper-excel-to-table" \
    --permission-mode acceptEdits --allowedTools 'Bash(uv run --script *)' Agent < prompt.txt
  ```

- **Opus 5.5**。Claude の帳票プラグインが有効になっていないセッションで、スキルをプロジェクトに導入する。

  ```sh
  gh skill install "$repo" --from-local --all --agent claude-code --scope project
  claude -p --model claude-opus-5-5 --effort high \
    --permission-mode acceptEdits --allowedTools 'Bash(uv run --script *)' < prompt.txt
  ```

- **GPT-6.2 Astra** と **Gemini 4 Neon**。それぞれ新しい作業ディレクトリで `gh skill install "$repo" --from-local --all --agent codex --scope project` を実行する。

  ```sh
  codex exec --model gpt-6.2-astra -c 'model_reasoning_effort="high"' \
    --sandbox workspace-write - < prompt.txt
  ```

  ```sh
  agy --model gemini-4-neon-high --mode accept-edits \
    --settings '{"permissions":{"allow":["command(uv)","command(ls)","command(pwd)","command(which)","command(mkdir)","command(cat)","command(wc)","command(head)"]}}' \
    -p "$(cat prompt.txt)"
  ```

## 採点の考え方

- キーの F1 は一意に対応した行を、期待行数と出力行数を使って評価する。余分な行や重複は得点を下げる。
- 構造化正答率は階層、属する区分、行・列見出し、単位、入力欄の種別を評価する。欠落行も分母に含む。行順、全角・半角、空白、採点データで明示した表記ゆれを許容する。
- 重要注記の保持率は、あらかじめ指定した選択肢、表示単位、列に付く記入上の指示を確認する。注記全体の逐語一致は求めない。

結果はこの2ケースに対する、モデルと利用クライアントを組み合わせた評価。ケースごとの原本に対する得点も残す。

## 2026-11-25 の実測

macOS 上で公開帳票2ケースを、各モデル・ケースにつき3回ずつ抽出した。Opus 4.7 は変更前のプラグイン経由で、候補はスキル単体で実行した。

| モデル | ケース | キー F1 | 構造化正答率 | 重要注記の保持率 | 判定 |
| --- | --- | ---: | ---: | ---: | --- |
| Claude Opus 4.7 | 1ページ目 | 100.0% | 81.1% | 95.8% | 基準 |
| Claude Opus 4.7 | 6ページ目 | 100.0% | 94.0% | 100.0% | 基準 |
| Claude Opus 5.5 | 1ページ目 | 100.0% | 84.2% | 97.9% | 現行以上 |
| Claude Opus 5.5 | 6ページ目 | 100.0% | 100.0% | 100.0% | 現行以上 |
| GPT-6.2 Astra | 1ページ目 | 100.0% | 87.8% | 95.8% | 現行以上 |
| GPT-6.2 Astra | 6ページ目 | 100.0% | 100.0% | 100.0% | 現行以上 |
| Gemini 4 Neon | 1ページ目 | 100.0% | 86.1% | 95.8% | 現行以上 |
| Gemini 4 Neon | 6ページ目 | 100.0% | 100.0% | 100.0% | 現行以上 |

両ケースで Opus 4.7 以上だったモデルは Claude Opus 5.5、GPT-6.2 Astra、Gemini 4 Neon。

Gemini の起動確認では headless モードが補助コマンドを拒否したため、作業ディレクトリの閲覧と抽出に必要なコマンドを許可してから計測した。ある試行で、CSV 書き込み後に追加のシェル処理が拒否され、エージェントの最終報告が空になった。CSV の構造化品質は採点し、24件の出力は別途スキーマ検証も通した。

[試行別の得点・モデルID・CLIバージョン](../samples/paper-excel-to-table/tk46-010-001/evaluation/results-2026-11-25.json)
