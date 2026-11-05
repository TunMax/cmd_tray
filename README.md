# cmd_tray

在 Windows 托盘中运行命令行程序的小工具。

`cmd_tray` 会在一个新的控制台中启动指定命令，自动隐藏控制台窗口，并在系统托盘中提供一个图标，用于显示/隐藏控制台或退出程序。适合 Jellyfin、Node.js 服务、Python 脚本等需要常驻后台、但不想一直占用任务栏的程序。

## 功能

- 启动命令时自动创建独立控制台
- 通过子进程 PID 绑定控制台窗口，不依赖 exe 名称、窗口标题或 `FileName`
- 启动后自动隐藏控制台
- 托盘菜单支持显示/隐藏控制台
- 退出时向控制台窗口发送关闭消息
- 支持使用 uv 配置开发环境
- 通过 GitHub Actions 自动构建并发布 Windows exe

## 环境要求

- Windows 10 / 11
- Python 3.9 及以上（仅源码运行需要）
- 依赖：`wxPython`、`PyYAML`、`pywin32`

## 目录结构

源码运行：

```text
cmd_tray/
├── cmd_tray.py
├── cmd_tray.yaml          # 必须与 cmd_tray.py 同目录
├── pyproject.toml
├── README.md
├── LICENSE
└── favicon.ico            # 示例图标
```

使用打包后的 exe：

```text
任意目录/
├── cmd_tray.exe
├── cmd_tray.yaml          # 必须与 cmd_tray.exe 同目录
└── icons/
    └── app.ico
```

目标程序（例如 `jellyfin.exe`）不需要和 `cmd_tray` 放在同一目录。只要它在 `PATH` 中，或在 `CMD` 中使用绝对路径即可。

## 配置文件

编辑与 `cmd_tray.py` / `cmd_tray.exe` 同目录的 `cmd_tray.yaml`：

```yaml
# 托盘图标路径：绝对路径，或相对于本程序所在目录的路径；仅支持 .ico
Logo: ./favicon.ico

# 鼠标悬停在托盘图标上时显示的名称，也是托盘菜单的第一项
AppName: Jellyfin 10.7.7

# 要执行的命令，由 cmd.exe /c 执行；无需写 start
CMD: 'jellyfin'

# FileName 已废弃：窗口句柄通过启动的进程自动获取
# 可以删除、留空或保留旧值，均不影响运行
```

### 配置项说明

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `Logo` | 是 | 托盘图标路径，只支持 `.ico`。相对路径基于 `cmd_tray.py` / `cmd_tray.exe` 所在目录 |
| `AppName` | 否 | 托盘提示文字，默认为 `CMD Tray` |
| `CMD` | 是 | 要执行的命令，会由 `cmd.exe /c` 在新控制台中启动 |
| `FileName` | 否 | **已废弃**。旧配置可以保留，程序不会读取 |

如果命令中包含空格或引号，需要同时遵循 YAML 和 `cmd.exe` 的引号规则。例如：

```yaml
CMD: '"C:\Program Files\MyApp\app.exe" --port 8080'
```

示例中的 `CMD: 'jellyfin'` 只是演示，实际使用时替换为你自己的命令。

## 快速开始

### 方式一：源码 + uv（推荐）

