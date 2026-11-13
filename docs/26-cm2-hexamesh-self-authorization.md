> 发布副本（2026-11-13）：原文为 /root/re24-admin/docs/26-cm2-hexamesh-self-authorization.md。
> 本文记录 re24-admin 子工程阶段的自授权；把代码整理为公开仓是后续的独立动作。
> 正文保留原始路径与措辞，便于审计；范围与可逆性以原文为准。

# 26 · CM2 Hexamesh 逆向自授权清单（2026-11-13）

> 授权来源：用户 m01634，原话要点「无人值守、全部授权」「先探测、制定规划并 git 提交、确认后逐项执行验证提交」「自授权清单单独增量提交」。
> 范围：仅限 /root/re24-admin 的 reverse/cm2-hexamesh 子工程、docs/25–27，以及 /root/projects/逆向1 与 re24 发行版内 /var/lib/re24-reverse 的私有证据目录。
> 本清单单独提交，不与其他实现提交混合。

## 26.1 我做了什么（按类别）

| 类别 | 动作 | 位置 | 可逆性 |
| --- | --- | --- | --- |
| 只读 | 读取 zip 清单、许可、readme；计算 md5/B 数 | /root/projects/逆向1 | 无副作用 |
| 解压 | 把 zip 解到私有目录 | re24:/var/lib/re24-reverse/extracted | 可删目录复原 |
| 动态 | Wine 9.0 运行 demo 六例，输入 y\n\n | 同上 | 生成的文件可删 |
| 静态 | Ghidra 12.1.4 headless 反编译 exe，导出 140 函数 | re24:/var/lib/re24-reverse | 项目目录可删 |
| 分析 | pefile 读 PE 头/导入/导出；字符串检索 | 宿主只读 | 无副作用 |
| 证据 | 复制 out.txt、六例输出到宿主 work/ 目录 | /root/projects/逆向1/work | 可删 |
| 编码 | 新建 reverse/cm2-hexamesh 纯 Python 源码、测试、README | /root/re24-admin | git 可回滚 |
| 提交 | 分阶段 git commit | /root/re24-admin | git revert |
| 文档 | docs/25 规划、docs/26 本清单、docs/27 总验收 | /root/re24-admin | git revert |

## 26.2 我没有做什么

- 没有修改 /opt/re24、/usr/local/bin/re24、re24-serve、re24-worker、DB、systemd 单元。
- 没有安装或升级任何软件包；Wine 9.0、Ghidra 12.1.4、Python 3.12、pefile 均为既有环境。
- 没有把任何原厂二进制、DLL、.dat 或反编译全文提交进 git。
- 没有外发网络请求；Ghidra、Wine、Python 全部本地运行。
- 没有读取或写入任何凭据、token、ssh key、浏览器 profile。
- 没有对真实用户会话执行 kill、删除、回滚。
- 没有改写 /root/re24 冻结仓；没有触碰 /root/chronicon-re。

## 26.3 破坏性操作与快照

| 操作 | 目标 | 快照/回滚 |
| --- | --- | --- |
| 解压 zip | /var/lib/re24-reverse/extracted | 原 zip 仍在，md5 已记录 |
| Wine 运行 | WINEPREFIX=/var/lib/re24-reverse/wineprefix | 独立 prefix，不碰用户默认 prefix |
| Ghidra 分析 | /var/lib/re24-reverse/ghidra-project | 独立项目目录 |
| 生成中间文件 | /tmp/cm2out、/tmp/q4、/tmp/cli | 临时目录，可删 |
| git 提交 | /root/re24-admin | 每个提交可用 git revert 回滚 |

没有执行 rm -rf 于任何非临时目录；没有覆盖用户文件。

## 26.4 许可与合规核对

- 许可文件：cm2_evaluation_licence_agreement.txt，8,128 B；45 天内部评估期。
- 明文允许：import / run / analyze working behavior；modify / adapt / recompile Source Code（在评估目的内）。
- 未检出 reverse engineering / decompile 的明文禁止条款（grep 未命中）。
- 交付不含原二进制；只含独立重写的 Python 源码、格式说明与统计摘要。
- 若许可方后续提出限制，删除 reverse/cm2-hexamesh 与 docs/25–27 即可完全撤回交付。

## 26.5 数据与隐私

- 输入 .dat 是厂商随包样例，不含个人信息。
- 反编译文本仅存于私有工作目录，未入库；仓库只保留函数名/地址等必要证据引用。
- 证据目录中的 md5、行数、统计值不构成二进制再分发。

## 26.6 提交边界

| 提交 | 内容 |
| --- | --- |
| 3a32dc6 | docs/25 逆向规划（先行提交，等确认） |
| eeaf3f4 | cm2hx 骨架 + CUBE/RINGS |
| 3c15fb6 | q4t3 解析 + 体素填充 |
| 717ffaa | 四格式写出 + demo 驱动 |
| dc09280 | 测试 + oracle 结构校验 |
| 本提交 | docs/26 自授权清单（单独） |
| 后续 | docs/27 总验收、README 索引、tag |

## 26.7 未授权即不做的事项

- 不向第三方分发原二进制或反编译全文。
- 不把本实现宣称为厂商源码或官方等价物。
- 不基于本实现提供商业交付。
- 不在许可期外继续使用原 demo 输出作为 oracle。
