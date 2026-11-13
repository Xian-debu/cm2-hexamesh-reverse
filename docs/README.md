# 文档（发布副本）

本目录是 /root/re24-admin 中 docs/25–27 的发布副本，正文保留原始写作时间、
本地路径与 re24-admin 的提交号，便于审计。独立仓的代码历史与 re24-admin
不同：独立仓由 git subtree split 得到，6 个提交，HEAD 9194dc0。

| 文件 | 内容 | 说明 |
| --- | --- | --- |
| 25-cm2-hexamesh-reverse-plan.md | 逆向规划：目标、许可、L1–L4、R0–R6、A1–A10 | 已执行 |
| 26-cm2-hexamesh-self-authorization.md | 自授权清单：做了什么、没做什么、可逆性 | 历史记录 |
| 27-cm2-hexamesh-acceptance.md | 总验收：六例对照、A1–A10、限制、复现 | 结论以本文为准 |

## 两处措辞更正

1. docs/25 初稿把实现称为 clean-room 语义。实际工作包含对 demo EXE 与 DLL 的
   静态反编译分析，因此不是严格 clean-room；正确说法是“独立重写、不复制厂商
   源码或二进制”。NOTICE 采用后者。
2. 原文的提交号、tag 与路径属于 /root/re24-admin；本仓的对应实现由 subtree
   split 发布；主体代码相同，测试默认数据目录改为本仓 data/，无数据时跳过 oracle 校验。
3. docs/27 §27.4 的 Wine 命令把 WINEPREFIX/WINEDEBUG 放在 printf 前，环境变量
   只会作用于 printf。正确写法是：
       printf "y\n\n" | env WINEPREFIX=/path/prefix WINEDEBUG=-all \
         WINEDLLOVERRIDES=mscoree,mshtml= /usr/lib/wine/wine64 ./cm2_hexamesh_iso_demo.exe
   正文保留原样，以本条为准。

原始规划、验收记录与更多工程文档保存在作者的 re24-admin 工作仓，未随本仓发布。
