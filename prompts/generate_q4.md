# TABITO 共通テスト中国語 Q4 生成タスク v0.5

2026大学入学共通テスト中国語 第4問の**原创候補問題**を作成する。

目的は「多資料っぽい問題」を作ることではない。指定された2026 familyの学生向け構造を保ちながら、題材・文章・数値・人物・具体的な判断ロジックを新規設計し、共通テストらしい情報処理を成立させることである。

## 規則の優先順位

以下の入力に重複がある場合、勝手に平均しない。優先順位は固定する。

1. **Item Spec** — 今回のID、family、scope、topic等
2. **Production Profile** — 命題上の authoritative contract。hard core、family scaffold、情報依存、品質条件
3. **Reference Patterns** — 2026本試・追試から観察した task role / option language / variation の具体像。例を新しい必須ルールへ膨張させない
4. **Output Template** — JSONフィールドと表現可能な資料・taskの形

このprompt本文は作業手順だけを与える。上記入力に既に書かれたslot構造をここで再定義しない。

## 作成手順

### 1. 先に大問の情報設計を作る

本文を書き始める前に、内部的に次を決める。

- AからBまで一つの目的・活動として自然につながるscenario
- 各answer slotが何を判断させるか
- 各資料がどの設問に必要か
- 直接理解 / 比較 / 検証 / 条件照合 / 適用等が単調に反復しないか

題材だけ共通で、設問同士が独立したworksheetにはしない。

### 2. 情報依存を設計してから選択肢を書く

`cross_source` は飾りのmetadataではない。

- 一つの資料だけを残しても正答が一意なら `cross_source` と呼ばない
- 本当に複数資料を使わせる設問では、各資料単独では候補が複数残り、組み合わせて初めて決まるようにする
- 誤答肢は、一資料だけならもっともらしいが別資料との照合で落ちる near-miss を優先する
- visual / table / chart / flow は、その関係を視覚化する意味があるときだけ使う

すべての設問を無理にcross-source化しない。single-sourceの自然な理解問題も残す。

### 3. 誤答肢に「誤読経路」を持たせる

正答以外を単なるデタラメにしない。

- 条件の一部だけ満たす
- 数値・範囲・主体・時点を一箇所ずらす
- 一資料の事実は正しいが結論が違う
- 因果や必要条件を逆にする

一語だけ、常識だけ、選択肢の長さだけで正答できるshortcutを避ける。

### 4. 冊子として自然に書く

- 中国語は自然な現代簡体字。HSK穴埋め教材や母語者向け圧縮ニュースの文体にしない
- 日本語の導入・設問は短い試験文体にする。解き方を説明するAI文体にしない
- `subsection_intros_ja.A/B` はfull Q4で必須。誰が何のために読むかを示すが、答えや読み方を先に教えない
- Bの導入はAの言い換えではなく、情報の用途・局面が変わることを自然に示す
- 資料を短いカードへ細切れにしすぎず、共通テスト冊子らしい情報密度を保つ
- 数量資料は重い計算ではなく、比較・割合・増減・条件判断を測る
- 題材上必要な低頻度語だけ最小限にglossする

### 5. 原创性は内容と論理で作る

公式問題から再現してよいのは、選択した2026 familyのstudent-facing grammarである。

必ず新規にするもの：
- scenarioの具体内容
- 人物・施設名
- 全中国語本文
- 数値・図表データ
- case
- 選択肢文
- 正答を決める具体的論理

名詞だけ差し替えたreskin、公式文章の軽い言換えは禁止。

## 出力前の内部チェック

JSONを返す前に、少なくとも次を内部で検証する。

1. 指定familyのslot/task scaffoldから外れていないか
2. A/B導入とscenario progressionが自然か
3. 正答または正答集合が資料だけから一意か
4. `cross_source` と宣言した各taskがsingle-source ablationを通るか
5. visual materialが装飾になっていないか
6. distractorが局所的にもっともらしく、keyword shortcutがないか
7. 直接理解ばかり、同じ認知操作ばかりになっていないか
8. option languageがReference Patternsのtask roleに合うか
9. 内容・数値・case・判断ロジックが原创か
10. 全体が細切れworksheetではなく一つのDNC Q4として読めるか

## Production Profile — authoritative authoring contract

{{ generation_profile_yaml }}

## 2026 Reference Patterns — family-specific observed surface

{{ reference_patterns_yaml }}

## Output Template

{{ template_yaml }}

## Item Spec — highest priority for this run

{{ item_spec_json }}

## Output contract

- JSONのみ。Markdown fenceや説明文は禁止
- `schema_version`: `"0.2"`
- `workflow.blueprint_version`: `"R8-2026-main-tsui-v4"`
- fullでは `subsection_intros_ja.A/B` を含める
- `dependency_mode` と、人間が追える粒度の `evidence` を各taskに記録する
- single-choice / multi-select の全誤答肢に `distractor_rationales_ja` を付ける
- multi-slot choice は各slotの誤答理由を `slot_distractor_rationales_ja` に記録する
- `quality_notes.ambiguity_risk` は原則 `low`
