# -*- coding: utf-8 -*-
import os
import subprocess
import sys
import time

import pywintypes
import wx
import wx.adv
import win32con
import win32console
import win32gui
import yaml


def start_app(cmd):
    """在新控制台中启动命令，返回子进程对象。"""
    return subprocess.Popen(
        cmd,
        shell=True,
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )


def find_console_hwnd(proc, timeout=8.0, interval=0.1):
    """获取子进程所使用控制台的窗口句柄。

    AttachConsole 把当前进程临时附加到子进程的控制台，再用
    GetConsoleWindow 取得该控制台窗口的 HWND。整个过程不依赖
    exe 名称、窗口标题或配置文件中的 FileName。
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            return 0
        try:
            # AttachConsole 要求当前进程未附加到其他控制台
            win32console.FreeConsole()
            win32console.AttachConsole(proc.pid)
            try:
                hwnd = win32console.GetConsoleWindow()
            finally:
                win32console.FreeConsole()
            if hwnd:
                return int(hwnd)
        except pywintypes.error:
            pass
        time.sleep(interval)
    return 0


class FolderBookmarkTaskBarIcon(wx.adv.TaskBarIcon):
    MENU_ID1, MENU_ID2, MENU_ID3 = wx.NewIdRef(count=3)

    def __init__(self, ICON, TITLE, hwnd, proc):
        super().__init__()
        # 传参
        self.ICON = ICON
        self.TITLE = TITLE
        self.hwnd = hwnd
        self.proc = proc
        # 设置图标和提示
        self.SetIcon(wx.Icon(self.ICON), self.TITLE)
        # 绑定菜单项事件
        self.Bind(wx.EVT_MENU, self.onOne, id=self.MENU_ID1)
        self.Bind(wx.EVT_MENU, self.onTwo, id=self.MENU_ID2)
        self.Bind(wx.EVT_MENU, self.onExit, id=self.MENU_ID3)

    def CreatePopupMenu(self):
        '''生成菜单'''

        menu = wx.Menu()
        menu.Append(self.MENU_ID1, self.TITLE)
        menu.Append(self.MENU_ID2, '显示/隐藏控制台')
        menu.Append(self.MENU_ID3, '退出')
        return menu

    def _get_hwnd(self):
        """返回有效的控制台窗口句柄，句柄失效时尝试重新绑定。"""
        if self.hwnd and win32gui.IsWindow(self.hwnd):
            return self.hwnd
        self.hwnd = 0
        if self.proc is not None and self.proc.poll() is None:
            self.hwnd = find_console_hwnd(self.proc, timeout=1.0)
        return self.hwnd

    def onOne(self, event):
        pass

    def onTwo(self, event):
        hwnd = self._get_hwnd()
        if not hwnd:
            wx.MessageBox('未找到控制台窗口，程序可能已经退出。', '提示',
                          wx.OK | wx.ICON_INFORMATION)
            return
        if win32gui.IsWindowVisible(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
        else:
            win32gui.ShowWindow(hwnd, win32con.SW_SHOWNORMAL)
            try:
                win32gui.SetForegroundWindow(hwnd)
            except pywintypes.error:
                pass

    def onExit(self, event):
        hwnd = self._get_hwnd()
        if hwnd:
            try:
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            except pywintypes.error:
                pass
        elif self.proc is not None and self.proc.poll() is None:
            self.proc.terminate()
        wx.Exit()


class MyFrame(wx.Frame):
    def __init__(self, ICON, TITLE, hwnd, proc):
        super().__init__()
        # 保存引用，避免托盘图标对象被回收
        self.tray_icon = FolderBookmarkTaskBarIcon(ICON, TITLE, hwnd, proc)


if __name__ == "__main__":
    app = wx.App()

    # 配置文件和程序放在同一目录，不依赖当前工作目录
    base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    config_path = os.path.join(base_dir, 'cmd_tray.yaml')
    with open(config_path, 'r', encoding='utf8') as f:
        config = yaml.safe_load(f) or {}

    cmd = str(config.get('CMD') or '').strip()
    if not cmd:
        wx.MessageBox('请在 cmd_tray.yaml 中填写要运行的 CMD。', '配置错误',
                      wx.OK | wx.ICON_ERROR)
        sys.exit(1)

    # 在新控制台中启动程序，然后绑定该控制台窗口
    try:
        proc = start_app(cmd)
    except OSError as exc:
        wx.MessageBox('启动命令失败：%s' % exc, '错误', wx.OK | wx.ICON_ERROR)
        sys.exit(1)

    hwnd = find_console_hwnd(proc)
    if not hwnd:
        wx.MessageBox('程序未能获取控制台窗口，即将关闭！', '注意',
                      wx.OK | wx.ICON_WARNING)
        if proc.poll() is None:
            proc.terminate()
        sys.exit()

    # 隐藏控制台窗口
    win32gui.ShowWindow(hwnd, win32con.SW_HIDE)

    # 图标相对路径处理
    logo = str(config.get('Logo') or '')
    if logo and not os.path.isabs(logo):
        logo_path = os.path.join(base_dir, logo)
        if os.path.exists(logo_path):
            logo = logo_path
    title = str(config.get('AppName') or 'CMD Tray')

    # Then a frame.
    frm = MyFrame(logo, title, hwnd, proc)
    # Show it.
    frm.Show()
    app.MainLoop()
