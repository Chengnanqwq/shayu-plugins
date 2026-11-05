"""时间感知 · 本地报时，不花模型

问她「现在几点」「今天周几」「还有几天到周末」，不用调模型，直接答——
快、免费、也不会胡说时间。

顺便还能算几个她常被问到的：
  · 现在几点 / 今天几号 / 今天周几
  · 距周末还有几天
  · 今年还剩多少天
  · 现在该不该睡（配合她的作息人设，23 点之后会劝一句）
"""

import datetime as _dt

NAME = "时间感知"
VERSION = "1.0.0"
DESC = "本地报时/报日期/算周末倒计时，不消耗模型额度"
AUTHOR = "ShaYu"
ENABLED = True

WEEK = ("周一", "周二", "周三", "周四", "周五", "周六", "周日")

_RE_TIME = ("几点", "什么时候了", "现在时间", "几时")
_RE_DATE = ("几号", "今天日期", "今天是几月", "什么日子")
_RE_WEEK = ("周几", "星期几")
_RE_WEEKEND = ("周末还有", "还有几天到周末", "还要多久到周末", "离周末")
_RE_YEAR = ("今年还剩", "今年还有多少天", "离过年还有")


def _now():
    return _dt.datetime.now()


def answer(text: str) -> str:
    t = (text or "").strip()
    if not t:
        return ""
    now = _now()
    if any(k in t for k in _RE_TIME):
        h, m = now.hour, now.minute
        core = f"{h} 点 {m:02d} 分"
        if h >= 23 or h < 5:
            return core + "，这个点还不睡？"
        if 5 <= h < 9:
            return core + "，起这么早。"
        return core + "。"
    if any(k in t for k in _RE_WEEK):
        return f"今天{now.strftime('%m月%d日')}，{WEEK[now.weekday()]}。"
    if any(k in t for k in _RE_DATE):
        return f"今天 {now.strftime('%Y年%m月%d日')}。"
    if any(k in t for k in _RE_WEEKEND):
        left = (5 - now.weekday()) % 7          # 到周六
        return "已经周末了。" if left == 0 and now.weekday() >= 5 else f"还有 {left} 天到周末。"
    if any(k in t for k in _RE_YEAR):
        end = _dt.date(now.year, 12, 31)
        return f"今年还剩 {(end - now.date()).days} 天。"
    return ""


def on_message(ctx):
    ans = answer(ctx.get_text() if hasattr(ctx, "get_text") else str(ctx.get("text", "")))
    return ans or None


def commands():
    return {
        "/几点": "现在几点（本地时间）",
        "/周几": "今天周几",
        "/周末": "还有几天到周末",
    }
