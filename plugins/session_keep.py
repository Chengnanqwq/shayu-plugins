"""新会话主动接话 · 插件版

行为：
  对方隔了很久（默认 5 小时）又开口 = 开了新会话；
  她回完之后，如果对方没下文，就主动接一句；
  对方一直不理，最多接 N 次（默认 3）；
  对方只要**明确说不聊**（别烦我 / 不想聊 / 闭嘴 / 滚 / 我要睡了 …）就彻底停，
  冷却期（默认 6 小时）内不再主动，等他自己再来找。

只做私聊，不碰群。
"""

NAME = "新会话主动接话"
VERSION = "1.0.0"
DESC = "对方开了新会话就主动接话，直到他明确说不聊为止（私聊限定，可配间隔与次数）"
AUTHOR = "ShaYu"
ENABLED = False          # 默认关闭：会不会觉得烦，交给用户自己开
CAPS = ("timer", "notify")

import json
import pathlib
import random
import re
import time

DECLINE = re.compile(
    r"别(?:烦|发|说|吵|问了)|不想聊|不聊了|不聊这个|闭嘴|滚开|滚吧|"
    r"我要睡了|我睡了|先这样|不用回了|别回了|安静|烦死了|不想说话")

FIRST = ("在忙？刚那句还没说完呢。", "人呢，没影了？", "话说一半就跑，我又不会咬你。",
         "喂，还听着吗。", "你走神了吧。")
MORE = ("还在忙就算了，回头再说。", "我先待着，想起来再喊我。",
        "你要是睡了就不用回我了。", "不催你，就是问一句。")

_state = {"users": {}}
_file = pathlib.Path(__file__).resolve().parent / "_session_keep.json"


def _load():
    try:
        if _file.exists():
            _state["users"] = json.loads(_file.read_text(encoding="utf-8")) or {}
    except Exception:
        _state["users"] = {}


def _save():
    try:
        _file.write_text(json.dumps(_state["users"], ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception:
        pass


def _conf(api):
    def g(k, d):
        v = api.cfg(k) if hasattr(api, "cfg") else None
        return d if v in (None, "") else v
    return {
        "gap": float(g("proactive_gap_seconds", 5 * 3600)),
        "first": float(g("proactive_first_seconds", 150)),
        "every": float(g("proactive_every_seconds", 600)),
        "max": int(g("proactive_max_times", 3)),
        "chance": float(g("proactive_chance", 0.85)),
        "cooldown": float(g("proactive_decline_cooldown", 6 * 3600)),
    }


def _u(uid):
    return _state["users"].setdefault(str(uid), {"last": 0, "nag": 0, "declined": False, "declined_at": 0})


def on_message(ctx):
    """记下这一句：是不是新会话、有没有说不聊。不拦截，正常回复照走。"""
    try:
        if not hasattr(ctx, "get"):
            return False
        uid = str(ctx.get("user_id") or ctx.get("user") or "")
        text = ctx.get_text() if hasattr(ctx, "get_text") else str(ctx.get("text", ""))
        if not uid:
            return False
        api = _API_REF.get("api")
        conf = _conf(api) if api else {"gap": 5 * 3600, "cooldown": 6 * 3600}
        now = time.time()
        u = _u(uid)
        gap = now - float(u.get("last") or 0)
        u["last"] = now
        if DECLINE.search(text or ""):
            u.update({"declined": True, "declined_at": now, "nag": 0, "due": 0})
            _save()
            return False
        if u.get("declined") and (now - float(u.get("declined_at") or 0)) < conf["cooldown"]:
            _save()
            return False
        u["declined"] = False
        u["nag"] = 0
        # 回完这一句之后挂上定时（由 tick 负责）
        u["due"] = now + conf["first"]
        u["new"] = gap > conf["gap"] or gap == 0
        _save()
    except Exception as e:
        print(f"[session_keep] on_message 出错（忽略）: {e}")
    return False


_API_REF = {}


def setup(api):
    _load()
    _API_REF["api"] = api
    api.log(f"已加载，{len(_state['users'])} 个会话在跟踪")
    api.every(20, tick)


def tick(api):
    conf = _conf(api)
    now = time.time()
    for uid, u in list(_state["users"].items()):
        if u.get("declined") or not u.get("due"):
            continue
        if now < float(u["due"]):
            continue
        nag = int(u.get("nag") or 0)
        if nag >= conf["max"]:
            u["due"] = 0
            continue
        if random.random() > conf["chance"]:
            u["due"] = now + conf["every"]
            continue
        line = random.choice(FIRST if nag == 0 else MORE)
        ok = api.send(uid, line) if hasattr(api, "send") else False
        if ok:
            api.log(f"主动接话 → {uid}（第 {nag + 1} 次）")
            u["nag"] = nag + 1
            u["due"] = now + conf["every"]
        else:
            u["due"] = 0
    _save()


def commands():
    return {"/接话": "看新会话主动接话的状态（次数与间隔可配）"}


def ui_html():
    return ('<div style="position:fixed;right:16px;bottom:120px;z-index:40;padding:9px 13px;'
            'border-radius:11px;background:rgba(18,20,34,.82);color:#cfd6ff;font-size:12px;'
            'border:1px solid rgba(140,150,255,.2)">新会话主动接话：已启用</div>')
