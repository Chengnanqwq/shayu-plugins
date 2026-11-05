"""防复读 · 别把刚说过的话再说一遍

模型聊久了容易复读：连着两三轮用同一个句式、同一句话，或者把你的话原样回敬。
这个插件在回复出口比一下最近 6 条，相似度太高就换成一句短的人话，把复读掐掉。

判定用 difflib 的相似度，不是精确匹配——「哦。你是我的。」和「哦，你是我的」
这种改个标点的复读也能抓到。
"""

import difflib

NAME = "防复读"
VERSION = "1.0.0"
DESC = "连续几轮说同一句话/同一句式时自动换掉，避免机器人复读机"
AUTHOR = "ShaYu"
ENABLED = True

THRESHOLD = 0.86      # 相似度超过这个就算复读
KEEP = 6              # 记住最近几条
MIN_LEN = 6           # 太短的不比（「哦。」「嗯。」本来就短）

_ALT = (
    "刚说过一遍了。",
    "这句我讲过了。",
    "别让我复读。",
    "换句新的：你今天还行吗。",
    "我刚说过，你听进去没。",
)

_RECENT: list[str] = []
_STATE = {"hits": 0, "seen": 0}


def _norm(s: str) -> str:
    return "".join(ch for ch in (s or "") if ch.isalnum())


def is_repeat(ans: str) -> bool:
    a = _norm(ans)
    if len(a) < MIN_LEN:
        return False
    for old in _RECENT:
        if difflib.SequenceMatcher(None, a, _norm(old)).ratio() >= THRESHOLD:
            return True
    return False


def on_reply(ans, ctx=None):
    text = str(ans or "").strip()
    if not text:
        return ans
    _STATE["seen"] += 1
    if is_repeat(text):
        _STATE["hits"] += 1
        alt = _ALT[_STATE["hits"] % len(_ALT)]
        _RECENT.append(alt)
        del _RECENT[:-KEEP]
        return alt
    _RECENT.append(text)
    del _RECENT[:-KEEP]
    return ans


def commands():
    return {"/复读": "看防复读插件抓到过几次"}
