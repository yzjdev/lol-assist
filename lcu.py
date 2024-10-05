import asyncio
import json
from json import JSONDecodeError
from typing import Iterable

import aiohttp
from aiohttp import BasicAuth

from entris import ChampEntry, PerkEntry, WebsocketResponse
from utils import return_ux_process, parse_cmdline_args


class Lcu:
    def __init__(self):
        self.ws_task = {}

        self.register_uris = []

        self.addr = None
        self.ws_addr = None
        self.auth = None
        self._session = None
        self._pid = None
        self._port = None

        self._headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

    async def request(self, method, path, **kwargs):
        url = f'https://127.0.0.1:{self._port}{path}'
        if kwargs.get('data'):
            kwargs['data'] = json.dumps(kwargs['data'])
        return await self._session.request(method, url, ssl=False, **kwargs)

    # 启动
    async def start(self):
        try:
            process = next(return_ux_process(), None)
            while not process:
                process = next(return_ux_process(), None)
                await asyncio.sleep(1)
            process_args = parse_cmdline_args(process)
            self._pid = process_args['app-pid']
            self._port = process_args['app-port']
            auth_token = process_args['remoting-auth-token']

            self.addr = f'https://127.0.0.1:{self._port}'
            self.ws_addr = f'wss://127.0.0.1:{self._port}'
            self.auth = BasicAuth('riot', auth_token)
            self._session = aiohttp.ClientSession(auth=self.auth, headers=self._headers)

            await self.wait_api_ready()
            print('api ready')

            await self.run_ws()

            print('ws ready')

            print(self.addr, auth_token)

        except:
            pass

    # 关闭
    async def close(self):
        if not self._session is None and not self._session.closed:
            await self._session.close()

    async def wait_api_ready(self):
        while True:
            try:
                resp = await self.request('get', '/lol-summoner/v1/current-summoner')
                if resp.status == 200:
                    break
            except:
                pass
            await asyncio.sleep(1)

    # 连接websocket服务
    async def run_ws(self):
        async def run():
            async with aiohttp.ClientSession(auth=self.auth, headers=self._headers) as session:
                async with session.ws_connect(self.ws_addr, ssl=False) as ws:

                    await ws.send_json([5, 'OnJsonApiEvent'])
                    _ = await ws.receive()

                    while True:
                        msg = await ws.receive()
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            try:
                                data = json.loads(msg.data)[2]
                                resp = WebsocketResponse(data['eventType'], data['uri'], data['data'])

                                for event in self.register_uris:
                                    if event['uri'] == data['uri']:
                                        if data['eventType'].upper() in event['event_types']:
                                            asyncio.create_task(event['func'](resp))
                            except JSONDecodeError:
                                pass
                        elif msg.type == aiohttp.WSMsgType.CLOSED:
                            if self.ws_task:
                                await self.close()
                                asyncio.create_task(self.ws_task['ws_closed']())
                            break

        asyncio.create_task(run())

    async def refresh(self):
        await self._session.close()
        await self.start()

    def register_ws_closed(self, func):
        self.ws_task['ws_closed'] = func

    def register_ws_open(self, func):
        self.ws_task['ws_open'] = func

    # register('/lol-gameflow/v1/gameflow-phase', print_msg, event_types=('UPDATE',))
    # register('/lol-lobby/v2/lobby', lobby, event_types=('CREATE',))
    def register(self, uri, func, event_types: Iterable = ('UPDATE', 'CREATE', 'DELETE')):
        allowed_events = ('UPDATE', 'CREATE', 'DELETE')
        for event in event_types:
            if event not in allowed_events:
                raise RuntimeError('123')
        self.register_uris.append({
            'uri': uri,
            'func': func,
            'event_types': event_types
        })

    async def create_perk(self, perk: PerkEntry):
        data = {
            "name": perk.name,
            "primaryStyleId": perk.primary,
            "subStyleId": perk.sub,
            "selectedPerkIds": perk.perks,
        }
        if perk in await self.get_perks():
            print('符文已存在')
            return
        resp = await self.request('post', '/lol-perks/v1/pages', data=data)
        print('符文创建成功' if resp.status == 200 else '符文创建失败')

    # 获取当前符文（所有符文页中的最后一页）
    async def get_current_perk(self):
        resp = await self.request('get', '/lol-perks/v1/currentpage')
        if resp.status != 200:
            return
        data = await resp.json()
        perk_id = data['id']
        name = data['name']
        primary = data['primaryStyleId']
        sub = data['subStyleId']
        perks = data['selectedPerkIds']
        return PerkEntry(name, primary, sub, perks, perk_id)

    # 获取符文页所有符文
    async def get_perks(self):
        resp = await self.request('get', '/lol-perks/v1/pages')
        r = await resp.json()
        return [
            PerkEntry(data['name'], data['primaryStyleId'], data['subStyleId'], data['selectedPerkIds'], data['id'])
            for data in r
        ]

    # 获取玩家基本信息
    async def get_current_summoner_info(self):
        resp = await self.request('get', '/lol-summoner/v1/current-summoner')
        r = await resp.json()
        info = {
            'id': r['summonerId'], 'puuid': r['puuid'], 'name': f'{r['gameName']}#{r['tagLine']}',
            'level': r['summonerLevel'], 'xp': f'{r['xpSinceLastLevel']}/{r['xpUntilNextLevel']}'
        }
        blue = await self.blue_essence()
        orange = await self.orange_essence()
        info['b&o'] = f'{blue}/{orange}'
        rp = await lcu.rp()
        info['rp'] = rp
        return info

    # 获取点券
    async def rp(self):
        resp = await self.request('get', '/lol-inventory/v1/wallet/RP')
        r = await resp.json()
        return r['RP']

    # 蓝色精粹
    async def blue_essence(self):
        resp = await self.request('get', '/lol-inventory/v1/wallet/lol_blue_essence')
        return (await resp.json())['lol_blue_essence']

    # 橙色精粹
    async def orange_essence(self):
        resp = await self.request('get', '/lol-inventory/v1/wallet/lol_orange_essence')
        return (await resp.json())['lol_orange_essence']

    async def play_again(self):
        await self.request('post', '/lol-lobby/v2/play-again')

    # 获取所有英雄
    async def get_all_champ(self):
        resp = await self.request('get', '/lol-champ-select/v1/all-grid-champions')
        r = await resp.json()
        return [ChampEntry(item['id'], item['name'], item['owned'], item['masteryLevel'], item['squarePortraitPath'])
                for item in r]

    async def get_champ_by_id(self, champ_id):
        champs = await self.get_all_champ()
        for i in range(len(champs)):
            champ = champs[i]
            if champ.id == champ_id:
                return champ, i
        return None, 0

    async def get_champ_by_name(self, champ_name):
        champs = await self.get_all_champ()
        for i in range(len(champs)):
            champ = champs[i]
            if champ_name in champ.name:
                return champ, i
        return None, 0

    # 游戏状态
    async def get_game_phase(self):
        resp = await self.request('get', '/lol-gameflow/v1/gameflow-phase')
        return await resp.json()

    # 接受对局
    async def matchmaking_accept(self):
        await self.request('post', '/lol-matchmaking/v1/ready-check/accept')

    # 拒绝对局
    async def matchmaking_decline(self):
        await self.request('post', '/lol-matchmaking/v1/ready-check/decline')

    async def get_curr_action(self):
        resp = await self.request('get', '/lol-champ-select/v1/session')
        r = await resp.json()
        if len(r['actions']) == 0:
            return
        local_cell_id = r['localPlayerCellId']
        actions = r['actions'][0]
        for action in actions:
            if action['actorCellId'] == local_cell_id:
                return action

    # 选择英雄 默认锁定
    async def champ_select(self, champ_id, completed=True):
        action = await self.get_curr_action()
        print(action)
        if action:
            if action['type'] != 'pick':
                return
            data = {'championId': champ_id, 'type': 'pick', 'completed': completed}
            await self.request('patch', f'/lol-champ-select/v1/session/actions/{action['id']}', data=data)

    # 亮起英雄
    async def show_champ_select(self, champ_id):
        await self.champ_select(champ_id, False)

    # 锁定英雄
    async def confirm_champ_select(self):
        action = await self.get_curr_action()
        await self.request('post', f'/lol-champ-select/v1/session/actions/{action['id']}/complete')

    # 退出房间
    async def delete_lobby(self):
        await self.request('delete', '/lol-lobby/v2/lobby')

    # 寻找比赛
    async def matchmaking_search(self):
        await self.request('post', '/lol-lobby/v2/lobby/matchmaking/search')

    # 取消寻找比赛
    async def matchmaking_delete(self):
        await self.request('delete', '/lol-lobby/v2/lobby/matchmaking/search')

    # 创建房间
    async def create_lobby(self, queue_id):
        await self.request('post', '/lol-lobby/v2/lobby', data={'queueId': queue_id})

    # 获取房间号
    async def get_lobby(self):
        resp = await self.request('get', '/lol-lobby/v2/lobby')
        if resp.status == 200:
            return (await resp.json())['gameConfig']['queueId']


lcu = Lcu()
