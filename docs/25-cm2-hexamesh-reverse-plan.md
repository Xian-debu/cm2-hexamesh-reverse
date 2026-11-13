> 发布副本（2026-11-13）：原文为 /root/re24-admin/docs/25-cm2-hexamesh-reverse-plan.md。
> 正文保留原始路径、提交号与措辞；独立仓历史与两处措辞更正见 docs/README。
> 更正：原文“clean-room 语义”不准确——实现基于黑盒运行与静态反编译分析，
> 不是严格 clean-room；本仓 NOTICE 使用“独立重写、不复制厂商源码或二进制”。

# 25 · CM2 Hexamesh Iso 一比一等效源码逆向规划（2026-11-13）

> 状态：已执行（2026-11-13；结果见 docs/27）｜对象：/root/projects/逆向1/cm2_hexamesh_iso_demo.zip
> 目标仓：/root/re24-admin（本文件）｜实施目录：reverse/cm2-hexamesh/
> 授权：用户 m01634 全权授权无人值守执行；自授权清单单独提交，见 docs/26。

## 25.1 结论先行

- 原厂 **源码不可恢复**：交付物是 Windows x64 PE + 7 个 CM2 DLL，核心 `cm2::hexamesh_iso::mesher::run` 位于 1.4 MB DLL 的 RVA 0x10e0a0，跨度约 113 KB，无 PDB、无符号、无导出源码；反编译只能得到行为线索，不能还原原始 C++。
- 因此本任务交付的是 **独立的行为等效实现**（clean-room 语义，不复制二进制），而不是「原厂源码复原」。等效分 L1–L4 四级，逐级给出可验证判据；L4 字节级只对 CUBE 争取，q4t3 四例明确不承诺逐字节。
- 可达性判断：CUBE（TMSHHX01）几何/拓扑可精确复现；RINGS（TMSHHX10）可复现结构化表面与同量级体网格，精确节点序列不保证；cast/hatch/bielle/crank 四例可复现 CLI、文件格式、网格有效性、体积与质量量级，拓扑不承诺一致。

## 25.2 目标物与许可

| 项 | 值 |
| --- | --- |
| zip | /root/projects/逆向1/cm2_hexamesh_iso_demo.zip，3,173,390 B，md5 069106e83f40a54743ca67bbbc40d5fb |
| 解压 | 20 文件，10,267,405 B |
| demo | cm2_hexamesh_iso_demo.exe，58,848 B，PE32+ console，SDK 5.7.0.0 |
| 核心 DLL | cm2hexamesh_iso_x64_57.dll，1,397,216 B，38 个导出符号 |
| 数据 | 4 个 *_q4t3.dat：cast 62,138 B / hatch 377,066 B / bielle 304,205 B / crank 4,386,795 B |
| 许可 | 45 天内部评估；允许 import/run/analyze working behavior、modify/adapt/recompile Source Code；未检出 reverse/decompile 禁令 |
| 交付边界 | 不复制、不再分发原二进制与 .dat；仓库只保存解析器、生成器、测试与摘要 |

## 25.3 探测证据（已完成）

### 25.3.1 动态基线

在 re24 发行版内用 Wine 9.0 跑通 demo（rc=0），工作目录 `extracted/cm2/libs/Releasex64`，固定输入 `printf "y\n\n"`。六个用例与原始统计：

| 用例 | 输入 | 节点 | 单元 | 体积 | Qmin | 用时 |
| --- | --- | --- | --- | --- | --- | --- |
| TMSHHX01 CUBE | 参数 8 | 729 | 512 H8 | 64 | 1.0 | <0.1 s |
| TMSHHX10 RINGS | 0x18,8,5 | 1200 | 600 H8 | 439.2305 | 0.4236856 | <0.1 s |
| cast | cast_q4t3.dat | 755 | 632（H8 317/W6 73/P5 166/TH4 76） | 392708.2 | 0.2856775 | — |
| hatch | hatch_q4t3.dat | 2912 | 3893（1036/221/1515/1121） | 18019.33 | 0.03009062 | — |
| bielle | bielle_q4t3.dat | 1812 | 1764（739/150/550/325） | 0.9830531 | 0.2285347 | — |
| crank | crank_q4t3.dat | 49131 | 66138（31801/4786/17428/12123） | 116897.2 | 0.1230315 | 18.48 s 总 |

