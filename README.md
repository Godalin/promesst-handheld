# Promesst / Promesst 2 掌机移植

面向 **XF40H + ArkOS + PortMaster** 的两款独立游戏。使用 C + SDL2，保留原作规则，新增掌机输入、方屏缩放、可靠写入存档和独立运行目录。

当前状态：两代已生成 Linux aarch64 程序，并通过容器内的原作对照与运行验证。**尚未在 XF40H 真机测试，也未完成两代通关验证。** `dist/` 中的完整包是本地个人使用的候选版本。

## 在掌机上安装

GitHub 仓库不附带完整游戏安装包。请先按照下方“从源码重建”步骤在本地生成 ZIP，再安装到掌机。

1. 确保 ArkOS 中已安装可用的 PortMaster。
2. 将 `dist/promesst.aarch64.local-full.zip` 或 `dist/promesst2.aarch64.local-full.zip` 解压到系统实际使用的 `ports/` 目录。
3. 确认启动脚本与游戏目录并列，从 Ports 菜单启动对应游戏。

```text
ports/
├── Promesst.sh
├── promesst/
│   ├── promesst.aarch64
│   ├── data/
│   ├── INSTALL.txt
│   ├── saves/                 # 首次运行创建
│   └── conf/                  # 首次运行创建
├── Promesst 2.sh
└── promesst2/
    ├── promesst2.aarch64
    ├── data2/
    ├── INSTALL.txt
    ├── saves/
    └── conf/
```

需要 aarch64 用户空间和 SDL2 ≥ 2.0.8。程序动态使用系统 SDL2，安装包不替换系统库。启动失败时查看相应游戏目录中的 `log.txt`。更新时保留 `saves/` 和 `conf/`。

## 操作

按实体位置定义动作，不依赖按键上印刷的 A/B 字母。

| 实体按键 | 动作 |
| --- | --- |
| 方向键 / 左摇杆 | 移动、菜单导航 |
| 下方动作键 | 原作 Z 动作、菜单确认 |
| 右方动作键 | 原作 X 动作 |
| 左方动作键 | 原作 C 动作（二代） |
| R1 | 按原作规则撤销一个房间 |
| Start | 菜单 |
| 上方动作键 | 切换整数缩放 / 等比最大化，保存缩放偏好 |
| Select + Start | 原生控制模式下保存并退出 |

默认 320×240 逻辑画布，在 XF40H 的 720×720 屏幕上以 640×480 居中显示。等比最大化模式为 720×540。原作能力解锁时机和说明保留。
SDL 控制器映射缺失时，启动脚本会尝试 PortMaster 的 gptokeyb 键盘映射。该模式使用 PortMaster 的退出快捷键；建议从游戏菜单的保存退出项离开。

## 从源码重建

原作源码、关卡和素材 **不提交到 Git**。本仓库保存固定版本、校验值、获取工具和适配代码。源码下载包仍由各自从官网获取。

```bash
# 获取本项目的适配代码
git clone https://github.com/Godalin/promesst-handheld.git
cd promesst-handheld

# Python 3.8+；在线下载固定版本并校验 SHA-256
python3 scripts/fetch_upstream.py

# 或先自行从官网下载两个发行包，再离线导入
python3 scripts/fetch_upstream.py --archive-dir /path/to/downloaded/archives

# 需要正在运行的 Docker；依赖只安装到容器
bash scripts/build.sh aarch64

# 生成供个人本地使用的完整资源包
python3 scripts/package.py --local-full
```

`package.py` 默认生成需要自行补素材的包，`--local-full` 才包含本地原作素材。即使不包含素材，二进制仍包含原作代码和嵌入关卡；公开再分发许可需要另外确认。当前没有明确的整体游戏再分发授权，详情见 [许可与来源](licenses/README.md)。

桌面 Linux 或 macOS 已安装 CMake、pkg-config、SDL2 时，可使用 `bash scripts/build.sh native`。运行时设置 `PROMESST_ASSET_DIR` 为本地对应游戏素材目录；桌面存档默认使用各代独立的 SDL 用户目录。当前验证使用 ARM64 Linux 容器，没有将 macOS 构建标记为已验证。

## 仓库结构

```text
├── CMakeLists.txt             # 两代程序、回归与原作对照目标
├── scripts/
│   ├── upstream.lock.json     # 固定下载 URL、版本、SHA-256
│   ├── fetch_upstream.py      # 获取或离线导入，解开嵌套源码包
│   ├── prepare_sources.py     # 检查并应用适配，源码生成到 build/
│   ├── Dockerfile            # Ubuntu 18.04 ARM64，兼容较旧 glibc
│   ├── build.sh              # 构建与验证入口
│   ├── package.py            # 分别生成两代 ZIP
│   └── bmp_to_png.py          # 本地运行截图转换
├── src/platform/
│   ├── sdl2/                 # 绘图、原作事件接口、控制器与循环
│   └── storage/              # 各代路径、原子保存、缩放偏好
├── packaging/portmaster/     # 独立启动脚本模板、备用输入映射
├── tests/                    # 存档/撤销回归、原作轨迹对照、包检查
├── docs/                     # 架构、交付、设备与验证记录
├── licenses/                 # 原创适配代码许可及来源说明
├── upstream/                 # 本地原作源码，已忽略
└── assets/                   # 本地原作素材，已忽略
```

`build/`、`staging/`、`dist/` 都被忽略。`src/games/` 和 `cmake/toolchains/` 暂为预留目录；当前通过获取原作后生成源码的方式构建，不维护另一份被提交的原作副本。

## 验证与来源

- [另外三个前身：PuzzleScript 五款游戏试用包](extras/puzzlescript/README.md)
- [验证记录与真机待办](docs/validation.md)
- [架构](docs/architecture.md)、[交付设计](docs/delivery.md)、[XF40H 方案](docs/devices/xf40h.md)
- [一代官方下载](https://silverspaceship.com/promesst/)、[二代官方下载](https://silverspaceship.com/promesst2/)
- [已有一代掌机移植参考](https://github.com/szymor/promesst)
- [PortMaster 打包规范](https://portmaster.games/packaging.html)
