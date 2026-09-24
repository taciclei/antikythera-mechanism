# 安提基特拉机械：一个可运转、经过验证的 3D 重建

[English](README.md) · [Français](README.fr.md) · [Español](README.es.md) · [Deutsch](README.de.md) · [Italiano](README.it.md) · [Português](README.pt.md) · [Ελληνικά](README.el.md) · **中文** · [日本語](README.ja.md)

![重建后的机械，正面四分之三视角](docs/images/front34.jpg)

https://github.com/user-attachments/assets/c810d3ee-ecfa-46e3-b11d-f919c3ae2cd9

https://github.com/user-attachments/assets/40b1f61b-5fb0-4b54-bd1c-1ba1f423a424


安提基特拉机械是一台手摇驱动的青铜天文计算器，于公元前 2 世纪或前 1 世纪在希腊制造，1901 年从一艘沉船中被打捞出水。它是已知最古老的复杂齿轮机械。本仓库包含它在 **Blender 5.2** 中的完整 3D 重建：

- 全部 **69 个齿轮**都采用真实齿数；
- 轮齿为共轭渐开线齿，因此每一对齿轮都能正确啮合、真正运转；
- 每条齿轮系都已对照其所模拟的天文周期**以精确分数进行核验**；
- 所有零件都已在整个运动范围内**经过碰撞检查**。

整个构建由 Claude Opus 5.5 根据一份自成一体的主提示词（[`PROMPT_OPUS.md`](PROMPT_OPUS.md)）一次性完成，随后经过独立验证。

## 亮点

- **69 个齿轮**，按确定程度分类标注：
  - 30 个**现存**齿轮，实物存在于残片之中（CT 扫描）；
  - 7 个**重建**齿轮，依据充分的证据；
  - 32 个**假设**齿轮，来自 Freeth et al. 2021 的模型。

  每种状态都有各自的 Blender 集合，因此每一组都可以单独隐藏或显示。
- **精确的数学**。主轮 b1 转 1 圈即为 1 年。该机械恰好只有**一个自由度**（曲柄），全部 22 个目标都以分数形式精确吻合（示例见下表）。

  | 输出 | 精确速率（圈/年） | 周期 |
  |---|---|---|
  | 月球（平均） | 254/19 | 19 年内 254 个恒星月 |
  | 默冬刻度盘 | −5/19 | 5 圈 = 19 年 = 235 个朔望月 |
  | 沙罗刻度盘 | −940/4237 | 4 圈 = 223 个朔望月 |
  | 月球交点（龙指针） | −5/93 | 18.6 年，反向转动 |
  | 金星 | 289/462（相对于 b1） | 462 年内 289 个会合周期 |
- **在机械上真正可运转**。
  - 中心距精确到 10⁻⁶ mm，所有重合度均 ≥ 1.2。
  - 在数千个 3D（BVH）采样中，**相互穿透为 0**：涵盖每一处啮合在一个齿距内的全过程、每个销槽机构的完整周期，以及 240 个曲柄位置下的 168 对零件。
- **月球的忽快忽慢由圆形齿轮实现**，而非椭圆齿轮。旋转的 e3 转盘上的一个销槽机构重现了喜帕恰斯的月球近点不等（±6.58°）。
- **行星在正确的时刻逆行**。火星、木星和土星在冲日时逆行（180° ± 0.03°），水星和金星则始终保持在各自的最大距角之内。
- **一个曲柄驱动一切**。所有运动都来自以年为单位的 `AM_Controller["crank"]`，经由简单表达式驱动器传递，因此无需启用 Python 脚本，文件即可播放动画。
- **清晰易读的显示**。古代七颗“行星”（太阳、月球、水星、金星、火星、木星、土星）各有专属颜色和一个随之移动的标签，并配有图例。
- **博物馆式布光**。场景采用深色无影墙背景和暖色柔光箱，并以 AgX 色彩渲染。这一布光方案是从三种并排渲染的设计中挑选出来的。
- **爆炸视图**。将 `AM_Controller["explode"]` 从 0 调到 1，所有零件都会沿堆叠轴向滑开。
- **3D 打印**。每个零件一个 STL 文件，另有一个完整的 3MF 文件，提供三种配置：树脂 ×1、树脂 ×1.5 和 FDM ×2。