Oracle 文件与 md5 已存档（见 25.7 R0 证据目录）；控制台 out.txt 13,223 B，md5 1285aeb1f8cd3b968b1db24bf1458993。

### 25.3.2 静态分析

- exe 由 Ghidra 12.1.4 headless 导出 140 函数到 `decomp-exe.c`（4,217 行）：main `FUN_140002b20`、CUBE `FUN_140003140`、RINGS `FUN_140003780`、q4t3 读文件 `FUN_140004700` / 用例 `FUN_140004d90`。
- CUBE 路径：`extrude_translate` + `extrude_translate_Q4` + 绕三轴各 90° + `merge`/`simplify` → `mesher::run`。RINGS 路径：`extrude_rotate` + `extrude_rotate_Q4` + 5 层 copy/translate/rotate → `mesher::run`。
- DLL 只导出 `mesher::run(data_type&)` 等 38 个符号；`settings_type` 默认值与内部八叉树全部内联在 113 KB 区间，逐指令复刻不现实。
- 结论：走「行为契约 + 独立算法」路线，用 oracle 做差分，而不是反编译抄写。

### 25.3.3 输出格式事实

- MEDIT/VIZIR `.mesh`：`MeshVersionFormatted 3`、`Dimension 3`、注释、`Vertices N`、坐标 `%.6E`（三位指数）、`Hexahedra`/`Pyramids`/`Tetrahedra` 段、行尾 `0`、`End`；**不写 wedges**。
- 该省略是导出器怪癖：cast 的统计 632 含 W6 73，而 `.mesh` 段合计 559；W6 只出现在 `.bdf` 的 `CPENTA`。复刻必须保留这个行为。
- Nastran `.bdf`：CM2 头、MAT1、`GRID*` 两行长格式，单元 `CHEXA`/`CPENTA`/`CPYRAM`/`CTETRA`。
- FEMAP `.neu`：星号头、版本 403/404、节点与单元记录。
- 统计里的 `Nodes` 是**被引用节点数**，不是 `.mesh` 的 `Vertices N`：cast 文件 809 顶点、统计 755；hatch 4889/2912；bielle 3786/1812；crank 84939/49131。
- q4t3 输入：首段 `N x 3[` 坐标（CRLF、科学计数法），次段 `M x 4[`，1-based；第 4 个索引为 4294967295 表示三角形，否则四边形。只有 quad 段，三角混排。

### 25.3.4 几何线索

- CUBE 输出是精确 9³ 笛卡尔网格：x/y/z 0..4、步长 0.5，729 点、512 个 0.5 立方体；首 hex 为 (176,174,385,386,175,173,388,387)，坐标解出为 0.5 立方体。节点顺序非张量积，但点集与单元集可精确判定。
- RINGS 输出是 5 个互相垂直、沿 x 平移 7.8 的矩形截面环面（截面外半径 6、内半径 4、半高 1，24 个角度站、每站 9 个轮廓点，含接缝重复点）；后 4 个环交替绕 x 轴旋转 90°，形成链状。输出 1233 顶点中仅 1200 被引用，含 153 个内部点。
- q4t3 输出保留全部输入顶点（cast 619 → 809 = +190；bielle 3345 → 3786 = +441），内部加点；被引用数小于输入数说明大量输入点未被使用/合并。边界节点基本沿用输入坐标。

## 25.4 等价定义（L1–L4）

