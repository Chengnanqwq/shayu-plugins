"""定时提醒 · 用插件 API 的例子

演示拓展点：注册一个每 60 秒执行一次的任务，读配置、数记忆、必要时给主人推一条。
插件不需要碰 bot 的代码，也不要知道消息怎么发——给它一个 api 就行。
"""

NAME = "定时提醒"
VERSION = "1.0.0"
DESC = "每 10 分钟看一眼：记忆涨了多少、有没有报错，需要时给主人推一条（演示 api 用法）"
AUTHOR = "ShaYu"
ENABLED = False          # 演示用，默认关闭；在面板插件列表里手动开启
CAPS = ("memory", "notify", "timer")

_last = {"nodes": 0, "t": 0}


def setup(api):
    if not hasattr(api, "every"):
        return
    api.log("已加载，开始计时")

    def tick(a):
        n = a.memory_count()
        grew = n - _last["nodes"] if _last["nodes"] else 0
        _last["nodes"] = n
        a.log(f"记忆 {n} 条（本轮 +{grew}）")
        if grew >= 30:
            a.notify(f"记忆涨了 {grew} 条，现在共 {n} 条")

    api.every(600, tick)


def commands():
    return {"/定时": "看这个演示插件在做什么"}