| 正面刻度盘 | 背面刻度盘 |
|---|---|
| ![正面刻度盘，行星带有颜色和标签](docs/images/front.jpg) | ![默冬与沙罗螺旋刻度](docs/images/back.jpg) |

| 爆炸视图 | 内部（展开） |
|---|---|
| ![爆炸视图静帧](docs/images/exploded.jpg) | ![爆炸视图视频中的一帧](docs/images/exploded_video_frame.jpg) |

## 视频

- [`antikythera.mp4`](build/out/renders/antikythera.mp4)：20 s。曲柄转过 4 年，行星、月球和背面刻度盘全部随之运动。
- [`antikythera_eclate.mp4`](build/out/renders/antikythera_eclate.mp4)：15 s 爆炸视图。机械在齿轮持续转动的同时逐层展开，然后重新合拢。

视频中行星有时**向后运动**，这并不是 bug。这是从地球上看到的**逆行**现象，而该机械正是为展示它而制造的。龙指针（月球交点）则始终反向转动。

## 快速上手

1. 安装 **Blender 5.2** 或更高版本。
2. 打开 [`build/out/am.blend`](build/out/am.blend)，按 **空格键** 播放动画。
3. 选中 `AM_Controller`，修改它的自定义属性：
   - `crank`：年数；1 即 b1 转一圈；
   - `explode`：0 到 1；
   - `patina`：0 为崭新的青铜，1 为博物馆藏品般的铜锈。
4. 在大纲视图（Outliner）中隐藏集合：
   - 隐藏 `AM_CASE` 和 `AM_DIALS`，可查看齿轮传动；
   - 隐藏 `AM_HYPOTHETICAL`，只保留有实证的部分；
   - 隐藏 `AM_LABELS`，去除标签；
   - 隐藏 `AM_STAGE`，去除布光场景。
5. 点击任意零件即可查看其自定义属性：`status`、`role`、`teeth`、`module` 和 `sources`。

### 重新运行验证

请使用 Blender 自带的 Python。以下路径适用于 macOS，在其他系统上请相应调整。

```sh
PY=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
BL=/Applications/Blender.app/Contents/MacOS/Blender

$PY tools/validate_spec.py          # exact linear solve (1 DOF, 22 targets), centre distances, collision screening
$PY tools/check_kinematics.py       # pin-and-slot laws, followers, elongations, retrogrades, solar apogee
cd build && $PY -m unittest discover -s tests && $PY -m am.verify --stage all && cd ..
$BL -b build/out/am.blend --python-exit-code 1 -P tools/crosscheck_blend.py   # Blender rotations vs an independent solver
```

[`build/README.md`](build/README.md) 列出了每一个构建、检查、导出和渲染步骤，每个步骤对应一条命令。

### 从主提示词完整重建