1. 安装 [uv](https://docs.astral.sh/uv/getting-started/installation/)。
2. 获取源码并进入目录：

   ```powershell
   git clone https://github.com/TunMax/cmd_tray.git
   cd cmd_tray
   ```

3. 按需修改 `cmd_tray.yaml`，并准备好图标文件。
4. 创建环境并安装依赖：

   ```powershell
   uv sync
   ```

5. 启动程序：

   ```powershell
   uv run cmd_tray.py
   ```

   如果不想让启动器本身占用一个控制台窗口，可以使用：

   ```powershell
   uv run pythonw cmd_tray.py
   ```

不使用 uv 时，请自行安装 `wxPython`、`PyYAML`、`pywin32`，然后运行 `python cmd_tray.py`。

> 第一次使用可以先验证托盘功能：把 `CMD` 改成 `ping 127.0.0.1 -t` 并运行，确认图标和显示/隐藏功能正常后，再替换为实际命令。

### 方式二：使用打包后的 exe

1. 将 `cmd_tray.exe`、`cmd_tray.yaml` 和图标文件按目录结构放置。
2. 编辑 `cmd_tray.yaml`，确认 `CMD` 可以正常执行。
3. 双击 `cmd_tray.exe`。
4. 启动成功后，系统托盘会出现图标，控制台会自动隐藏。

## 托盘菜单

右键单击托盘图标：

| 菜单项 | 作用 |
| --- | --- |
| `AppName` | 显示当前程序名称，无操作 |
| 显示/隐藏控制台 | 切换控制台窗口的显示状态 |
| 退出 | 向控制台窗口发送关闭消息，并退出托盘程序 |

如果目标程序已经退出，托盘图标仍会保留。此时点击“显示/隐藏控制台”会提示未找到窗口，可以选择“退出”。

## 工作原理

1. 读取程序目录下的 `cmd_tray.yaml`。
2. 使用 `subprocess.Popen(..., creationflags=CREATE_NEW_CONSOLE)` 启动 `CMD`。
3. 通过 `AttachConsole(pid)` 附加到子进程控制台，再用 `GetConsoleWindow()` 获取窗口句柄。
4. 保存该句柄并隐藏控制台，托盘菜单后续直接操作这个句柄。
5. 如果句柄失效，会尝试重新绑定。

因此不再需要通过 `FileName` 拼接窗口标题来 `FindWindow`，也不会受窗口标题变化影响。

## 注意事项

- **仅支持 Windows**：程序依赖 `win32gui`、`win32console` 等 Windows API。
- **不要在 `CMD` 里写 `start`**：程序本身已经会创建新控制台。写 `start` 可能导致进程脱离控制台，从而无法绑定窗口。
- **目标程序需要保持控制台窗口存在**：纯 GUI 程序或启动后立即脱离控制台的命令，可能无法获取窗口句柄。
- **Windows Terminal 限制**：如果 Windows 默认终端应用是 Windows Terminal（ConPTY），可见窗口由 Windows Terminal 管理，`GetConsoleWindow()` 返回的可能是隐藏的伪控制台窗口，导致自动隐藏/显示失效。可在 Windows Terminal 的“设置 → 启动 → 默认终端应用程序”中改为“Windows 控制台主机”。
- **启动最多等待 8 秒**：如果 8 秒内获取不到控制台窗口，程序会提示并退出。
- **配置位置固定**：`cmd_tray.yaml` 必须与 `cmd_tray.py` / `cmd_tray.exe` 同目录，程序不会从当前工作目录查找。
- **`CMD` 的工作目录**：目标命令继承启动 `cmd_tray` 时的工作目录。如果目标程序依赖相对路径，请在快捷方式中设置正确的“起始位置”，或在命令中使用绝对路径。
- **退出行为**：点击“退出”会向控制台窗口发送 `WM_CLOSE`。如果目标程序不响应关闭消息，可能仍会留在后台，需要手动结束。
- **图标格式**：`Logo` 只支持 `.ico`，不支持 `.png`、`.jpg`。
- **管理员权限**：如果目标程序需要管理员权限，请以管理员身份启动 `cmd_tray`，否则子进程同样没有权限。

## 常见问题

### 启动后提示“程序未能获取控制台窗口，即将关闭”

可能原因：

- `CMD` 为空或命令无法执行；
- 命令启动后立即退出；
- `CMD` 中使用了 `start`，或命令自行脱离了控制台；
- 目标是 GUI 程序，没有可绑定的控制台窗口；
- 默认终端为 Windows Terminal，控制台窗口由 Windows Terminal 承载。

### 托盘图标不显示

- 检查 `Logo` 路径是否正确，建议先使用绝对路径测试；
- 确认文件是有效的 `.ico` 格式；
- 确认 `cmd_tray.yaml` 与程序位于同一目录。

### 点击“显示/隐藏控制台”没有反应

- 目标程序可能已经退出，窗口句柄已失效；
- 默认终端可能为 Windows Terminal，参见上文“注意事项”；
- 程序启动时获取窗口失败，托盘图标虽然存在，但无法控制窗口。

### 退出后目标程序还在运行

程序通过关闭控制台窗口来结束目标进程。如果目标程序屏蔽了关闭消息，或自行创建了独立进程，需要手动结束。可以在任务管理器中结束对应进程。

### 提示找不到 `cmd_tray.yaml`

请确认配置文件与 `cmd_tray.py` / `cmd_tray.exe` 位于同一目录，而不是当前终端的工作目录。

## 打包（可选）

如需分发为 exe，可以使用 PyInstaller：

```powershell
uv add --dev pyinstaller
uv run pyinstaller --noconsole --onefile --name cmd_tray cmd_tray.py
```

打包完成后：

1. 从 `dist\` 取出 `cmd_tray.exe`；
2. 将 `cmd_tray.yaml` 和图标文件按目录结构放在 exe 旁边；
3. 双击 `cmd_tray.exe` 运行。

`--noconsole` 用于避免托盘程序自身弹出控制台窗口。目标程序仍由 `cmd_tray` 在新控制台中启动。`cmd_tray` 只负责启动和隐藏控制台，不会打包目标程序本身。

如果打包后提示缺少 `win32console`，可以追加隐藏导入参数：

```powershell
uv run pyinstaller --noconsole --onefile --name cmd_tray --hidden-import win32console cmd_tray.py
```

### GitHub Actions 自动构建与发布

仓库已配置 `.github/workflows/build-exe.yml`。

- 当 `cmd_tray.py`、`pyproject.toml`、`cmd_tray.yaml` 或 `favicon.ico` 在 `master` / `main` 分支发生变化时，会自动构建 Windows exe；构建成功后会创建 GitHub Release。
- 创建或更新 Pull Request 时只构建并上传 Artifact，不发布 Release。
- 也可以在 Actions 页面手动触发；手动触发时，仅从 `master` / `main` 分支运行会发布 Release。

Release 版本号使用中国标准时间（UTC+8）的日期，例如 `20261105`。如果当天已经存在同名 Tag 或 Release，则依次使用 `20261105.post1`、`20261105.post2` 等。发布包名称为 `cmd_tray-<版本号>-windows-x64.zip`，包含 exe、配置文件、图标、README 和 LICENSE。

在仓库的 Actions 页面选择 `Build and Release Windows EXE`，进入对应运行记录，在页面底部下载 Artifact；或直接在 Releases 页面下载发布包。

如果创建 Release 时提示权限不足，请检查仓库的 `Settings → Actions → General → Workflow permissions`，确保工作流可以写入仓库内容。

## 许可证

本项目基于 [GNU General Public License v3.0](LICENSE) 发布。
