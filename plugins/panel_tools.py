"""面板小工具 · 第一个「改应用」的插件

以前插件只能改她说什么；这个插件改的是**应用本身**：
在傻鱼面板右下角放一张小卡片，显示在线状态和记忆条数，带一个刷新按钮，
数据走它自己的接口 `/plug/panel_tools/stats`。

三个应用级钩子都在这里用上了：
  CAPS     —— 声明要 ui 和 http 权限（面板靠它决定要不要注入）
  ui_html / ui_css / ui_js —— 注入到面板的 DOM / 样式 / 脚本
  handle_http —— 插件自己的 HTTP 接口

写自己的插件时照抄这份就行。
"""

NAME = "面板小工具"
VERSION = "1.0.0"
DESC = "往面板右下角放一张状态卡片（在线状态 + 记忆条数 + 刷新），演示插件如何改应用界面"
AUTHOR = "ShaYu"
ENABLED = True

CAPS = ("ui", "http")      # 申请的能力：注入界面 + 自己的接口


def ui_html():
    return """
<div class="shayu-plug-card" id="pt-card">
  <div class="pt-head"><span class="pt-dot" id="pt-dot"></span>面板小工具</div>
  <div class="pt-row">状态：<b id="pt-online">…</b></div>
  <div class="pt-row">记忆：<b id="pt-nodes">…</b> 条</div>
  <div class="pt-row">插件：<b id="pt-plugins">…</b> 个</div>
  <button class="pt-btn" id="pt-refresh">刷新</button>
</div>
"""


def ui_css():
    return """
.shayu-plug-card{position:fixed;right:16px;bottom:16px;z-index:40;width:186px;
  padding:12px 14px;border-radius:14px;font-size:12px;line-height:1.9;
  background:rgba(18,20,34,.86);border:1px solid rgba(140,150,255,.22);
  box-shadow:0 10px 30px rgba(0,0,0,.45);backdrop-filter:blur(10px);color:#cfd6ff}
.shayu-plug-card .pt-head{font-weight:600;color:#eaf0ff;margin-bottom:6px;
  display:flex;align-items:center;gap:7px}
.shayu-plug-card .pt-dot{width:7px;height:7px;border-radius:50%;background:#5a6280}
.shayu-plug-card .pt-dot.on{background:#4be08f;box-shadow:0 0 8px #4be08f}
.shayu-plug-card .pt-row{color:#9aa4cc}
.shayu-plug-card b{color:#eaf0ff;font-weight:600}
.shayu-plug-card .pt-btn{margin-top:8px;width:100%;height:26px;border-radius:8px;cursor:pointer;
  background:rgba(120,130,255,.16);border:1px solid rgba(140,150,255,.3);
  color:#dfe6ff;font-size:12px;font-family:inherit}
.shayu-plug-card .pt-btn:hover{background:rgba(120,130,255,.3)}
"""


def ui_js():
    return """
(function () {
  var box = document.getElementById('pt-card');
  if (!box) return;
  function $(id) { return document.getElementById(id); }
  function load() {
    fetch(shayu.api('/plug/panel_tools/stats')).then(function (r) { return r.json(); })
      .then(function (d) {
        if (!d || !d.ok) return;
        $('pt-online').textContent = d.connected ? '在线' : '离线';
        $('pt-dot').className = 'pt-dot' + (d.connected ? ' on' : '');
        $('pt-nodes').textContent = d.nodes;
        $('pt-plugins').textContent = d.plugins;
      }).catch(function () { $('pt-online').textContent = '读不到'; });
  }
  $('pt-refresh').addEventListener('click', load);
  load();
  setInterval(load, 30000);
})();
"""


def handle_http(path, query=None, body=b""):
    """插件自己的接口：/plug/panel_tools/stats"""
    import json
    import pathlib

    if path in ("stats", "", "/"):
        base = pathlib.Path(__file__).resolve().parent.parent
        nodes = 0
        try:
            b = base / "brain_memory.json"
            if b.exists():
                d = json.loads(b.read_text(encoding="utf-8-sig"))
                nodes = len(d.get("nodes") or [])
        except Exception:
            pass
        try:
            plugins = len([p for p in (base / "plugins").glob("*.py")])
        except Exception:
            plugins = 0
        connected = False
        try:
            import urllib.request as ur
            with ur.urlopen(f"http://127.0.0.1:{_panel_port()}/api/status", timeout=3) as r:
                connected = bool(json.loads(r.read().decode()).get("connected"))
        except Exception:
            connected = None
        return 200, {"ok": True, "nodes": nodes, "plugins": plugins, "connected": connected}
    return 404, {"ok": False, "error": "no such path"}


def _panel_port():
    try:
        import json
        import pathlib
        cfg = json.loads((pathlib.Path(__file__).resolve().parent.parent / "config.json")
                         .read_text(encoding="utf-8-sig"))
        return int(cfg.get("panel_port") or 6200)
    except Exception:
        return 6200


def commands():
    return {"/面板": "看看面板小工具（右下角那张卡片）"}
