# -*- coding: utf-8 -*-
import sys
import wx
import wx.adv
import multiprocessing, os, time, yaml
import win32gui, win32con
import subprocess


def cmd_run_lite(cmd):
    subprocess.run(cmd, shell=True)


def start_app(CMD):
    cmd_run_lite('start ' + CMD)


class FolderBookmarkTaskBarIcon(wx.adv.TaskBarIcon):
    MENU_ID1, MENU_ID2, MENU_ID3 = wx.NewIdRef(count=3)

    def __init__(self, ICON, TITLE):
        super().__init__()
        # 传参
        self.ICON = ICON
        self.TITLE = TITLE
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

    def onOne(self, event):
        pass

    def onTwo(self, event):
        if win32gui.IsWindowVisible(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
        else:
            win32gui.ShowWindow(hwnd, win32con.SW_SHOWNORMAL)

    def onExit(self, event):
        win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
        wx.Exit()


class MyFrame(wx.Frame):
    def __init__(self, ICON, TITLE):
        super().__init__()
        FolderBookmarkTaskBarIcon(ICON, TITLE)


if __name__ == "__main__":
    multiprocessing.freeze_support()  # 解决pyinstaller打包后多进程模块无法工作
    app = wx.App()
    # 读取yaml配置
    server_name = []
    with open('cmd_tray.yaml', 'r', encoding='utf8') as f:
        config = yaml.load(f.read(), Loader=yaml.FullLoader)
    # 启动相关exe
    multiprocessing.Process(target=start_app, args=(config['CMD'],)).start()
    # 找到cmd窗口并隐藏
    time_count = time.time()
    while True:
        hwnd = win32gui.FindWindow(None, os.getcwd().replace('/', '\\') + '\\' + config['FileName'])
        print('finding cmd window...')
        if hwnd != 0:
            win32gui.ShowWindow(hwnd, win32con.SW_SHOWNORMAL)
            win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
            break
        if time.time() - time_count > 8:
            wx.MessageBox('程序未能正常找到控制台窗口，即将关闭！', '注意', wx.OK | wx.ICON_WARNING)
            sys.exit()
    # 图标相对路径处理
    if os.path.exists(os.path.join(os.getcwd(), config['Logo'])) == True:
        config['Logo'] = os.path.join(os.getcwd(), config['Logo'])
    # Then a frame.
    frm = MyFrame(config['Logo'], config['AppName'])
    # Show it.
    frm.Show()
    app.MainLoop()
