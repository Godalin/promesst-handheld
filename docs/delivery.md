# 安装包与运行目录

## 面向玩家的交付

发布 `promesst.zip` 和 `promesst2.zip`，可以只安装其中一个，也可以同时安装。
目标是：在有可用 PortMaster 的已验证 ArkOS 设备上，解压到系统实际使用的 `ports/` 目录，
从 Ports 菜单选择对应游戏启动。包内自带程序、允许分发的素材和必要的附加依赖。

目前已生成两代完整个人本地使用包，尚未真机验证或获得整体游戏公开再分发授权。
原作源码和素材被 Git 忽略；完整本地包通过 `package.py --local-full` 生成。默认打包不含素材，但二进制仍包含原作代码，不能据此认为可公开再分发。

## 打包来源

`packaging/portmaster/<游戏>/` 为预留目录。实际使用 `launch.sh.in` 和共享输入模板生成启动脚本，打包工具生成
README、元数据与实机截图。二进制、附加库和资源由打包过程放入 `staging/`。
最终包写入 `dist/`，源码、工具链与回归数据不进入玩家安装包。

PortMaster 提交目录按官方规范生成：

```text
staging/portmaster/port/
├── promesst/
│   ├── port.json
│   ├── README.md
│   ├── screenshot.png
│   ├── gameinfo.xml
│   ├── Promesst.sh
│   └── promesst/
│       ├── promesst.aarch64
│       ├── data/
│       ├── libs.aarch64/       # 如有额外动态库
│       └── licenses/
└── promesst2/
    ├── port.json
    ├── README.md
    ├── screenshot.png
    ├── gameinfo.xml
    ├── Promesst 2.sh
    └── promesst2/
        ├── promesst2.aarch64
        ├── data/
        ├── libs.aarch64/       # 如有额外动态库
        └── licenses/
```

手动安装用 ZIP 的顶层直接包含启动脚本和同名游戏目录，而不是要求玩家寻找多层子目录。
提交 PortMaster 的目录和手动安装 ZIP 分别生成、分别校验。

## 安装后的示例

```text
<实际 ROM 根目录>/ports/
├── Promesst.sh
├── Promesst 2.sh
├── promesst/
│   ├── promesst.aarch64
│   ├── data/
│   ├── licenses/
│   ├── saves/                 # 首次运行创建
│   ├── conf/                  # 首次运行创建
│   └── log.txt                # 运行日志
└── promesst2/
    ├── promesst2.aarch64
    ├── data/
    ├── licenses/
    ├── saves/
    ├── conf/
    └── log.txt
```

运行数据不会随发布 ZIP 下发，升级包不覆盖 `saves/` 和 `conf/`。
一代与二代存档互不混用；启动另一代也不会覆盖此前进度。

## 启动脚本约定

1. 按 PortMaster 官方方式寻找控制目录、加载 `control.txt` 和固件适配文件。
2. 使用 PortMaster 提供的 `directory`、`DEVICE_ARCH` 与 `get_controls`，兼顾双卡路径和控制器配置。
3. 检查对应架构的二进制及资源，并创建该游戏的 `saves/`、`conf/`。
4. 通过项目路径变量传入资源、存档和配置位置，设置随包动态库的搜索目录。
5. 优先使用游戏的 SDL2 原生控制器支持；有必要时使用 gptokeyb 提供退出快捷键，避免重复映射动作键。
6. 通过 PortMaster 平台辅助启动，游戏正常退出后清理本次启动产生的辅助进程。

两个启动脚本分别发布，可共用仓库内的生成模板。最终安装包中的脚本能够独立工作。
不得硬编码只能使用 `/roms` 或第一张卡，不修改系统库，不在第一次启动时要求在线下载素材。

## 发布资料

`port.json` 填写真实架构、依赖、安装说明和作者信息；完成全包和真机验证后才标记 ready-to-run。
截图使用真实游戏画面，满足官方要求的 4:3 比例和至少 640×480 分辨率。
保留原作者及已有移植作者的署名，附上源码、素材及随包依赖所要求的许可材料。
发布记录包括源码版本、构建环境、测试设备及固件版本。

## 官方依据

- [PortMaster 打包规范](https://portmaster.games/packaging.html)
- [ArkOS Ports 入口说明](https://github.com/christianhaitian/arkos/wiki/ArkOS-Emulators-and-Ports-information#ports)
