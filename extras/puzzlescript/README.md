# Order of the Sinking Star 的另外三个前身

这三个前身合计五款游戏，均使用 PuzzleScript：

| 游戏 | 作者 | 作者发布的来源 |
| --- | --- | --- |
| Skipping Stones to Lonely Homes | Alan Hazelden | [官网及源码链接](https://alan.draknek.org/games/puzzlescript/skipping-stones.php) |
| Mirror Isles | Alan Hazelden | [官网及源码链接](https://alan.draknek.org/games/puzzlescript/mirrors.php) |
| Heroes of Sokoban | Jonah Ostroff | [一代](https://sites.math.washington.edu/~ostroff/puzzles/Heroes_of_Sokoban.html) |
| Heroes of Sokoban II: Monsters | Jonah Ostroff | [二代](https://sites.math.washington.edu/~ostroff/puzzles/Heroes_of_Sokoban_II_Monsters.html) |
| Heroes of Sokoban III: The Bard and The Druid | Jonah Ostroff | [三代](https://sites.math.washington.edu/~ostroff/puzzles/Heroes_of_Sokoban_III_The_Bard_and_The_Druid.html) |

[Order of the Sinking Star 官方商店介绍](https://store.steampowered.com/app/499170/Order_of_the_Sinking_Star/)确认这些游戏是其设计基础。

本工具获取固定版本的原版规则、关卡与像素图案，将其整理成掌机运行器可以读取的文件。没有重写游戏规则，也不把它们接入 Promesst 的 C / SDL2 代码。
原作下载、提取脚本和本地 ZIP 均被 Git 忽略，公共仓库只保存工具、版本与说明。未确认原作整体再分发授权，因此不要将这些完整 ZIP 或游戏文件上传到公开仓库。

## 生成两个本地试用包

Python 3.8+，只使用标准库，不需要编译游戏：

```bash
python3 extras/puzzlescript/prepare.py
```

自动获取原作并逐一校验下载文件与提取源码的 SHA-256。Heroes 使用作者官网的独立 HTML 导出，仅读取其中的源码字符串，不执行下载的 JavaScript。
Alan 的两个游戏使用作者官网链接到的 Gist，固定到具体源码版本。

离线获取后，可以按 `upstream.lock.json` 中的 `archive_name` 命名五个下载文件，再导入：

```bash
python3 extras/puzzlescript/prepare.py --archive-dir /path/to/downloads
```

产物：

- `dist/sinking-star-predecessors.arkos.local.zip`：五个 `.pz` 游戏文件，使用 ArkOS 的 PuzzleScript 模拟器。
- `dist/sinking-star-predecessors.portmaster-addon.local.zip`：五个 `.txt` 游戏文件，补充到已经安装的 PuzzleScript PM。

两种包都包含 `INSTALL.txt` 和记录原作哈希的 `SOURCES.json`；不附带运行器或修改固件。打包后校验 ZIP CRC 和五款原作内容的哈希。

## ArkOS 安装

[ArkOS 官方说明](https://github.com/christianhaitian/arkos/wiki/ArkOS-Emulators-and-Ports-information#puzzlescript)列出了 `lr-puzzlescript` 核心及 `.pz` 格式。Skipping Stones 如果出现方向键响应慢，先试下方 PortMaster 路线，详见性能说明。

1. 将 ArkOS 包里的 `puzzlescript/` 文件夹放到当前使用的 ROM 卡根目录（电脑上一般显示为 `EASYROMS`）。
2. 文件应位于 `/roms/puzzlescript/` 或 `/roms2/puzzlescript/`。
3. 刷新游戏列表或重启 EmulationStation，从 PuzzleScript 系统进入游戏。

如果你的 XF40H 固件没有 PuzzleScript 系统或对应核心，请先试下方 PortMaster 路线；本工具不会代替你安装系统核心。

[核心上游](https://github.com/amberwhitehead/pzretro)的默认 RetroPad 操作为：方向键移动、A 动作、Y 撤销、Start 重置、L 返回标题。字母指 RetroPad 映射，可以在 RetroArch 快捷菜单的 Controls 中查看并修改。

**退出前使用 RetroArch 的 Save State；再次进入时 Load State。** 核心默认设置不保证自动保存关卡进度。Save State 可以保留关卡内状态及检查点；不同核心版本的存档兼容性仍需实际确认。

## PortMaster 安装

1. 先从 PortMaster 安装 **PuzzleScript PM**。
2. 将补充包里的 `puzzlescriptpm/` 合并到掌机当前使用的 `ports/` 目录。
3. 从 Ports 启动已有的 PuzzleScript PM，在游戏列表中选择对应标题。

[官方移植](https://github.com/PortsMaster/PortMaster-New/tree/main/ports/puzzlescriptpm)已经提供 Heroes 三部曲；本包使用 `sinkingstar_` 前缀，不覆盖已有游戏，也不复用旧游戏的存档键。

官方默认操作：方向键移动、X 动作、B 撤销、R1 重置、Select 退出。以设备实际映射为准。
运行器保存已完成的关卡进度和游戏主动创建的检查点；这不等于随时保存当前位置。
Skipping Stones 使用游戏检查点；Mirror Isles 和 Heroes 以关卡进度为主。如果需要完整的关卡内存档，使用 ArkOS / RetroArch 路线。
该运行器的屏幕和输入处理依赖具体固件，因此在 XF40H 上仍需验收。

## Skipping Stones 方向键响应慢

XF40H 上已收到 ArkOS PuzzleScript 菜单运行 Skipping Stones 时，按方向键后要等一下才移动的反馈。目前没有取得该设备的核心版本、配置或耗时日志，因此尚未确认唯一原因。

原作使用一张 **76×70** 的大地图，只显示 **19×14** 的当前视区，并通过 `realtime_interval 0.1` 定期执行世界规则。可见范围小，并不意味着引擎只计算这一小块。[lr-puzzlescript 上游](https://github.com/amberwhitehead/pzretro#performance)说明复杂大地图可能无法及时完成更新。
核对上游 `6d859b47092f585a7ec05804c1d51a1676a06531` 的输入循环：先处理按键事件，再执行时间更新；首次方向输入没有故意等待 0.1 秒的设置。规则运算占用线程时，后续按键需要等当前计算结束；这是本次延迟的一个可能原因，仍需真机测量。

建议先做一次实际对比：

1. 在 ArkOS 的 RetroArch 快捷菜单中保存原来的 Save State。
2. 从 PortMaster 安装 **PuzzleScript PM**，合并本项目的 `portmaster-addon` 包。
3. 从 Ports 启动 PuzzleScript PM，选择 **Skipping Stones to Lonely Homes**，对比首次按方向键的响应。

官方 PM 运行器使用 Node.js / V8，ArkOS 核心使用 QuickJS；两条路线需要实测比较，不能据此保证 XF40H 的帧率或延迟。RetroArch Save State 不能直接转成 PM 的存档，需要在 PM 内重新开始，原来的 ArkOS 存档可以继续保留。
如果继续使用 ArkOS，可检查核心选项 **Anti-Aliased Font** 与 **PuzzleScript Plus Engine** 是否关闭；本作不需要这两个选项，上游默认也均为关闭。修改后重新启动游戏，具体选项以固件提供的核心为准。

没有通过减少地图、删除实时规则或改变计时来缓解延迟，这些修改需要额外验证原作机制与解谜结果。

新增 `benchmark_pm.js` 用于测量固定 PM 引擎的初始地图规则运算与软件绘制耗时：

```bash
python3 extras/puzzlescript/fetch_test_engine.py
node extras/puzzlescript/benchmark_pm.js
```

每项预热后测量 80 次，报告中位数、P95 和最大值。不接触实体输入、显示或音频，也不写玩家存档。结果只代表执行脚本的机器与 Node 版本；不包含控制器采样、显示输出和系统调度，不能当作 XF40H 按键到画面的延迟测试。

## 兼容性验证

以下检查使用固定版本的官方 PuzzleScript PM 引擎和开发机 Node.js，在 720×720 软件帧缓冲中执行，关闭实体输入、音频输出和真实显示设备：

- 五款原版脚本均无编译错误；共 89 张地图加载、执行开始规则并绘制通过（Skipping Stones 是一张大地图，其余各 22 张）。
- 第一张地图移动、动作处理、撤销恢复、重置，以及每款 300 次时间更新检查通过。
- 检查点格式恢复及新进程读档通过。存档测试主动建立测试检查点，不能当作已解谜到达原作检查点的证明。
- 检查实际绘制的 Skipping Stones、Mirror Isles 和 Heroes 游戏截图。

**尚未用 XF40H 真机或 ArkOS 随附的 libretro 核心执行这些文件，也未完成通关测试。** 这些是可拷卡试用的原版游戏文件，不是已经验证所有固件兼容性的最终移植版本。

复验需要 Node.js 18+；测试引擎下载到被忽略的 `build/puzzlescript/pm-engine/`，不会打进游戏文件包：

```bash
python3 extras/puzzlescript/fetch_test_engine.py
node extras/puzzlescript/verify_pm.js
```

引擎提交和各文件 Git blob 校验值记录在 `upstream.lock.json`。测试结果与本地截图在 `build/puzzlescript/validation/`。
