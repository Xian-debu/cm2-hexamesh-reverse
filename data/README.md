# q4t3 输入数据

本目录只放说明，**不放厂商 demo 或 .dat 数据**。四个输入文件受厂商评估许可约束，
请自行从 CM2 MeshTools SDK 5.7 demo 获取。

## 需要的文件

| 文件 | 字节 | 顶点 | 面（quad + tri） |
| --- | ---: | ---: | ---: |
| cast_q4t3.dat | 62,138 | 619 | 577（553 + 24） |
| hatch_q4t3.dat | 377,066 | 4,010 | 2,086（1,984 + 102） |
| bielle_q4t3.dat | 304,205 | 3,345 | 1,406（1,336 + 70） |
| crank_q4t3.dat | 4,386,795 | 49,198 | 13,684（13,116 + 568） |

## 格式

纯文本、CRLF、科学计数法，两段：

1. 第一行 N x 3[，随后 N 行 x y z；
2. 下一行 M x 4[，随后 M 行四个 1-based 索引；第 4 个索引为 4294967295
   表示三角形，其余表示四边形。

解析器在 cm2hx/q4t3.py；它会把三角形拆成三条边、修复朝向并计算带符号体积。
原 demo 用同样的几何做六面体主导网格；本实现用体素填充近似（见 README）。

## 怎么用

把四个 .dat 放进本目录（.gitignore 会忽略 *.dat，不会误提交），然后：

    ./tests/run_all.sh
    python3 -m cm2hx.demo q4t3 data/cast_q4t3.dat out

也可以显式指定目录：

    export CM2_Q4T3_DIR=/path/to/data
    ./tests/run_all.sh

数据目录不存在时 verify 会打印 SKIP 并以 0 退出，单元测试仍全部运行。
