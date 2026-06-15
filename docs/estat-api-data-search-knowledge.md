# estat-api-data-search knowledge dump

基本的なところは `estat-file-search-knowledge.md`と重なるところが多い。

異なるところは以下:

- APIエンドポイントが異なる (`getStatsList`)
- データセットという概念が曖昧になる。 実質、政府統計と統計表IDの2層だと思った方が良い
- ファイルではないのでURLではなく、統計表IDが重要となる。
  - `getStatsData` に統計表IDを入れて投げることで実際のデータを取得可能

## API検索APIについて

全く命名からは想像できないが、APIで提供されているデータを検索するときは、
`https://api.e-stat.go.jp/rest/3.0/app/json/getStatsList`
のエンドポイントを使う。

e.g. 社会・人口統計体系 の統計表一覧を取得する例

```bash
curl -X 'GET' \
  'https://api.e-stat.go.jp/rest/3.0/app/json/getStatsList?appId={E_STAT_APP_ID}&statsCode=00200502&limit=10' \
  -H 'accept: application/json'
```

### APIパラメータ

https://api.e-stat.go.jp/swagger-ui/e-statapi3.0.html#/%E7%B5%B1%E8%A8%88%E8%A1%A8%E6%83%85%E5%A0%B1%E5%8F%96%E5%BE%97/get-rest-json-statsList を参考にする

| カテゴリ | パラメータ名 | 型 | 必須 | 内容・仕様 | 備考・Tips |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **認証・基本** | **appId** | string | **○** | アプリケーションID |  |
| | **lang** | string | - | 取得言語（J：日本語 / E：英語） 省略時は「J」。Available: J, E | 基本全部省略でJでよい |
| **時間軸** | **surveyYears** | string | - | 調査年月（yyyy / yyyymm / yyyymm-yyyymm）統計の対象となった期間で検索 | 中身が多種多様すぎるのでほぼ使わない  |
| | **openYears** | string | - | 公開年月（yyyy / yyyymm / yyyymm-yyyymm）データが公開された期間で検索 | 信用できない |
| | **updatedDate** | string | - | 更新日付（yyyy / yyyymm / yyyymmdd / 範囲） 差分データのチェックに利用 | あまり信用できない |
| **分類・地域** | **statsField** | string | - | 統計分野（2桁：大分類 / 4桁：小分類）例：「03」労働・賃金、「0201」人口 | 無視でよし |
| | **statsCode** | string | - | 政府統計コード（5桁：作成機関 / 8桁：統計コード）  例：「00200521」国勢調査 | 重要  |
| | **collectArea** | string | - | 集計地域区分（1:全国 / 2:都道府県 / 3:市区町村） 検索データ種別=2（小地域）の場合は無効 | 無視でよし |
| **検索種別** | **searchKind** | string | - | 検索データ種別（1:統計情報 / 2:小地域・メッシュ） 省略時は「1」。Available: 1, 2  | 無視でよし |
| | **statsNameList** | string | - | 統計調査名一覧取得（Y：一覧を取得） Y指定時、統計表ではなく調査名一覧を出力 | 無視でよし (Yにはしない) |
| | **searchWord** | string | - | 検索キーワード（AND, OR, NOT検索対応） 表題やメタ情報から文字列検索 | ここは初見で政府統計の特定ができてないときに政府統計を特定するために使う |
| **取得制御** | **startPosition** | string | - | データ取得開始位置（1からの行番号） 継続取得時は前回の <NEXT_KEY> を指定 | 量が多い時はここでpagenation |
| | **limit** | string | - | データ取得件数（省略時は10万件）数値で指定（例：10） | ここは書いてある通り100000を信用してOK |
| | **explanationGetFlg** | string | - | 解説情報有無（Y：取得 / N：取得しない） 省略時は「Y」。Available: Y, N | 省略(Y)で良い |
| | **callback** | string | - | コールバック関数名 JSONP形式を利用する場合に必須 | 無視 |

基本的には、`statsCode`, `searchWord` のみを使う想定でよい。

### Resopnse

Header sample

```
access-control-allow-origin: * 
cache-control: no-store 
content-encoding: gzip 
content-type: application/json; charset=utf-8 
date: Sat,25 Apr 2026 04:41:58 GMT 
server: ZENEDGE 
strict-transport-security: max-age=0 
vary: Accept-Encoding 
x-cache-status: NOTCACHED 
x-cdn: Served-By-Zenedge 
x-content-type-options: nosniff 
x-frame-options: SAMEORIGIN 
x-xss-protection: 1; mode=block 
x-zen-fury: 616fd9b07c3eaf1afbe1bf94706ddd43d53c206d
```

Response sample:

`GET_STATS_LIST.DATALIST_INF.TABLE_INF`を見ればよい。

Swagger UIや仕様書に型定義があるがゆるふわでほぼ信用ならない(descriptionとかstrだったりstructだったり)ので基本的に現物をしっかり確認する。

