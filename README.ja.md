# アンティキティラ島の機械：実際に動作する検証済み3D復元モデル

[English](README.md) · [Français](README.fr.md) · [Español](README.es.md) · [Deutsch](README.de.md) · [Italiano](README.it.md) · [Português](README.pt.md) · [Ελληνικά](README.el.md) · [中文](README.zh.md) · **日本語**

![復元された機械、斜め前方からの眺め](docs/images/front34.jpg)

アンティキティラ島の機械は、紀元前2世紀または紀元前1世紀にギリシアで作られた手回しクランク式の青銅製天文計算機で、1901年に沈没船から引き揚げられました。知られている中で最古の複雑な歯車機械です。このリポジトリには、**Blender 5.2** で制作したその完全な3D復元モデルが収められています。

- **69枚の歯車**すべてが、実物どおりの歯数を持っています。
- 歯は共役なインボリュート歯形なので、すべての歯車対が正しく噛み合い、実際に動作します。
- すべての歯車列について、それが表す天文周期と**厳密な分数で照合**しています。
- 可動範囲全体にわたって、部品同士の**干渉（衝突）チェック**を行っています。

ビルド全体は、それ単体で完結した1つのマスタープロンプト（[`PROMPT_OPUS.md`](PROMPT_OPUS.md)）から Claude Opus 5.5 が1回のパスで生成し、その後、独立に検証しました。

## 主な特徴

- **69枚の歯車**。確実性の度合いによって分類しています。
  - 30枚は**現存**：断片の中に物理的に残っているもの（CTスキャン）。
  - 7枚は**復元**：有力な証拠に基づくもの。
  - 32枚は**仮説**：Freeth et al. 2021 のモデルに基づくもの。

  状態ごとに専用の Blender コレクションがあるため、グループ単位で表示・非表示を切り替えられます。
- **厳密な数学。** 主歯車 b1 の1回転が1年に相当します。この機構の**自由度はちょうど1**（クランク）で、22個の目標値すべてが分数として厳密に一致します（以下は抜粋）。

  | 出力 | 厳密な回転速度（回転/年） | 周期 |
  |---|---|---|
  | 月（平均運動） | 254/19 | 19年間に254恒星月 |
  | メトン周期ダイヤル | −5/19 | 5回転 = 19年 = 235朔望月 |
  | サロス周期ダイヤル | −940/4237 | 4回転 = 223朔望月 |
  | 月の交点（竜の針） | −5/93 | 18.6年、逆回転 |
  | 金星 | b1 に対して 289/462 | 462年間に289会合周期 |
- **機械として実際に動作します。**
  - 中心距離は 10⁻⁶ mm の精度で厳密であり、すべての噛み合い率は ≥ 1.2 です。
  - 数千回の3D（BVH）サンプリングで**相互貫入は 0** でした。対象は、1歯ピッチにわたるすべての噛み合い、ピン・スロット機構のすべてのサイクル、そして240通りのクランク位置における168組の部品ペアです。
- **月は楕円歯車ではなく、円形の歯車で加速・減速します。** 回転する e3 ターンテーブル上のピン・スロット機構が、ヒッパルコスの月の不等（±6.58°）を再現します。
- **惑星は正しいタイミングで逆行します。** 火星・木星・土星は衝（180° ± 0.03°）で逆行し、水星と金星は最大離角の範囲内にとどまります。
- **1つのクランクですべてを駆動します。** すべての運動は年単位の `AM_Controller["crank"]` から単純式ドライバーを介して生成されるため、Python スクリプトを有効にしなくてもアニメーションが動作します。
- **見やすい表示。** 古代の7つの「惑星」（太陽、月、水星、金星、火星、木星、土星）には、それぞれ固有の色と、天体に追従するラベルが付いており、凡例も用意されています。
- **博物館風のライティング。** シーンには暗いサイクロラマ背景と暖色のソフトボックスが配置され、AgX カラーでレンダリングしています。このセットアップは、並べてレンダリングした3案の中から選びました。
- **分解図。** `AM_Controller["explode"]` を 0 から 1 に動かすと、すべての部品が積層軸に沿ってスライドします。
- **3Dプリント。** 部品ごとの STL と全体の 3MF を、レジン ×1、レジン ×1.5、FDM ×2 の3種類のプロファイルで用意しています。

