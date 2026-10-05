# 本地原作文件

原作目录已加入 `.gitignore`，只保留空目录占位文件；不会提交原作源码或素材。固定来源、版本、发行包 SHA-256 和原始源码 SHA-256 保存在 `scripts/upstream.lock.json`。

- Promesst 1.01：https://silverspaceship.com/promesst/
- Promesst 2 1.00：https://silverspaceship.com/promesst2/
- Linux 移植作者：David Gow；原作作者：Sean Barrett。

运行 `python3 scripts/fetch_upstream.py`，或用 `--archive-dir` 指定自己下载的包。导入过程只提取原作源码、说明和素材，不将 x86 程序或随包 Linux 系统库用于掌机版。修改后的源码由 `prepare_sources.py` 生成到被忽略的 `build/`，原始文件保持不变。

下载与导入校验完成日期：2026-10-05。未找到明确的整体游戏再分发许可，见 [来源说明](../licenses/README.md)。
