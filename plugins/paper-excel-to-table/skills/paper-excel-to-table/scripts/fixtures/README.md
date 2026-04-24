# fixtures

この skill には検証用 PDF を **同梱しません**。サンプル一式は repo root の
[`samples/paper-excel-to-table/`](../../../../../../samples/paper-excel-to-table/) 配下に置いてあります。

同梱しない理由:

- `plugins/` 配下に置くと `/plugin install` で利用者の環境にまでコピーされてしまう (~1 MB の無駄)
- サンプル原本のライセンス管理 (政府統計データの出典明記) を skill 配布の仕組みから切り離したい

## 現在のサンプル

| ID | 原本 | 概要 |
|---|---|---|
| [`tk46-010-001`](../../../../../../samples/paper-excel-to-table/tk46-010-001/) | 地方公営企業決算状況調査 (水道事業) 調査票レイアウト | 10 ページ / A4 縦横混在 |

各サンプル配下の `context.md` に出典 URL・抽出時の user_context・抽出結果 (`extracted.csv`) の注意点が記載されています。
