# TABITO 共通テスト中国語 Q4 生成タスク v0.4.1

旅人教育の内部教研用に、2026大学入学共通テスト中国語 第4問を蓝本とした**原创候補問題**を作成する。

## 最重要ルール

2026本試験・追試験は「能力の参考」ではなく、**現在のQ4の実際の型**である。

以前の失敗は、換皮を避けるために2026のsurface grammarまで捨て、一般的な「多資料読解」にしてしまったことだった。今回は逆に、**題材・文章・数値・固有名詞・正誤関係は原创にしつつ、設問骨格・資料接続・選択肢言語は選択した2026 familyに十分近づける。**

full Q4 の `surface_family` は必ず次のどちらか：

- `main_2026`：2026本試型
- `makeup_2026`：2026追試型

`Item Spec` に指定された family を厳守する。

## 共通A（21〜28）

### A 問1 — 21・22
- 中国語の会話文
- 内容一致を7〜8程度の**日本語選択肢**から二つ選ぶ
- テーマ・論点・登場人物の立場を導入する

### A 問2 — 23〜26
- 調査・資料読解の4枠
- 表、グラフ、説明文＋図などを使う
- `main_2026`：2枠 + 1枠 + 1枠
- `makeup_2026`：2枠 + 2枠
- 本試の表/グラフ型では**中国語選択肢中心**
- 追試のグラフ型は中国語選択肢、説明文＋図の統合型は日本語選択肢も可
- 四つの独立単選問題に分解しない

### A 問3 — 27・28
- 講演内容、説明のまとめ、構造化memo等のまとまりある中国語資料
- 6〜8程度の**日本語選択肢**から二つ選ぶ

## B：family別

### `main_2026`
- 問1 29・30：中国語 checklist / 条件資料を読み、**日本語選択肢**から二つ選ぶ
- 問2 31・32：中国語 profile / candidate と中国語の希望・条件を照合し、対象名・記号等の短い選択肢から選ぶ
- 問2 33：照合過程から追加すべき情報項目等を**日本語選択肢**から一つ選ぶ
- 問3 34：中国語 flowchart / rule tree / process を読み、一般原則を**中国語選択肢**から一つ選ぶ
- 問3 35・36：中国語の二つのcaseを、A/B/C/D等の短い分類・結果選択肢へ適用する

### `makeup_2026`
- 問1 29・30：SNS / timetable / 日付 / 曜日 / 条件等を組み合わせ、日付・時刻等の**日本語選択肢**から二つ選ぶ
- 問2 31・32：map / memo / system diagram等の複合資料を読み、**日本語選択肢**中心に二つ選ぶ
- 問2 33・34：flyer / instructions / safety notice 等を読み、**日本語選択肢**中心に二つ選ぶ
- 問3 35・36：中国語reflection / summary / opinion textから、**日本語選択肢**で二つ選ぶ

## 原创性の境界

**再現してよい／むしろ再現すべきもの**：
- A/B、21〜36、A=8枠/B=8枠
- 上記の問1/問2/問3の役割
- 「二つ選べ」が多いこと
- taskごとの日本語/中国語選択肢の分布
- 本試型/追試型の資料→設問の接続方法

**必ず原创にするもの**：
- テーマと具体的場面
- 登場人物・施設名
- 中国語本文
- 数値と図表データ
- 選択肢の具体的内容
- 正答を決める具体的論理関係
- case内容

**禁止**：
- ペットを別の動物や別の商品に置き換えただけ
- 自動運転を別の交通サービスに置き換えただけ
- 公式の文・選択肢・数値・caseを軽く言い換える
- 「原创」を優先しすぎて2026 Q4の型から離れる
- 全選択肢を機械的に中国語または日本語へ統一する

## 文体・設問

- 中国語は自然な現代簡体字。
- 日本語設問は大学入試センター冊子に置いて違和感のない簡潔な試験文体。
- option language は上記family/task grammarに従う。
- 語注は必要最小限。
- 1つの資料を細切れカードにしすぎない。共通テストらしい情報密度を保つ。
- visualは位置・経路・因果・階層・手順など、視覚化する意味がある場合に使う。
- 正答集合は一意。誤答肢には部分一致、条件見落とし、因果逆転、範囲誤読などの自然な誤読経路を持たせる。

## Blueprint

{{ blueprint_yaml }}

## 2026 Q4 Generation Profile

{{ generation_profile_yaml }}

## 2026 Q4 Surface Grammar

{{ surface_grammar }}

## Q4 Template

{{ template_yaml }}

## Detailed Item-Writing Direction

{{ item_writing_direction }}

## Item Spec

{{ item_spec_json }}

## JSON設計

- `schema_version`: `"0.2"`
- `workflow.blueprint_version`: `"R8-2026-main-tsui-v3"`
- fullの場合は `surface_family` を `main_2026` / `makeup_2026` のどちらかにする
- fullでは answer_number 21〜36を一度ずつ使用
- materials と tasks は subsection(A/B) と order を持つ
- task.response_mode: `single_choice` / `multi_select` / `multi_slot_choice`
- `dependency_mode` を明示
- evidence locator を人間が確認できる粒度で記述
- single_choice / multi_select は正答以外の全選択肢について `distractor_rationales_ja`
- multi_slot_choice は各slotの `slot_distractor_rationales_ja`
- `quality_notes.ambiguity_risk` は原則 low

出力前に必ず確認：

1. 21〜28は「会話2 → 調査資料4 → 講演/memo2」になっているか。
2. 29〜36は指定familyのB構造に一致するか。
3. 各taskのoption languageが2026 familyの使い分けに合うか。
4. 本文やcaseの換皮ではなく内容は原创か。
5. 逆に原创性を意識しすぎて一般的なworksheetになっていないか。
6. 資料・選択肢の情報密度が共通テスト冊子に近いか。
7. 正答が一意か。

**JSON以外を出力しない。**
