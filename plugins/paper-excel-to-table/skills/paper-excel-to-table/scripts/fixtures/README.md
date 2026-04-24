# fixtures

この skill には大きな PDF サンプルを **同梱しません**。検証に使う PDF は repo 内の別の場所に置いてあります。

- `docs/dev/ﾚｲｱｳﾄ_tk46_010_001.pdf`
  - 出典: [地方公営企業決算状況調査 | 2025年度 | 調査票レイアウト（水道事業）](https://www.e-stat.go.jp/stat-search/files?page=1&layout=datalist&toukei=00200251&tstat=000001125335&cycle=7&year=20250&month=0&tclass1=000001125336&tclass2=000001125337)
  - 10 ページ / A4 縦主体 + 一部横
  - skill の e2e 検証 (SKILL.md の「抽出ワークフロー」) はこの PDF のページ 1 を対象に行う

同梱しない理由:

- 配布サイズを小さく保つ (skill は軽量 text + scripts に留める)
- 統計表レイアウト PDF のライセンス取り扱いを skill 単体の配布条件から切り離す
