# CM2 HexaMesh(R) Iso 5.7 demo — 独立行为等效重写

![tests](https://github.com/Xian-debu/cm2-hexamesh-reverse/actions/workflows/tests.yml/badge.svg)

本仓库是对 CM2 HexaMesh Iso 5.7 demo 的**独立重写**：用 Python 标准库重建
demo 的六条 TMSHHX 测试路径、q4t3 输入解析、MEDIT/BDF/NEU 输出格式与网格统计。
仓库**不含任何厂商二进制、DLL、输入 .dat 或反编译全文**，也不包含厂商源码。

- 上游对象：CM2 MeshTools SDK 5.7 precompiled demo（Windows x64，2026-05）
- 本实现：Python 3.10+，零第三方依赖，不加载 DLL、不需要 Wine
- 公开仓：https://github.com/Xian-debu/cm2-hexamesh-reverse

## 结论先行

| 用例 | oracle 节点/单元 | 本实现节点/单元 | oracle 体积 | 本实现体积 | 判定 |
| --- | --- | --- | --- | --- | --- |
| TMSHHX01 CUBE | 729 / 512 H8 | 729 / 512 H8 | 64 | 64 | 几何精确；文本顺序不同 |
| TMSHHX10 RINGS | 1200 / 600 H8 | 1200 / 600 H8 | 439.2305 | 439.230496 | 数量/体积/bbox/hard 精确；Qmin 不同 |
| cast | 755 / 632（H8 317, W6 73, P5 166, TH4 76） | 1760 / 794（全 H8） | 392708.2 | 487615 | 表面与 hard 精确；体网格近似 |
| hatch | 2912 / 3893（1036/221/1515/1121） | 8139 / 3407（全 H8） | 18019.33 | 29973.5 | 同上 |
| bielle | 1812 / 1764（739/150/550/325） | 5300 / 2456（全 H8） | 0.9830531 | 1.50704 | 同上 |
| crank | 49131 / 66138（31801/4786/17428/12123） | 74126 / 35069（全 H8） | 116897.2 | 87347.7 | 同上 |

> 注：oracle 节点数是控制台统计的实际引用数；本实现列出的是 MEDIT 文件中的 Vertices 数
> （四例均为生成的全部顶点）。两者口径不同，不能直接相减。
> q4t3 四例的体积误差分别为 +24.2% / +66.3% / +53.3% / −25.3%。

**做到了**：六条用例可离线重跑；文件名、控制台字段、MEDIT/BDF/NEU 段结构、
CRLF 行尾、CHEXA 续行与原 demo 一致；CUBE 的逐单元坐标集合精确；RINGS 的
节点数、单元数、体积、包围盒、hard nodes/edges/faces 精确；q4t3 的输入表面
（点数、面数、hard 计数）100% 还原。

**没做到**：不是逐字节同一文件。CUBE 节点编号顺序不同；RINGS 少 33 个
未引用顶点且 Qmin 更高；q4t3 体网格由独立体素填充器生成，是水密、正体积的
全六面体网格，但**没有复刻厂商的六面体/楔形/金字塔/四面体边界模板**，因此
单元数、体积、拓扑都不与 oracle 一致。原厂 C++ 源码不可恢复。

完整验收与逐项判据见 [docs/27](docs/27-cm2-hexamesh-acceptance.md)。

## 快速开始

    git clone https://github.com/Xian-debu/cm2-hexamesh-reverse.git
    cd cm2-hexamesh-reverse

    # CUBE / RINGS（不依赖任何私有数据）
    python3 -m cm2hx.demo cube  out
    python3 -m cm2hx.demo rings out

    # 单元测试（9 个；无 q4t3 数据时 verify 自动跳过）
    ./tests/run_all.sh

    # q4t3 案例（需要从厂商 demo 取得的 .dat，见 data/README.md）
    # 方式一：放进本仓 data/ 目录（该目录默认被 .gitignore 忽略 .dat）
    cp /path/to/demo/data/*_q4t3.dat data/
    ./tests/run_all.sh
    # 方式二：显式指定目录
    CM2_Q4T3_DIR=/path/to/demo/data ./tests/run_all.sh
    python3 -m cm2hx.demo q4t3 /path/to/demo/data/cast_q4t3.dat out

输出：CUBE/RINGS 写 TMSHHX01.mesh / .bdf / .neu（RINGS 为 TMSHHX10.*）；
q4t3 先写输入表面回显 <name>.dat.mesh，再写 <name>.dat_HX.mesh 与
<name>.dat_HX.bdf，与原 demo 一致（不写 .neu）。

## 输入数据不随仓库分发

厂商 demo、DLL 与四个 q4t3 输入都受其自身许可约束，**不在本仓库中**。
要跑 q4t3 路径，请自行取得 demo，并把 CM2_Q4T3_DIR 指向包含
cast_q4t3.dat / hatch_q4t3.dat / bielle_q4t3.dat / crank_q4t3.dat 的目录。
格式说明与计数见 [data/README.md](data/README.md)。

本仓库的 CI 与默认测试不依赖这些数据：9 个单测运行通过（其中 2 个 q4t3
用例在无数据时跳过），oracle 校验打印 SKIP 后退出 0。

## 等价层级

| 层级 | 内容 | 状态 |
| --- | --- | --- |
| L1 行为/CLI | 六条用例、诊断字段、导出文件名与顺序 | 一致 |
| L2 文件格式 | MEDIT/BDF/NEU 段结构、字段、CRLF、CHEXA 续行 | 一致；CUBE 三份文件行数 1252/2496/4325 相同 |
| L3 几何 | CUBE 精确；RINGS 数量/体积/bbox/hard 精确；q4t3 仅输入表面精确 | 部分达成 |
| L4 字节级 | 同一 md5 | 未达成 |

验收判据 A1–A10 的结果是 6 PASS / 2 PARTIAL / 2 FAIL（A3 字节级、A5 q4t3
几何级未达成），详见 [docs/27](docs/27-cm2-hexamesh-acceptance.md)。

## 目录

    cm2hx/
      cube.py       结构化 9^3 立方体网格
      rings.py      24 站 x 5 环 x 5 quad 的环状扫掠网格
      q4t3.py       q4t3 表面解析、朝向修复、带符号体积
      voxel.py      q4t3 表面 -> 水密体素六面体（列扫描奇偶填充）
      mesh.py       网格容器、体积、缩放 Jacobian 质量、水密判定
      formats.py    MEDIT / BDF / NEU / q4t3 写出与 MEDIT 读回
      demo.py       六条 TMSHHX 用例驱动与控制台报告
      verify.py     对照记录值做结构校验
    tests/          单元测试与一键脚本
    data/           输入数据说明（数据本身不在仓库）
    evidence/       oracle 校验和与复现环境
    docs/           规划、自授权、总验收（发布副本）

## 复现 oracle

原始 demo 在 Linux 上可用 Wine 9.0 运行；本仓库只记录方法和校验和，不附带二进制。
步骤、环境变量与六个用例的 md5 见 [evidence/oracle.md](evidence/oracle.md)。

## 许可与声明

本仓库代码与文档以 MIT 许可发布，仅覆盖本仓库中独立创作的部分。
厂商名称、CM2/HexaMesh 商标与 demo 本身的许可归其权利人；本仓库与厂商无隶属、
无背书关系，也不授予任何厂商二进制或数据的使用权。详见 [LICENSE](LICENSE)
与 [NOTICE](NOTICE)。

## 文档

- [docs/25 逆向规划](docs/25-cm2-hexamesh-reverse-plan.md)
- [docs/26 自授权清单](docs/26-cm2-hexamesh-self-authorization.md)
- [docs/27 总验收报告](docs/27-cm2-hexamesh-acceptance.md)
- [docs/README 发布副本说明](docs/README.md)
