# 帳票の抽出手順

## 入力

- `image_paths` と `output_csv_path` は必須。画像は対象ページ順に絶対パスで渡す。欠けている場合は `MISSING_INPUT:` と対象項目を返す。
- `user_context` に帳票名、対象ページ、既知の項目と意味を渡す。画像を確認しても必要な意味が特定できない場合は、`INSUFFICIENT_CONTEXT:` と確認事項を返す。
- `schema_path` は任意の検証用 YAML の絶対パス。
- `workdir` は裁断画像の保存先。省略時は先頭のページ画像と同じディレクトリ。
- `rasterize_info` があればページ数・画像寸法はその JSON を参照する。ツールはこのスキルの `scripts/` にある。

## PDF のラスタライズ

```sh
uv run --script "$SKILL_DIR/scripts/rasterize.py" "$PDF" "$WORKDIR" --dpi 300 --pages "$PAGES"
```

`--pages` は `1`、`1,3,5`、`2-4,7`、`1-` の形式。省略すると全ページを出力する。stdout の JSON に `page_count` とページごとの画像パス・寸法が入る。300 DPI の画像を保持しておくと、細かなセルを裁断して拡大したときにも元の画素を使える。

## 観察・抽出・検証

1. 各画像を開き、データ、見出し、メタデータの位置を把握する。識別子は右端や複数箇所に載ることがあるため、位置を特定する。インデント・箇条書き・段番号・見出しを階層に対応付け、見た目のセル結合から論理的な項目の境界を判断する。指定された YAML は [schema.py](../scripts/schema.py) の `dump-json-schema --schema` で確認できる。
2. 指定のパスに UTF-8 CSV を書く。階層を整数の `level` 列に入れる。平坦な表は0とする。空欄、存在しないセル、読み取れないセルを区別し、読み取れないセルには `?` を入れる。脚注と補足記号は `notes` などに保持し、保持できないものは報告する。
3. CSV と原画像を照合する。`?`、文字密度の高い箇所、異常な桁数、見落とした脚注の周辺を優先して裁断し、裁断画像を開いて該当セルを更新する。

   ```sh
   uv run --script "$SKILL_DIR/scripts/crop.py" "$IMAGE" \
     --rel-box x,y,w,h -o "$WORKDIR/crop-01.png"
   ```

   原点は左上。比率指定 `--rel-box` とピクセル指定 `--box` は別の呼び出しにする。同じ形式の矩形と `-o` を繰り返せば複数の裁断をまとめられる。裁断の呼び出しは1回の抽出につき最大6回。残った未読セルは `?` のまま報告する。
4. YAML が指定されていれば `uv run --script "$SKILL_DIR/scripts/schema.py" validate "$CSV" --schema "$SCHEMA"` を実行する。エラーに対応する箇所を再観察し、最大3回再検証する。スキーマの `allow_unknown` は `?` の扱いを指定する。
5. `csv_path`、`rows`、`id_column` と元画像上の位置、`hierarchy_signal`、`crops_used`、`low_confidence`、`schema_validation`、`notes_for_user` を報告する。

抽出中の書き込み先は出力 CSV と `workdir` 内の `crop-*.png` に限る。上限に達した場合は、残りの問題を明記して途中結果を渡す。
