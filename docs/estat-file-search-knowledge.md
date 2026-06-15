# estat-file-search knowledge dump

## このskillで実現したい私がやってるワークフロー

### 前提:

e-Statの検索性は非常に悪い。階層を行き来しながら、目当てのものを探す必要がある。

階層とは、政府統計コード・データセット一覧またはデータセット・データセットまたは統計表(・配布形式）の基本的には3層の親子関係になっている。
ちなみに、名称や英名、変数名は一貫性がなくコロコロ変わる。この3層の概念と、最上位の政府統計コードは多くの場合不変であることに留意する。

### 探すための基本的な考え方:

政府統計コードを探す ⇄ 適当なキーワードで検索してHitした統計表の親を調べる

上記のようなイテレーションが基本となる。
政府統計コードは強力なフィルターなので是非とも特定しておきたい。
最初から自分が欲しい政府統計コードがわかってれば話は早いが、ほとんどの政府統計コードについて中身が初見ではわからないのがジレンマである。
そこで、自分の欲しい統計表がありそうな政府統計名称を探して掘っていくトップダウン的なアプローチと、適当なキーワードで検索して出てきた統計表の親をたどるボトムアップ的なアプローチの
両方でイテレーションしながら、最終的に自分が欲しい統計表がどの政府統計に収納されているのか（もしくはそんなものはないのか）を確定させていく必要がある。

なお、政府統計名ないし所管省庁名はコロコロ変わるので、政府統計コードの特定を推奨する。

政府統計コードと欲しいと情報が格納されている統計表IDがわかれば仕事の99%は完了している。

### 何か欲しい統計があるときの例

e.g. 保育施設の数や施設ごとの保育士の数に関する統計を調べたい

1. 「保育士」で検索 -> 政府統計: 「社会福祉施設調査」の配下の統計表が上位にヒットする
2. 政府統計: 「社会福祉施設調査」に紐づく統計表一覧を取得 -> 令和5年の調査の閲覧表の施設表（実際は階層になっていないのでわかりづらいが）の中にある統計表には施設数や保育士数がありそう
  3. ただし令和6年調査にはないということもわかる（調査自体はあるが形式が変わったのか？調査が行われなくなったのか？）
4. 令和5年のデータならありそう、ということで必要な題名の統計表の統計表IDを確認(web UIだとわからないが、APIだと取得できる)
  5. 必要なら年度間で同じ統計表があるか、などを継続調査する
5. 統計表IDからExcelやcsvのダウンロードURLを叩いてファイル取得

## ファイル検索APIについて

ファイル検索をするときは`https://api.e-stat.go.jp/rest/3.0/app/json/getDataCatalog` のエンドポイントを使う。

e.g. 政府統計: 社会福祉施設調査 の配下の統計表一覧を取得する例

```bash
curl -X 'GET' \
  'https://api.e-stat.go.jp/rest/3.0/app/json/getDataCatalog?appId={E_STAT_APP_ID}&statsCode=00450041&limit=10' \
  -H 'accept: application/json'
```

### APIパラメータ

前提: https://api.e-stat.go.jp/swagger-ui/e-statapi3.0.html#/%E3%83%87%E3%83%BC%E3%82%BF%E3%82%AB%E3%82%BF%E3%83%AD%E3%82%B0%E6%83%85%E5%A0%B1%E5%8F%96%E5%BE%97/get-rest-json-dataCatalog を参考にすること

| カテゴリ | パラメータ名 | 型 | 必須 | 内容・仕様 | 備考・Tips |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **認証・基本** | **appId** | string | **○** | アプリケーションID | URLに書かれるくらいなので秘匿性はそこまででもない |
| | **lang** | string | - | 取得言語（J：日本語 / E：英語）省略時は「J」 | 基本全部無指定で日本語でよい |
| **時間軸** | **surveyYears** | string | - | 調査年月（yyyy / yyyymm / yyyymm-yyyymm） | 中身が多種多様すぎるのでほぼ使わない |
| | **openYears** | string | - | 公開年月（yyyy / yyyymm / yyyymm-yyyymm） | 嘘ついてる統計もあるのでここも意味ない 使わない |
| | **updatedDate** | string | - | 更新日付（yyyy / yyyymm / yyyymmdd / 範囲） | 同上 疑いながら使うくらい |
| **分類・地域** | **statsField** | string | - | 統計分野（2桁：大分類 / 4桁：小分類）例：「03」労働・賃金、「0201」人口 | これも気にしなくてよい nullだと思え |
| | **statsCode** | string | - | 政府統計コード（5桁：作成機関 / 8桁：統計コード） 例：「00200521」国勢調査 | 重要 ここは押さえる |
| | **collectArea** | string | - | 集計地域区分（1:全国 / 2:都道府県 / 3:市区町村） | 意味なし |
| **カタログ** | **catalogId** | string | - | カタログID | 意味なし謎 |
| | **resourceId** | string | - | カタログリソースID | 意味なし 忘れてよし |
| **検索・形式** | **dataType** | string | - | ファイル形式（XLS, CSV, PDF, XML, XLS_REP, DB） カンマ区切りで複数指定可。省略時は全指定扱い | ここは70%くらい信用できるファイル検索の時は DB以外を列挙すると良い（が、疑うくらいなら無指定で後続の処理でフィルターするくらいで良い） |
| | **searchWord** | string | - | 検索キーワード（AND, OR, NOT検索対応）例：「東京 AND 人口」 | 政府統計コードと同じく重要 キーワード検索の重要なパラメータ |
| **取得制御** | **startPosition** | string | - | データ取得開始位置（1からの行番号） | 継続取得時は前回の <NEXT_KEY> を指定 |
| | **limit** | string | - | データ取得件数（省略時は10万件） | この10万件は嘘で確か100までしか指定できないので注意 |
| | **explanationGetFlg** | string | - | 解説情報有無（Y：取得 / N：取得しない）省略時は「Y」 | 基本は無指定でYでよい |
| | **callback** | string | - | コールバック関数名 JSONP形式を利用する場合に必須 | 忘れてよし |

基本的には、`statsCode`, `searchWord` のみを使う想定でよい。

### Resopnse

Header sample

```
access-control-allow-origin: * 
cache-control: no-store 
content-encoding: gzip 
content-type: application/json; charset=utf-8 
date: Fri,24 Apr 2026 14:22:35 GMT 
server: ZENEDGE 
strict-transport-security: max-age=0 
vary: Accept-Encoding 
x-cache-status: NOTCACHED 
x-cdn: Served-By-Zenedge 
x-content-type-options: nosniff 
x-frame-options: SAMEORIGIN 
x-xss-protection: 1; mode=block 
x-zen-fury: 2a00785df36e7c279d1f10c7f11a8c06bcdafca3
```

Response sample:

`GET_DATA_CATALOG.DATA_CATALOG_LIST_INF.DATA_CATALOG_INF`を見ればよい。

Swagger UIや仕様書に型定義があるがゆるふわでほぼ信用ならない(descriptionとかstrだったりstructだったり)ので基本的に現物をしっかり確認する。

```
{
  "GET_DATA_CATALOG": {
    "RESULT": {
      "STATUS": 0,
      "ERROR_MSG": "正常に終了しました。",
      "DATE": "2023-01-04T02:30:56.291+09:00"
    },
    "PARAMETER": {
      "LANG": "J",
      "SURVEY_YEARS": 2016,
      "OPEN_YEARS": 2019,
      "STATS_FIELD": "03",
      "STATS_CODE": "00450071",
      "COLLECT_AREA": 1,
      "EXPLANATION_GET_FLG": "Y",
      "DATA_TYPE": "XLS",
      "CATALOG_ID": "000001255613",
      "RESOURCE_ID": "000008508466",
      "DATA_FORMAT": "J",
      "START_POSITION": 1,
      "LIMIT": 2,
      "UPDATED_DATE": 2019
    },
    "DATA_CATALOG_LIST_INF": {
      "NUMBER": 1,
      "RESULT_INF": {
        "FROM_NUMBER": 1,
        "TO_NUMBER": 1
      },
      "DATA_CATALOG_INF": {
        "@id": "000001255613",
        "DATASET": {
          "STAT_NAME": {
            "@code": "00450071",
            "$": "毎月勤労統計調査"
          },
          "ORGANIZATION": {
            "@code": "00450",
            "$": "厚生労働省"
          },
          "TITLE": {
            "NAME": "毎月勤労統計調査　全国調査_夏季賞与_年次_2016年",
            "TABULATION_CATEGORY": "毎月勤労統計調査　全国調査",
            "TABULATION_SUB_CATEGORY1": "夏季賞与",
            "TABULATION_SUB_CATEGORY2": "",
            "TABULATION_SUB_CATEGORY3": "",
            "TABULATION_SUB_CATEGORY4": "",
            "TABULATION_SUB_CATEGORY5": "",
            "CYCLE": "年次",
            "SURVEY_DATE": 2016,
            "COLLECT_AREA": "全国"
          },
          "DESCRIPTION": "",
          "PUBLISHER": "厚生労働省",
          "CONTACT_POINT": "雇用・賃金福祉統計室",
          "CREATOR": "雇用・賃金福祉統計室",
          "RELEASE_DATE": "2019-11-08",
          "LAST_MODIFIED_DATE": "2019-11-08",
          "FREQUENCY_OF_UPDATE": "年次",
          "LANDING_PAGE": "https://www.e-stat.go.jp/stat-search/files?layout=datalist&toukei=00450071&tstat=000001011791&cycle=7&year=20160&month=0&tclass1=000001015911"
        },
        "RESOURCES": {
          "RESOURCE": {
            "@id": "000008508466",
            "TITLE": {
              "NAME": "1_事業所規模５人以上の結果",
              "TABLE_CATEGORY": "",
              "TABLE_NO": 1,
              "TABLE_NAME": "事業所規模５人以上の結果",
              "TABLE_EXPLANATION": "",
              "TABLE_SUB_CATEGORY1": "",
              "TABLE_SUB_CATEGORY2": "",
              "TABLE_SUB_CATEGORY3": ""
            },
            "URL": "https://www.e-stat.go.jp/stat-search/file-download?&statInfId=000031819388&fileKind=0",
            "DESCRIPTION": "",
            "FORMAT": "XLS",
            "RELEASE_DATE": "2019-09-20",
            "LAST_MODIFIED_DATE": "2019-09-20",
            "RESOURCE_LICENCE_ID": "Government of Japan Standard Terms of Use",
            "LANGUAGE": "J"
          }
        }
      }
    }
  }
}
```

重要なところ:

- DATASET.STAT_NAME: 政府統計コードと政府統計名がある
- DATASET.TITLE: 統計表を束ねたデータセット（またはWebUI上ではデータセット一覧）という概念の名称 | 大抵は該当年度の調査をまとめたものである
- RESOURCES: list形式で統計表の一覧が収納されている
- RESOURCES.RESOURCE.@id: 統計表ID とにかくこれを特定させたい重要な概念
- RESOURCES.RESOURCE.FORMAT: ファイル形式
- RESOURCES.RESOURCE.URL: ダウンロードURL 実体はこのURL叩いて取得する

## その他注意事項

- 信用できる部分は少ないので、普遍性に対して過信しないこと  現物を確認すること
- Webを検索しても大した情報は出てこないし、公式の仕様も嘘ついてたりするので期待しないこと
- この文章中のノウハウは私が血の汗を流しながら解読していったものなのでかなり高いレベルで信頼できる
- `LAST_MODIFIED_DATE`などは一見するとシステム的なカラムで嘘付きようがないのではないかと思われるかもしれないが、なんと「人  間  が  手  作  業  で  入  れ  て  い  る  フ  シ  が  あ  る」
- `getDataCatalog`のエンドポイントは一見すべての統計表を検索できるように見えるが、実はAPIしか提供されていない（つまり同じデータセット内で、format:DBしかないもの）政府統計はごっそり抜けている。 APIでデータが提供されている統計表(社会人口統計体系などの加工統計)は別のエンドポイント `getStatsList`を使う。 （なんじゃそりゃ）
- 統計表名 (`RESOURCES.RESOURCE.TITLE`)には`  〃  ` のようなふざけた命名もある Webで見たときに同上であることを示すものだが、こういうのは検索でHitしづらいので注意する
- また統計表番号(`RESOURCES.RESOURCE.TITLE.TABLE_NO`)も一貫しているものとそうでないものがあるので傾向をよく見ること

## 推奨事項

- 政府統計コードについて
  - 毎回検索するのは大変なので最新の一覧を作成した `scripts/get_gov_stats_codes/gov_stats_codes.csv`
  - これをskillsの配下に配置して、参照するように
  - たまに更新されるので、定期的に更新するように開発者（私）に促すこと
- `getDataCatalog`のレスポンスは結構RESOURCESのリストが重い jqなどを使うよりかは、一度ローカルに保存した後に、jq (jaq/jsongrep でも),rgやduckdbなどで解析することを積極的に推奨する
  - 必要ツールや推奨ツールはREADMEに書いておく

## skillsの想定ワークフロー

ユーザーニーズ:

- ○○の統計表をe-Statにないか探してほしい
- ○○調査の調査票を探して欲しい （e.g. 地方公営企業決算状況調査の最新の調査表レイアウト（水道事業）を探してきて）
- （別skillsへの誘導） ○○の統計表についてAPIでデータが提供されてないか探して

skillsのIO:

上記ユーザーニーズをTrigger/INPUTとして、
ユーザーが探しているものに近しい統計表IDおよびそれに紐づく統計表名、政府統計、ファイル形式、ダウンロードURL、landing page URLなどの一覧を提供する（もしくは該当のものがなさそうであることを返す）
要望があればダウンロードを実行する

## reference

- [e-Stat API Swagger UI](https://api.e-stat.go.jp/swagger-ui/e-statapi3.0.html)