| 前面ダイヤル | 背面ダイヤル |
|---|---|
| ![色分けされラベルの付いた惑星を表示する前面ダイヤル](docs/images/front.jpg) | ![メトン周期とサロス周期の螺旋](docs/images/back.jpg) |

| 分解図 | 内部（開いた状態） |
|---|---|
| ![分解図の静止画](docs/images/exploded.jpg) | ![分解動画の1フレーム](docs/images/exploded_video_frame.jpg) |

## 動画

- [`antikythera.mp4`](build/out/renders/antikythera.mp4)：20 s。クランクが4年分回転し、惑星、月、背面ダイヤルがすべて動きます。
- [`antikythera_eclate.mp4`](build/out/renders/antikythera_eclate.mp4)：15 s の分解図動画。歯車が回り続けたまま機構が一層ずつ開き、その後ふたたび閉じます。

動画の中で惑星がときどき**逆向き**に動くのはバグではありません。これは地球から見た**逆行運動**であり、この機構はそれを示すために作られています。竜の針（月の交点）は常に逆向きに回転します。

## クイックスタート

1. **Blender 5.2** 以降をインストールします。
2. [`build/out/am.blend`](build/out/am.blend) を開き、**Space** キーを押してアニメーションを再生します。
3. `AM_Controller` を選択し、カスタムプロパティを変更します。
   - `crank`：年数。1 で b1 が1回転します。
   - `explode`：0 から 1。
   - `patina`：0 は新品の青銅、1 は博物館収蔵品のような緑青。
4. アウトライナーでコレクションを非表示にします。
   - `AM_CASE` と `AM_DIALS`：歯車機構を見るため。
   - `AM_HYPOTHETICAL`：実証されている部分だけを残すため。
   - `AM_LABELS`：ラベルを消すため。
   - `AM_STAGE`：ライティングのセットを消すため。
5. 任意の部品をクリックすると、そのカスタムプロパティ `status`、`role`、`teeth`、`module`、`sources` を確認できます。

### 検証を再実行する

Blender に同梱されている Python を使用します。以下のパスは macOS 用です。他のシステムでは適宜読み替えてください。

```sh
PY=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
BL=/Applications/Blender.app/Contents/MacOS/Blender

$PY tools/validate_spec.py          # exact linear solve (1 DOF, 22 targets), centre distances, collision screening
$PY tools/check_kinematics.py       # pin-and-slot laws, followers, elongations, retrogrades, solar apogee
cd build && $PY -m unittest discover -s tests && $PY -m am.verify --stage all && cd ..
$BL -b build/out/am.blend --python-exit-code 1 -P tools/crosscheck_blend.py   # Blender rotations vs an independent solver
```

[`build/README.md`](build/README.md) には、ビルド、チェック、エクスポート、レンダリングのすべてのステップが、1ステップにつき1コマンドで記載されています。

### マスタープロンプトからすべてを再構築する

