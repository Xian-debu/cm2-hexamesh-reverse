# Oracle 证据（不含二进制）

这些值来自 2026-11-13 在 Linux 上用 Wine 9.0 运行 CM2 HexaMesh Iso 5.7 demo 的输出。
原始 zip、EXE、DLL 和 .dat **不在本仓库**；这里只记录可复核的测量值。

## 环境

- 宿主：Linux x86_64（Ubuntu 24.04 环境），Python 3.12
- Wine：9.0（/usr/lib/wine/wine64）
- demo：cm2_hexamesh_iso_demo.exe，PE32+ console，58,848 B，SDK 5.7.0.0
- 输入：交互提示回答 y，随后回车；六个用例由 demo 内置菜单驱动
- 工作目录：extracted/cm2/libs/Releasex64
- 环境变量：WINEPREFIX=<独立前缀>、WINEDEBUG=-all、WINEDLLOVERRIDES=mscoree,mshtml=

## 输入包

| 项 | 值 |
| --- | --- |
| zip 大小 | 3,173,390 B |
| zip md5 | 069106e83f40a54743ca67bbbc40d5fb |
| 解压后 | 20 文件，10,267,405 B |

## 控制台

| 项 | 值 |
| --- | --- |
| out.txt 大小 | 13,223 B |
| out.txt md5 | 1285aeb1f8cd3b968b1db24bf1458993 |

## CUBE / RINGS

| 文件 | 字节 | 行数 | md5 |
| --- | ---: | ---: | --- |
| TMSHHX01.mesh | 50,556 | 1,252 | ee5d30530e90ae71034f4c5cae879461 |
| TMSHHX01.bdf | 101,083 | 2,496 | 07bbac75694802dc720d12ba3798b4b7 |
| TMSHHX01.neu | 126,856 | 4,325 | 423e7ff8865dd07c4f86351fb5ae1c06 |
| TMSHHX10.mesh | 79,297 | 1,844 | f1bf2dfa49182e150acc43fbeabbc5ac |
| TMSHHX10.bdf | 158,713 | 3,680 | c67515af2ca580befdf6598c2a46535c |
| TMSHHX10.neu | 173,549 | 5,445 | ff3dc9c7568acd6480869e99e1553818 |

## q4t3 输出

| 文件 | 字节 | md5 |
| --- | ---: | --- |
| cast_q4t3.dat_HX.mesh | 54,773 | 4ace315b82a8f9155c821aa7879d0a32 |
| cast_q4t3.dat_HX.bdf | 109,976 | ccec94d5d390a38e24b0768a9a65fe99 |
| hatch_q4t3.dat_HX.mesh | 344,311 | 19d82586eed44f5f3e7deda13ec9e688 |
| hatch_q4t3.dat_HX.bdf | 670,377 | 6d4a53978a7f0f720a53585125ba0ee8 |
| bielle_q4t3.dat_HX.mesh | 231,845 | 8813fa56145b72cfb07e88ce1aec230e |
| bielle_q4t3.dat_HX.bdf | 470,600 | 35ddd580084f187b84b16ce210082614 |
| crank_q4t3.dat_HX.mesh | 6,660,991 | a7fb0dc9f6141588e2a694e1558961da |
| crank_q4t3.dat_HX.bdf | 12,413,890 | 554361b49948feed92e9be09d7d67128 |

## 六个用例的统计

| 用例 | 节点 | 单元 | 体积 | Qmin |
| --- | ---: | ---: | ---: | ---: |
| TMSHHX01 CUBE | 729 | 512 H8 | 64 | 1.0 |
| TMSHHX10 RINGS | 1,200 | 600 H8 | 439.2305 | 0.4236856 |
| cast | 755 | 632（H8 317 / W6 73 / P5 166 / TH4 76） | 392,708.2 | 0.2856775 |
| hatch | 2,912 | 3,893（1036/221/1515/1121） | 18,019.33 | 0.03009062 |
| bielle | 1,812 | 1,764（739/150/550/325） | 0.9830531 | 0.2285347 |
| crank | 49,131 | 66,138（31801/4786/17428/12123） | 116,897.2 | 0.1230315 |

注意：统计中的 Nodes 是实际被单元引用的节点数；MEDIT 文件里的 Vertices 数更大
（例如 cast 文件有 809 个顶点）。本实现按文件顶点统计，见 README 表注。

## 复核方式

本仓库不附带二进制，因此无法仅凭本仓库重放 oracle。持有 demo 的读者可以：

1. 在 Wine 下运行 demo，工作目录指向解压后的 libs/Releasex64；
2. 回答 y 后按菜单依次运行 TMSHHX01/TMSHHX10/TMSHHX50；
3. 用 md5sum 对照上表。

结构校验器 cm2hx.verify 检查的是本实现是否满足记录的计数、体积、闭合性等
结构目标，不比对 md5。
