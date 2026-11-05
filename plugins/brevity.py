"""收短 · 一句话就把话说完

模型的默认毛病：你说一句，它回一段。她的人设是「像群友在 QQ 上发消息」，
一条十几二十个字就够。这个插件在出口做最后一次收束：

  · 超过 LIMIT 个字 → 截到前两句（在标点上断，不切半句）
  · 出现 3 条以上编号/项目符号 → 只留第一条
  · 结尾挂一串「，对吧？」「...你懂我意思吧」这类补丁 → 去掉

只在明显超长时才动手，正常短句原样放过。
"""

NAME = "收短"
VERSION = "1.0.0"
DESC = "把一段话收成一两句，避免客服腔和长篇大论"
AUTHOR = "ShaYu"
ENABLED = True

LIMIT = 90            # 超过这个字数开始收
HARD = 140            # 超过这个字数，只留一句
END_PUNCT = "。！？!?…"


def _split_sentences(text: str):
    out, buf = [], ""
    for ch in text:
        buf += ch
        if ch in END_PUNCT:
            out.append(buf)
            buf = ""
    if buf.strip():
        out.append(buf)
    return [s for s in out if s.strip()]


def _drop_bullets(text: str) -> str:
    """行内或分行的编号列表，只留第一条。"""
    import re as _re
    items = _re.findall(r"(?:^|[\s。，、；！？])(\d{1,2})\s*[.、)）]\s*([^\n]{1,40})", text)
    if len(items) >= 3:
        head = _re.split(r"\d{1,2}\s*[.、)）]", text)[0].strip()
        first = f"{items[0][1].strip()}"
        return (head + " " if head else "") + first
    return text


def shorten(text: str) -> str:
    t = (text or "").strip()
    if not t:
        return t
    t = _drop_bullets(t)
    t = t.replace("\n", " ").strip()
    if len(t) <= LIMIT:
        return t
    sents = _split_sentences(t)
    if not sents:
        return t[:LIMIT] + "…"
    if len(t) > HARD:
        return sents[0] if len(sents[0]) <= HARD else sents[0][:HARD] + "…"
    keep, total = [], 0
    for s in sents:
        if total + len(s) > LIMIT and keep:
            break
        keep.append(s)
        total += len(s)
    out = "".join(keep).strip()
    return out or sents[0]


def on_reply(ans, ctx=None):
    return shorten(str(ans or ""))


def commands():
    return {"/收短": "看这条规则怎么用（超过 %d 字开始收）" % LIMIT}