**空の**フォルダーで、[Claude Code](https://claude.com/claude-code) を使って次を実行します。

```sh
claude -p --model 'claude-opus-5-5[1m]' --effort xhigh --permission-mode acceptEdits \
  --allowedTools Bash Read Write Edit Glob Grep < PROMPT_OPUS.md
```

- [`prompts/PROMPT_OPUS_v1_validated.md`](prompts/PROMPT_OPUS_v1_validated.md) は、このビルドを1回のパス（89 min）で生成した、まさにそのバージョンです。
- [`PROMPT_OPUS.md`](PROMPT_OPUS.md) は v1.2 です。惑星の色とラベル、博物館風の演出、分解スライダー、分解図動画が追加されています。これらはすべて後から `tools/` 内のスクリプトでこのビルドに加えたもので、v1.2 はまだゼロからの再実行を行っていません。

## 制作の過程

1. **調査。** 複数のエージェントが並行して一次資料を読みました。Freeth et al. 2006、2008、2021（補足情報を含む）、Price 1974、Budiselic et al. 2020、Woan & Bayley 2024、Anastasiou et al. 2014 などです。結果は1つのデータセットに統合され、その後、懐疑役のエージェントによってチェックされました。
2. **仕様。** [`spec/antikythera.json`](spec/antikythera.json) が唯一の信頼できる情報源（single source of truth）です。すべての歯車の歯数、モジュール、軸位置、z 範囲、軸穴径、そしてすべてのシャフト、スタッド、ボス、ピン、ダイヤル、材質を定義しています。このファイルは `tools/make_spec.py` によって生成され、公表データに含まれる22件の幾何学的に不可能な点を修正しています（たとえば、公表された距離では b2 が c1 と l1 の両方と噛み合うことはできません）。すべての中心距離は厳密に解かれています。
3. **独立したチェック。** `tools/validate_spec.py` と `tools/check_kinematics.py` は生成スクリプトとコードを一切共有しておらず、ミューテーションテストによって、意図的に注入したエラーを検出できることが確認されています。
4. **包絡線によるクラウン歯。** `tools/crown_envelope.py` は、a1 と q1 のコントレート歯（冠歯車の歯）を、相手側の歯が一度も掃過しない領域として算出します。その後、`tools/test_crowns_blender.py` が Blender 内で BVH を用いてそれらをチェックします。
5. **敵対的レビュー。** 独立したレビュアーによる2ラウンドのレビューで、データ、実際に動かして検証した Blender API、実行可能性、幾何形状を精査し、5件のブロッカーと約60件のその他の問題を発見しました。これらはすべて修正済みです。
6. **ワンパスビルド**：新しい Opus 5.5 セッションが、プロンプトだけを頼りに実行しました。131ターン、約5,000行のコードで、すべての受け入れ基準がグリーンになりました。
7. **独立検証**：結果に対して、テスト、厳密なチェック、完全な BVH チェック、そして `am.blend` 内のすべての物体を独立したソルバーと照合するクロスチェック（7·10⁻⁷ rad）を実施しました。

## リポジトリ構成

```
PROMPT_OPUS.md            master prompt (v1.2), self-contained; embeds the full JSON spec + SHA-256
prompts/                  the prompt version validated by the one-pass build (v1)
spec/antikythera.json     single source of truth (gears, axes, shafts, trains, dials, staging, video)
research/                 raw multi-agent research results with source URLs
tools/                    spec generator, validators, crown envelopes, annotation/staging/explode/render scripts
build/                    the project generated by the one-pass build (am/, blender_scripts/, tests/, README)
build/out/                am.blend, verification report (report.md/html), checks, print files, renders, videos
docs/                     dossier (HTML) and images
```

## 率直に認める限界

- 惑星の歯車列、月の交点、真太陽は、Freeth et al. 2021 の**仮説的な**モデルに従っています。アニメーションが動作するからといって、原機がどのように作られていたかが証明されるわけではありません。
- 一部の数量は公表されていません。それらについて仕様では文書化されたデフォルト値を用いており、`spec/antikythera.json` → `unresolved_defaults` に列挙しています。
  - 背面板上の軸の角度。
  - コスモス表示リングの半径。
  - 初期位相（元期は未較正）。
- 歯は共役インボリュート歯形（30° の基準ラック。これは古代の正三角形の歯に相当します）であり、原機の手やすりで仕上げた三角形の歯ではありません。
- 惑星の色は見やすさのためだけのもので、史実に基づくものではありません。

## 主な出典

- T. Freeth et al., "A Model of the Cosmos in the ancient Greek Antikythera Mechanism", *Scientific Reports* 11, 5821 (2021)、およびその補足情報（Supplementary Information）。
- T. Freeth et al., "Decoding the ancient Greek astronomical calculator known as the Antikythera Mechanism", *Nature* 444, 587 (2006).
- T. Freeth, A. Jones, J. Steele, Y. Bitsakis, "Calendars with Olympiad display and eclipse prediction on the Antikythera Mechanism", *Nature* 454, 614 (2008).
- T. Freeth & A. Jones, "The Cosmos in the Antikythera Mechanism", ISAW Papers 4 (2012).
- D. de Solla Price, *Gears from the Greeks* (1974).
- C. Budiselic et al. (2020); G. Woan & J. Bayley (2024)：カレンダーリングの穴の数。
- M. Anastasiou et al. (2014)：背面ダイヤルの螺旋。

URL付きの完全なリストは `spec/antikythera.json` → `sources` にあります。

## ライセンス

- **コード**：MIT（[`LICENSE`](LICENSE)）。
- **レンダリング画像、動画、3Dモデル、プリント用ファイル、テキスト**：CC BY 4.0（[`LICENSE-MEDIA.md`](LICENSE-MEDIA.md)）。
- **学術データ**：上記の文献を引用してください。

---

taciclei のために [Claude Code](https://claude.com/claude-code)（Claude Opus 5 / 5.5）で作成しました。