在一个**空**文件夹中，使用 [Claude Code](https://claude.com/claude-code)：

```sh
claude -p --model 'claude-opus-5-5[1m]' --effort xhigh --permission-mode acceptEdits \
  --allowedTools Bash Read Write Edit Glob Grep < PROMPT_OPUS.md
```

- [`prompts/PROMPT_OPUS_v1_validated.md`](prompts/PROMPT_OPUS_v1_validated.md) 是一次性生成本构建的确切版本（89 min）。
- [`PROMPT_OPUS.md`](PROMPT_OPUS.md) 为 v1.2。它新增了行星颜色与标签、博物馆式布景、爆炸滑块以及爆炸视图视频。这些内容都是事后通过 `tools/` 中的脚本添加到本构建中的，v1.2 尚未从零重新运行过。

## 制作过程

1. **资料研究**。多个并行智能体研读了一手文献：Freeth et al. 2006、2008 和 2021（含补充信息）、Price 1974、Budiselic et al. 2020、Woan & Bayley 2024、Anastasiou et al. 2014 等。研究结果被整合为一个统一的数据集，再由一个“怀疑论者”智能体进行核查。
2. **规格定义**。[`spec/antikythera.json`](spec/antikythera.json) 是唯一的事实来源。它给出了每个齿轮的齿数、模数、轴线位置、z 范围和内孔，以及每一根轴、短轴、凸台、销、刻度盘和每一种材料。它由 `tools/make_spec.py` 生成，该脚本修正了已发表数据中 22 处几何上不可能成立的问题（例如，按已发表的距离，b2 无法同时与 c1 和 l1 啮合）。每个中心距都经过精确求解。
3. **独立检查**。`tools/validate_spec.py` 和 `tools/check_kinematics.py` 与生成器不共享任何代码，变异测试证实它们能够捕捉到人为注入的错误。
4. **用包络法生成冠齿**。`tools/crown_envelope.py` 将 a1 和 q1 的冠齿（端面齿）计算为对偶齿轮的轮齿永远扫不到的区域。随后 `tools/test_crowns_blender.py` 在 Blender 中用 BVH 对其进行检查。
5. **对抗式评审**。两轮独立评审覆盖了数据、经实时实测的 Blender API、可执行性和几何，共发现 5 个阻断性问题和约 60 个其他问题，现已全部修复。
6. **一次性构建**：由一个全新的 Opus 5.5 会话仅凭提示词完成，共 131 轮，约 5,000 行代码，所有验收标准全部通过。
7. 对结果进行**独立验证**：测试、精确检查、完整的 BVH 检查，以及将 `am.blend` 中的每个刚体与独立求解器逐一交叉核对（7·10⁻⁷ rad）。

## 仓库结构

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

## 坦诚说明局限

- 行星齿轮系、月球交点和真太阳遵循 Freeth et al. 2021 的**假设性**模型。动画能够运转，并不能证明原件就是这样制造的。
- 部分数值从未发表。对于这些数值，规格采用了有据可查的默认值，列于 `spec/antikythera.json` → `unresolved_defaults`：
  - 后板上各轴的角度；
  - 宇宙环的半径；
  - 初始相位（历元未经校准）。
- 轮齿为共轭渐开线齿（30° 齿条，即古代的等边三角形齿形），而非原件上手工锉出的三角形齿。
- 行星颜色仅为便于阅读，并无历史依据。

## 主要文献

- T. Freeth et al., "A Model of the Cosmos in the ancient Greek Antikythera Mechanism", *Scientific Reports* 11, 5821 (2021)，及其补充信息（Supplementary Information）。
- T. Freeth et al., "Decoding the ancient Greek astronomical calculator known as the Antikythera Mechanism", *Nature* 444, 587 (2006).
- T. Freeth, A. Jones, J. Steele, Y. Bitsakis, "Calendars with Olympiad display and eclipse prediction on the Antikythera Mechanism", *Nature* 454, 614 (2008).
- T. Freeth & A. Jones, "The Cosmos in the Antikythera Mechanism", ISAW Papers 4 (2012).
- D. de Solla Price, *Gears from the Greeks* (1974).
- C. Budiselic et al. (2020)；G. Woan & J. Bayley (2024)：历法环的孔数。
- M. Anastasiou et al. (2014)：背面刻度盘的螺旋。

带 URL 的完整文献列表见 `spec/antikythera.json` → `sources`。

## 许可协议

- **代码**：MIT（[`LICENSE`](LICENSE)）。
- **渲染图、视频、3D 模型、打印文件和文本**：CC BY 4.0（[`LICENSE-MEDIA.md`](LICENSE-MEDIA.md)）。
- **学术数据**：请引用上述文献。

---

使用 [Claude Code](https://claude.com/claude-code)（Claude Opus 5 / 5.5）为 taciclei 构建。
