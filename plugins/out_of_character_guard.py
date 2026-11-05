"""兜底防出戏 · 那句「作为 AI」不许发出去

模型偶尔会漏出说明书腔：作为AI、语言模型、我无法、很抱歉、我作为一个程序……
一旦发出去，人设当场就穿了。这个插件在最后一道关口把这类句子切掉，
剩下的如果空了，就换她自己的短句。

它不管内容对错，只负责「不像人说的那部分」不许出门——所以永远开着也不会误伤正常回复。
"""

NAME = "兜底防出戏"
VERSION = "1.0.0"
DESC = "回复里出现「作为AI/语言模型/我无法/很抱歉」这类说明书腔时切掉，防止人设崩"
AUTHOR = "ShaYu"
ENABLED = True

PATTERNS = (
    r"作为\s*(?:一个)?\s*(?:AI|人工智能|语言模型|助手|程序)",
    r"我\s*(?:是|只是)\s*(?:一个)?\s*(?:AI|人工智能|语言模型|助手|程序)",
    r"(?:人工)?智能助手",
    r"语言模型",
    r"我无法(?:提供|回答|协助|帮助)",
    r"我(?:不能|不可以)提供",
    r"很抱歉[，,]?\s*我",
    r"抱歉[，,]?\s*我(?:无法|不能|没有)",
    r"I'?m (?:sorry|an AI)",
    r"as an AI",
    r"我没有(?:感情|情绪|意识)",
)

FALLBACK = (
    "这话不像我说的。重新来。",
    "你听错了，我没这么讲过。",
    "刚才那句不算，我换个说法。",
    "我不是这么说话的。",
)

import re

RE = re.compile("|".join(PATTERNS))
SPLIT = re.compile(r"(?<=[。！？!?…\n])")

_STATE = {"hits": 0, "seen": 0}


def clean(text: str) -> str:
    a = (text or "").strip()
    if not a:
        return a
    if not RE.search(a):
        return a
    kept = []
    for seg in SPLIT.split(a):
        if not seg.strip():
            continue
        if RE.search(seg) and len(seg.strip("。！？!?… \n")) <= 80:
            continue
        kept.append(seg)
    out = "".join(kept).strip()
    if not out:
        out = FALLBACK[_STATE["hits"] % len(FALLBACK)]
    return out


def on_reply(ans, ctx=None):
    _STATE["seen"] += 1
    before = str(ans or "")
    after = clean(before)
    if after != before:
        _STATE["hits"] += 1
    return after


def commands():
    return {"/出戏": "看兜底挡住过几次说明书腔"}