| 级别 | 含义 | 判据 |
| --- | --- | --- |
| L1 行为 | 同一 CLI、同一六用例、同文件命名、同控制台字段、同退出码 | `python3 -m cm2hx demo` 产出 6 组文件；stdout 含 Nodes/Elements/Volume/Qmin/Total |
| L2 格式 | 四类文件可被独立解析器读回，头/段/计数/精度/单位与 oracle 同构 | 自写解析器 round-trip；字段与段名逐项比对；wedge 省略行为一致 |
| L3 几何 | CUBE 点集/单元集完全一致（允许编号置换）；RINGS 体积 ±5%、单元数 ±10%；q4t3 体积 ±10%、单元类型齐全、全部单元有正体积、封闭性检查通过 | 差分脚本输出 PASS/FAIL 与相对误差 |
| L4 字节 | oracle 文本逐字节一致 | 只对 CUBE 的 .mesh/.bdf/.neu 争取；RINGS/q4t3 不承诺 |

说明：L3 的「点集一致」按坐标排序后比较（容差 1e-6），单元按顶点坐标集合比较，不比较编号；这避免把「文本顺序」误当几何差异。

## 25.5 可达性与不承诺项

**可达**
1. CUBE：由参数 8 直接生成 9³ 网格，几何/拓扑精确。
2. 六用例 CLI 与文件格式：解析 oracle 后 100% 可实现。
3. q4t3 输入解析与输入表面导出：已验证格式，能逐点复现。
4. 网格有效性：正体积、边界封闭、无重复单元，可自检。
5. 质量指标：体积、Qmin（按 oracle 同定义重算）、单元类型统计，可复现量级。

**不承诺**
1. 原厂源码逐行复原（无源码、无符号）。
2. q4t3 的节点编号、单元编号、内部点位置与 oracle 一致；八叉树边界投影是 113 KB 内联逻辑，独立实现只能逼近。
3. RINGS 的 153 个内部点精确坐标；只保证表面结构、规模与体积量级。
4. 任意新输入的工业级鲁棒性；验收只覆盖随包六例与格式契约。

## 25.6 实施架构

```
reverse/cm2-hexamesh/
  README.md                 入口、状态、等价等级、复现命令
  pyproject.toml            零依赖，仅 stdlib
  cm2hx/
    __init__.py
    q4t3.py                 q4t3 解析/写出
    mesh.py                 网格数据结构（nodes/cells、体积、质量、边界）
    surface.py              输入表面、封闭性、法向
    grid.py                 体素/八叉树近似与边界投影
    cube.py                 CUBE 精确生成
    rings.py                RINGS 结构化生成
    mesher.py               通用 hex-dominant 生成器
    export_medit.py         .mesh 写出（含 wedge 省略）
    export_nastran.py       .bdf 写出
    export_femap.py         .neu 写出
    demo.py                 六用例 CLI 与控制台统计
    verify.py               oracle 差分与验收报告
  tests/                    stdlib unittest
  docs/                     等价说明、已知差异
```

算法基线（通用 q4t3）：
1. 解析输入表面，统一绕向，计算 bbox、体积、边长中位数。
2. 以边长中位数为尺度建立体素格；用射线法判定格点/格心在内部。
3. 对完全在内部的体素生成 H8；边界体素做「外点向表面最近点投影 + 有效性检查」，退化为 P5/TH4/W6 时按模板拆分。
4. 合并重复节点，删除未引用节点（或按 oracle 怪癖保留未引用节点），写三种格式。
5. 自检：每个单元正体积、边界无悬空面、体积与 bbox 合理。

## 25.7 阶段计划与提交

