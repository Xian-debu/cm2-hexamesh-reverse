# CM2 HexaMesh(R) Iso 5.7 — 行为等效逆向实现（cm2hx）

本目录是 `/root/projects/逆向1/cm2_hexamesh_iso_demo.zip` 的独立逆向重写，
不含任何厂商二进制。目标不是复制 DLL，而是在**可复现、可审计**的前提下，
用 Python 标准库重建 demo 的六条测试路径、输入输出格式与几何结果。

## 结论先行

| 项目 | 原 demo | 本实现 | 判定 |
|---|---|---|---|
| TMSHHX01 CUBE | 729 节点 / 512 H8 / 体积 64 / Qmin 1 | 完全相同 | 几何精确，文件行数相同，节点编号顺序不同 |
| TMSHHX10 RINGS | 1200 / 600 / 体积 439.2305 / Qmin 0.4236856 | 1200 / 600 / 体积 439.230496227598 / Qmin 0.701057 | 数量、体积、bbox、hard 数完全一致；Qmin 不同 |
| cast q4t3 | 755 / 632（H8 317, W6 73, P5 166, TH4 76）/ 392708.2 | 1760 / 794（全 H8）/ 487615 | 输入 hard 数精确；体网格为阶梯体素，拓扑不等价 |
| hatch q4t3 | 2912 / 3893 / 18019.33 | 8139 / 3407 / 29973.5 | 同上 |
| bielle q4t3 | 1812 / 1764 / 0.9830531 | 5300 / 2456 / 1.50704 | 同上 |
| crank q4t3 | 49131 / 66138 / 116897.2 | 74126 / 35069 / 87347.7 | 同上 |

**明确边界**：CUBE/RINGS 做到了“几何等价 + 输出结构等价”，但不是逐字节
同一文件（节点编号/未引用顶点不同）。四个 q4t3 案例的**表面读取、
hard 计数、诊断输出格式**等价；体网格由独立的列扫描体素填充器生成，
能保证水密、正体积、Qmin=1，但**没有复刻厂商的八叉树边界模板**，
因此元素数量、体积和拓扑都不与 oracle 一致。详见“等价层级”。

## 用法

零第三方依赖，Python 3.10+：

```bash
cd reverse/cm2-hexamesh
python3 -m cm2hx.demo cube  /tmp/out        # TMSHHX01
python3 -m cm2hx.demo rings /tmp/out        # TMSHHX10
python3 -m cm2hx.demo q4t3  /path/cast_q4t3.dat /tmp/out
./tests/run_all.sh                          # 9 个单测 + 结构校验
```

校验器默认读取私有工作目录的 q4t3 输入；可用 `CM2_Q4T3_DIR` 覆盖：

```bash
CM2_Q4T3_DIR=/path/to/data python3 -m cm2hx.verify
```

输出文件：CUBE/RINGS 写 `.mesh`（MEDIT/VIZIR）、`.bdf`（Nastran BULK）、
`.neu`（FEMAP neutral）；q4t3 先写回显表面 `<name>.mesh`，再写
`<name>_HX.mesh` 与 `<name>_HX.bdf`（与原 demo 一致，不写 .neu）。

## 目录

```
cm2hx/
  cube.py       CUBE 的结构化 9^3 网格（几何精确）
  rings.py      RINGS 的 24 站 × 5 环 × 5 quad 扫掠网格
  q4t3.py       q4t3 表面读写、朝向修复、带符号体积
  voxel.py      q4t3 表面 → 水密体素六面体（列扫描奇偶填充）
  mesh.py       网格容器、体积、缩放 Jacobian 质量、水密判定
  formats.py    MEDIT / BDF / NEU / q4t3 写出与 MEDIT 读回
  demo.py       六条 TMSHHX 用例的驱动与诊断输出
  verify.py     对照 oracle 的结构校验（硬编码的是验收目标，不是实现输入）
tests/
  test_cm2hx.py 单测：计数、体积、闭环、格式行数、CRLF
  run_all.sh    单测 + 结构校验
```

## 等价层级

- **L1 行为/CLI**：六条用例、诊断字段、导出文件名与顺序一致；可独立运行。
- **L2 文件格式**：MEDIT/BDF/NEU 段结构、字段、CRLF、CHEXA 续行一致；
  CUBE 三份文件行数分别为 1252 / 2496 / 4325，与原文件完全相同。
- **L3 几何**：CUBE 逐单元坐标集合精确；RINGS 节点数、单元数、体积、
  bbox、hard nodes/edges/faces 精确。q4t3 只保证输入表面与 hard 计数精确，
  体网格是**近似**。
- **L4 字节级**：未达成。CUBE 节点编号顺序不同；RINGS 缺少原文件中的
  33 个未引用顶点；q4t3 体网格拓扑不同。

## q4t3 体网格为什么不是一比一

原 DLL 的 `mesher::run` 位于约 113 KB 的单一函数区间内，无符号/无 PDB；
它对表面做八叉树细化，并在边界生成 hex/wedge/pyramid/tet 混合模板。
仅凭静态反编译无法在可接受时间内复刻该模板系统。本实现选择：

1. 精确解析 q4t3（1-based、第 4 索引 4294967295 表示三角形）；
2. 用竖直射线与三角化表面求交，按奇偶性填充内部网格列；
3. 输出轴对齐六面体，保证水密、正体积、Qmin=1，可被 MEDIT/BDF 读回。

这满足“能跑、格式对、几何在包围盒内、体积同量级”，但不满足
“元素数量/拓扑逐项一致”。验收报告（docs/27）把这项列为**未达成**，
没有用“等价”掩盖差异。

## 复现环境

- 原 demo：Wine 9.0，`WINEPREFIX=/var/lib/re24-reverse/wineprefix`，
  工作目录 `extracted/cm2/libs/Releasex64`，输入 `y\n\n`。
- 本实现：Python 3.12，纯标准库；不加载 DLL、不需要 Wine。
- 原始二进制与输出仅存在于私有工作目录，未进入本仓库。

## 许可

`cm2_evaluation_licence_agreement.txt` 允许内部评估用途下的
import/run/analyze working behavior 与 modify/adapt/recompile Source Code，
期限 45 天；未检出名文 reverse-engineering 禁令。本目录只含独立重写代码，
不 redistribution 原二进制。
