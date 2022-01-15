# cmd_tray
支持cmd运行的应用最小化至托盘。

## 使用介绍
```yaml
# 使用说明，本程序和cmd_tray.yaml需放置在要运行的exe文件的相同目录下。

# 托盘图标文件的相对或绝对路径，仅支持.ico文件。
Logo: ./jellyfin-web/favicon.ico

# 鼠标悬停托盘图标时会显示的名称
AppName: Jellyfin 10.7.7

# 运行的cmd命令。
CMD: 'jellyfin'

# cmd命令所运行exe文件的名称。
FileName: jellyfin.exe
```