| 阶段 | 内容 | 提交信息 | 验收 |
| --- | --- | --- | --- |
| R0 | 证据归档：out.txt、六例输出摘要、oracle md5、探测脚本 | `reverse(cm2): 归档探测证据与 oracle 摘要` | 证据可复现；不含二进制/.dat |
| R1 | 子工程骨架 + 解析器 + 格式写出 + 测试 | `reverse(cm2): 骨架与 q4t3/四格式解析` | 解析 oracle 四例无异常；round-trip 测试过 |
| R2 | CUBE 精确生成 + 三格式导出 | `reverse(cm2): CUBE 精确网格与导出` | 点集/单元集与 oracle 一致；文件可解析 |
| R3 | RINGS 结构化生成 | `reverse(cm2): RINGS 链状环面与体网格` | 1200 点/600 单元量级；体积 ±5% |
| R4 | q4t3 通用 mesher | `reverse(cm2): q4t3 hex-dominant 生成器` | 四例全部产出；正体积；体积 ±10% |
| R5 | demo CLI + 差分验收 | `reverse(cm2): 六用例 CLI 与差分验收` | A1–A8 全过；报告落 docs/27 |
| R6 | 总验收与收尾 | `reverse(cm2): 总验收与交付说明` | 报告、tag、goal 关闭、最终汇报 |

每阶段一小步一提交；R0 与 R6 之间不修改 /root/re24 与发行版，只在 reverse 子工程和证据目录工作。

## 25.8 验收判据（A1–A10）

| 编号 | 判据 | 通过标准 |
| --- | --- | --- |
| A1 | 六用例可跑 | `python3 -m cm2hx demo --out DIR` rc=0，生成 6 组 .mesh/.bdf/.neu |
| A2 | CUBE 几何 | 729 点、512 H8；点集与 oracle 一致（1e-6）；单元集一致 |
| A3 | CUBE 文本 | .mesh/.bdf/.neu 与 oracle 字节一致（L4 目标） |
| A4 | RINGS 规模 | 1200±1 引用节点、600±1 单元；体积 439.2305±5% |
| A5 | q4t3 四例 | 四例均有输出；体积相对误差 ≤10%；全部单元正体积；元素类型覆盖 H8/W6/P5/TH4 |
| A6 | 格式契约 | 自写解析器读回全部输出；wedge 省略行为与 oracle 一致；未引用顶点策略明确 |
| A7 | 质量指标 | 复算 Volume/Qmin，与 oracle 同量级；报告给出逐例数值 |
| A8 | 无原二进制依赖 | 测试与 demo 在只含源码+输入的目录可跑；不读取 oracle 输出 |
| A9 | 差分报告 | verify 输出逐例表（节点/单元/体积/Qmin/误差/PASS） |
| A10 | 文档与提交 | README/docs 与实测一致；git 干净；tag `cm2-hexamesh-v1.0` |

## 25.9 风险与应对

| 风险 | 影响 | 应对 |
| --- | --- | --- |
| 通用 mesher 边界投影产生退化单元 | A5 失败 | 投影后逐单元体积检查；退化则回退为体素 H8；记录回退数 |
| 体积偏差 >10% | A4/A5 失败 | 以输入表面体积为基准做尺度校准；必要时加密一层边界 |
| RINGS 表面构造推断错误 | 规模/体积偏差 | 先用 5 环结构生成，差分后调截面与角度站；文档记录推断依据 |
| 数值格式差异 | L2 失败 | 用 oracle 实际文本反推格式（指数位、字段宽度、换行），测试固定 |
| 时间不足 | 阶段未完成 | 按 R0→R5 顺序提交；未完成项在报告如实标注，不伪造 PASS |

## 25.10 交付物清单

- reverse/cm2-hexamesh 源码、测试、README、docs。
- docs/26 自授权清单（单独提交）。
- docs/27 总验收报告（结论、表格、关键数字、复现、边界）。
- 证据目录（摘要与 md5，不含原始二进制/.dat）。
- tag `cm2-hexamesh-v1.0`；goal 关闭记录。

## 25.11 变更记录

| 日期 | 变更 | 原因 |
| --- | --- | --- |
| 2026-11-13 | 初版：探测证据、L1–L4 等价、R0–R6、A1–A10、风险 | 用户 m01634 要求先规划后执行 |
| 2026-11-13 | 状态改为已执行；实际结果、偏差与 A3/A5 失败见 docs/27 | 执行完成，回填真实状态 |
