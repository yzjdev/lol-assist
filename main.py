import asyncio
from tkinter import *
from tkinter import font as tfont
from tkinter import ttk

from async_tkinter_loop import async_mainloop, async_handler

from lcu import lcu
from utils import save, get


def create_lobby_interface(mode, row, f):
    my_list = [item for item in mode.items()]
    for i in range(0, len(my_list), 3):
        row = row + i
        a = my_list[i:i + 3]
        for item in a:
            btn = ttk.Button(f, text=item[0], command=async_handler(lcu.create_lobby, item[1]))
            btn.grid(row=row, column=a.index(item), sticky=EW, padx=4, pady=4)
    return row


class Application(Tk):
    def __init__(self):
        super().__init__()
        self.window_resize()

        self.title('LOL助手')
        self.protocol('WM_DELETE_WINDOW', async_handler(self.close))
        self.font = ('', 16)  # 有部分组件效果不好，则使用font=font
        # 设置默认字体大小
        default_font = tfont.nametofont('TkDefaultFont')
        default_font.configure(size=16)

        # 组件
        self.champ_combobox = None
        # values
        self.auto_accept_var = BooleanVar(value=get('auto_accept', False))
        self.auto_select_var = BooleanVar(value=get('auto_select', False))
        self.auto_play_again_var = BooleanVar(value=get('auto_play_again', False))
        self.auto_matchmaking_search_var = BooleanVar(value=get('auto_matchmaking_search', False))

        self.game_phase_var = StringVar()
        self.summoner_info_var = StringVar()
        self.champ_entry_var = StringVar()
        self.champ_entry_var.trace(mode='w', callback=async_handler(self.on_champ_entry_changed))  # entry 内容监听

        # 显示游戏状态
        ttk.Label(self, textvariable=self.game_phase_var, font=self.font).pack()
        # 显示玩家信息
        Label(self, textvariable=self.summoner_info_var, font=self.font, height=2).pack()
        # 布局
        self.one_interface()
        self.two_interface()
        self.three_interface()


        self.start()  # 开始调用api
        self.register()  # 注册事件

    def window_resize(self, width=675, height=525):

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x_position = int((screen_width - width) / 2)
        y_position = int((screen_height - height) / 2)
        self.geometry('+{}+{}'.format(x_position, y_position))

    @async_handler
    async def start(self):
        await lcu.start()  # 启动服务
        phase = await lcu.get_game_phase()
        self.game_phase_var.set(phase)
        try:
            await self.show_summoner_info()  # 显示玩家信息
            await self.set_combobox_data()  # 绑定英雄数据
        except:
            pass

    async def close(self):
        await lcu.close()
        self.destroy()

    # Listener
    def register(self):
        lcu.register_ws_closed(self.ws_closed_listener)

        lcu.register('/lol-summoner/v1/current-summoner', self.summoner_listener, event_types=('UPDATE',))
        lcu.register('/lol-gameflow/v1/gameflow-phase', self.game_phase_listener, event_types=('UPDATE',))

    async def ws_closed_listener(self):
        self.start()

    async def summoner_listener(self, data):
        await self.show_summoner_info()


    # 游戏状态监听
    async def game_phase_listener(self, data):
        phase = data.data
        self.game_phase_var.set(phase)
        match phase:
            case 'Lobby':
                if self.auto_matchmaking_search_var.get():
                    await lcu.matchmaking_search()
            case 'ReadyCheck':
                if self.auto_accept_var.get():
                    await lcu.matchmaking_accept()
            case 'ChampSelect':
                if self.auto_select_var.get():
                    await lcu.champ_select(get('auto_select_champ_id'))
            case 'EndOfGame':
                await self.show_summoner_info()
            case 'PreEndOfGame':
                if self.auto_play_again_var.get():
                    await lcu.play_again()

    '''创建布局'''

    def one_interface(self):
        f = ttk.Frame(self)
        for i in range(4):
            f.columnconfigure(i, weight=1)
        f.pack(fill=X, padx=4, pady=4)

        a = ttk.Checkbutton(f, text='自动接受对局', variable=self.auto_accept_var, onvalue=True, offvalue=False)
        a['command'] = lambda: save('auto_accept', self.auto_accept_var.get())
        a.grid(column=0, row=0, padx=4, pady=4)

        b = ttk.Checkbutton(f, text='自动选择英雄', variable=self.auto_select_var, onvalue=True, offvalue=False)
        b['command'] = lambda: save('auto_select', self.auto_select_var.get())
        b.grid(column=1, row=0, padx=4, pady=4)

        self.champ_combobox = ttk.Combobox(f, state='readonly', width=14, font=self.font)
        self.champ_combobox.grid(column=2, row=0, padx=4, pady=4)

        champ_entry = ttk.Entry(f, textvariable=self.champ_entry_var, width=14, justify=CENTER, font=self.font)
        champ_entry.grid(column=3, row=0, padx=4, pady=4)

        c = ttk.Checkbutton(f, text='自动再玩一局', variable=self.auto_play_again_var, onvalue=True, offvalue=False)
        c['command'] = lambda: save('auto_play_again', self.auto_play_again_var.get())
        c.grid(column=0, row=1, padx=4, pady=4)

        d = ttk.Checkbutton(f, text='自动寻找对局', variable=self.auto_matchmaking_search_var, onvalue=True,
                            offvalue=False)
        d['command'] = lambda: save('auto_matchmaking_search', self.auto_matchmaking_search_var.get())
        d.grid(column=1, row=1, padx=4, pady=4)



    def two_interface(self):
        f = ttk.Frame(self)
        for i in range(3):
            f.columnconfigure(i, weight=1)
        f.pack(fill=X, padx=4, pady=4)

        ttk.Button(f, text='返回大厅', command=async_handler(lcu.delete_lobby)).grid(row=1, column=0, sticky=EW, padx=4,
                                                                                     pady=4)
        ttk.Button(f, text='寻找对局', command=async_handler(lcu.matchmaking_search)).grid(row=1, column=1, sticky=EW,
                                                                                           padx=4, pady=4)
        ttk.Button(f, text='取消寻找', command=async_handler(lcu.matchmaking_delete)).grid(row=1, column=2, sticky=EW,
                                                                                           padx=4, pady=4)

    def three_interface(self):
        game_mode = {
            '单排双排': 420, '自选模式': 430, '灵活组排': 440,
            '入门人机': 870, '新手人机': 880, '一般人机': 890,
            '大乱斗': 450, '斗魂竞技场': 1700
        }
        tactics_mode = {'双人作战': 1160, '匹配模式': 1090, '发条鸟的试炼': 1220, '排位': 1100, '狂暴模式': 1130}

        f = ttk.Frame(self)
        for i in range(3):
            f.columnconfigure(i, weight=1)
        f.pack(fill=X, padx=4, pady=4)

        ttk.Label(f, text='常规模式').grid(row=0, column=0)
        row = create_lobby_interface(game_mode, 1, f) + 1

        ttk.Label(f, text='云顶之弈').grid(row=row, column=0)
        create_lobby_interface(tactics_mode, row + 1, f)

    '''加载数据'''

    async def show_summoner_info(self):
        info = await lcu.get_current_summoner_info()
        name = info['name']
        level = info['level']
        xp = info['xp']
        essence = info['b&o']
        rp = info['rp']
        self.summoner_info_var.set('玩家：%s  等级：%s\n经验：%s  精萃：%s  点券：%s' % (name, level, xp, essence, rp))

    async def set_combobox_data(self):
        champs = await lcu.get_all_champ()
        names = [item.name for item in champs]
        self.champ_combobox['values'] = names
        champ, index = await lcu.get_champ_by_id(get('auto_select_champ_id'))
        self.champ_combobox.current(index)
        self.champ_combobox.bind('<<ComboboxSelected>>', async_handler(self.on_champ_selected))
        self.champ_entry_var.set(champ.id if champ else -1)

    async def on_champ_selected(self, event):
        champ, index = await lcu.get_champ_by_name(self.champ_combobox.get())
        self.champ_entry_var.set(champ.id if champ else '')

    async def on_champ_entry_changed(self, *args):
        var = self.champ_entry_var.get()
        try:
            champ, index = await lcu.get_champ_by_id(int(var))
        except ValueError:
            champ, index = await lcu.get_champ_by_name(var)
        if champ:
            save('auto_select_champ_id', champ.id)
        self.champ_combobox.current(index)


if __name__ == '__main__':
    try:
        app = Application()
        async_mainloop(app)
    except KeyboardInterrupt as e:
        pass
