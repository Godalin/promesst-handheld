# PortMaster 打包模板

`launch.sh.in` 按游戏名和素材目录生成两代独立的启动脚本。`controls.gptk` 仅在原生 SDL 控制器映射不可用时启动，避免两种输入同时触发动作。运行路径优先跟随启动脚本所在目录，支持空格、第二张卡和不同 ROM 根目录。

`scripts/package.py` 将实际 ARM64 程序与模板组装到 `staging/`，输出到 `dist/`。两代分别附上安装说明、来源资料、构建信息、元数据和本地运行截图。当前元数据标记为实验版本，尚未上传或提交 PortMaster。

完整结构见 [交付设计](../../docs/delivery.md)。
