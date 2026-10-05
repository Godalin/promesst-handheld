# 许可和来源

原作 main.c、关卡数据和素材来自 Sean Barrett 的官方下载包；Linux 移植由 David Gow 完成。
二代原作 credits 另外注明 Oryx 的 endgame art 和 Casey Muratori 的概念协助。
下载包中的整体游戏文件只带版权声明，当前没有找到明确的整体源码或素材再分发授权。
因此，Git 仓库不包含下载包、原始文件、生成后的原作源码和素材。

`scripts/fetch_upstream.py` 由使用者自行获取固定版本的官方发行包。
生成的完整 ZIP 是本地个人使用产物，不是已经获得再分发授权的公开发行版本。
公开发布包含原作代码的二进制也需要先确认授权，仅忽略素材不会改变这一点。

本项目新写的平台适配、获取、构建和测试代码使用 [MIT 许可](MIT.txt)。
这项许可只覆盖本项目原创代码，不覆盖原作代码、关卡、素材或第三方组件。

原作自带的 stb_image.c 和 stb_sdl2graph.h 标注 public domain。构建继续使用原作附带的图片解码器。
SDL2 动态链接到目标系统自带的库；安装包不复制 Docker 内的 SDL2 或系统库。
gptokeyb 使用已安装 PortMaster 提供的版本，安装包不复制其程序。