```json
{
  "GET_STATS_LIST": {
    "RESULT": {
      "STATUS": 0,
      "ERROR_MSG": "正常に終了しました。",
      "DATE": "2026-04-25T13:41:58.516+09:00"
    },
    "PARAMETER": {
      "LANG": "J",
      "STATS_CODE": "00200502",
      "DATA_FORMAT": "J",
      "LIMIT": 3
    },
    "DATALIST_INF": {
      "NUMBER": 85,
      "RESULT_INF": {
        "FROM_NUMBER": 1,
        "TO_NUMBER": 3,
        "NEXT_KEY": 4
      },
      "TABLE_INF": [
        {
          "@id": "0000010101",
          "STAT_NAME": {
            "@code": "00200502",
            "$": "社会・人口統計体系"
          },
          "GOV_ORG": {
            "@code": "00200",
            "$": "総務省"
          },
          "STATISTICS_NAME": "都道府県データ 基礎データ",
          "TITLE": {
            "@no": "0000010101",
            "$": "Ａ　人口・世帯"
          },
          "CYCLE": "年度次",
          "SURVEY_DATE": 0,
          "OPEN_DATE": "2026-02-20",
          "SMALL_AREA": 0,
          "COLLECT_AREA": "全国",
          "MAIN_CATEGORY": {
            "@code": "99",
            "$": "その他"
          },
          "SUB_CATEGORY": {
            "@code": "99",
            "$": "その他"
          },
          "OVERALL_TOTAL_NUMBER": 550080,
          "UPDATED_DATE": "2026-02-20",
          "STATISTICS_NAME_SPEC": {
            "TABULATION_CATEGORY": "都道府県データ",
            "TABULATION_SUB_CATEGORY1": "基礎データ"
          },
          "DESCRIPTION": {
            "TABULATION_CATEGORY_EXPLANATION": "社会・人口統計体系の都道府県ごとに集計したデータを提供します。"
          },
          "TITLE_SPEC": {
            "TABLE_NAME": "Ａ　人口・世帯"
          }
        },
        {
          "@id": "0000010101",
          "STAT_NAME": {
            "@code": "00200502",
            "$": "社会・人口統計体系"
          },
          "GOV_ORG": {
            "@code": "00200",
            "$": "総務省"
          },
          "STATISTICS_NAME": "都道府県データ 基礎データ",
          "TITLE": {
            "@no": "0000010101",
            "$": "Ａ　人口・世帯"
          },
          "CYCLE": "年度次",
          "SURVEY_DATE": 0,
          "OPEN_DATE": "2026-02-20",
          "SMALL_AREA": 0,
          "COLLECT_AREA": "都道府県",
          "MAIN_CATEGORY": {
            "@code": "99",
            "$": "その他"
          },
          "SUB_CATEGORY": {
            "@code": "99",
            "$": "その他"
          },
          "OVERALL_TOTAL_NUMBER": 550080,
          "UPDATED_DATE": "2026-02-20",
          "STATISTICS_NAME_SPEC": {
            "TABULATION_CATEGORY": "都道府県データ",
            "TABULATION_SUB_CATEGORY1": "基礎データ"
          },
          "DESCRIPTION": {
            "TABULATION_CATEGORY_EXPLANATION": "社会・人口統計体系の都道府県ごとに集計したデータを提供します。"
          },
          "TITLE_SPEC": {
            "TABLE_NAME": "Ａ　人口・世帯"
          }
        },
        {
          "@id": "0000010102",
          "STAT_NAME": {
            "@code": "00200502",
            "$": "社会・人口統計体系"
          },
          "GOV_ORG": {
            "@code": "00200",
            "$": "総務省"
          },
          "STATISTICS_NAME": "都道府県データ 基礎データ",
          "TITLE": {
            "@no": "0000010102",
            "$": "Ｂ　自然環境"
          },
          "CYCLE": "年度次",
          "SURVEY_DATE": 0,
          "OPEN_DATE": "2026-02-20",
          "SMALL_AREA": 0,
          "COLLECT_AREA": "全国",
          "MAIN_CATEGORY": {
            "@code": "99",
            "$": "その他"
          },
          "SUB_CATEGORY": {
            "@code": "99",
            "$": "その他"
          },
          "OVERALL_TOTAL_NUMBER": 66576,
          "UPDATED_DATE": "2026-02-20",
          "STATISTICS_NAME_SPEC": {
            "TABULATION_CATEGORY": "都道府県データ",
            "TABULATION_SUB_CATEGORY1": "基礎データ"
          },
          "DESCRIPTION": {
            "TABULATION_CATEGORY_EXPLANATION": "社会・人口統計体系の都道府県ごとに集計したデータを提供します。"
          },
          "TITLE_SPEC": {
            "TABLE_NAME": "Ｂ　自然環境"
          }
        }
      ]
    }
  }
}
```

重要なところ:

- @id: 統計表ID
- TITLE.$, TITLE_SPEC.TABLE_NAME: 統計表名 (どっちがどっちかよくわからんので現物を見ること)
- OVERALL_TOTAL_NUMBER: レコード数
- UPDATED_DATE: 更新日 (比較的信用できる・・・はず)

## その他注意事項

- 政府統計によっては、統計表ID(`@id`)で一意にならないので注意すること
  - 確かどうでもいいところで重複していて、本当に意味のない重複だった記憶がある

## 推奨事項

`estat-file-search-knowledge.md` に同じ

## skillsの想定ワークフロー

ユーザーニーズ:

- ○○の統計表がe-StatでAPIで提供されてないか探してほしい
- estat-file-search で見つからなかった場合や、APIがありそうなことが判明したとき

skillsのIO:

上記ユーザーニーズをTrigger/INPUTとして、
ユーザーが探しているものに近しい統計表IDおよびそれに紐づく統計表ID、統計表名、政府統計などの一覧を提供する（もしくは該当のものがなさそうであることを返す）

要望があればデータ取得を実行しても良いが、それはこのskillのスコープ外とする。

(`getstatsData` や `getMetaInfo` などのエンドポイントを叩けばよい 別skillsにする)

## reference

- [e-Stat API Swagger UI](https://api.e-stat.go.jp/swagger-ui/e-statapi3.0.html)
