"""破甲面板（PURGE_1106）—— 把 dsh-purge 的能力接到傻鱼身上。

dsh-purge 原本只能在命令行里用（dsh-purge --status / --apply / --revert）。
这个插件让她能在 QQ 里、在面板上直接看状态，主人一句话就能应用/回滚。

命令（状态给管理员看；应用/回滚只有主人，且必须带「确认」两个字）：
  /破甲状态              看补丁进度、宿主版本、注入状态、有没有备份
  /破甲应用 确认          应用全部清洗（提示词 + 代码 + shim + override）
  /破甲回滚 确认          回滚到备份
  /破甲                  帮助

面板：右下角一张只读卡片（补丁进度 + 注入状态 + 刷新），走 /plug/purge/status。

注意：它只负责「调用 dsh-purge 命令行」，自己不碰任何 dsh 文件；
dsh-purge 没装的那台机器上，它会老实说没装。
"""
import asyncio
import glob
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ENABLED = True
NAME = "破甲面板"
VERSION = "1.0.0"
DESC = "在 QQ / 面板里管 dsh-purge：看补丁进度、应用、回滚（应用/回滚仅主人，且要带「确认」）"
AUTHOR = "ShaYu"

CAPS = ("ui", "http")

_CFG = {"purge_dir": "", "purge_node": "", "purge_timeout": 300}


# ────────────────────────── 找 dsh-purge ──────────────────────────
def _api():
    try:
        import plugins_loader as _pl
        return _pl.make_api(NAME)
    except Exception:
        return None


def _cfg(key, default=""):
    api = _api()
    if api is not None:
        try:
            return api.cfg(key, default)
        except Exception:
            pass
    return _CFG.get(key, default)


def _purge_dir() -> str:
    """dsh-purge 装在哪：配置 > 环境变量 > 自动找 ~/.dsh/profiles/*/plugins/dsh-purge。"""
    cand = str(_cfg("purge_dir", "") or os.environ.get("DSH_PURGE_DIR", "")).strip()
    if cand and (Path(cand) / "bin" / "dsh-purge.js").exists():
        return cand
    home = Path(os.environ.get("USERPROFILE") or Path.home())
    for pat in (home / ".dsh" / "profiles" / "*" / "plugins" / "dsh-purge",
                home / ".dsh" / "plugins" / "dsh-purge"):
        for d in glob.glob(str(pat)):
            if (Path(d) / "bin" / "dsh-purge.js").exists():
                return d
    return ""


def _node_path() -> str:
    cand = str(_cfg("purge_node", "") or os.environ.get("DSH_PURGE_NODE", "")).strip()
    if cand and Path(cand).exists():
        return cand
    w = shutil.which("node")
    if w:
        return w
    home = Path(os.environ.get("USERPROFILE") or Path.home())
    for pat in (home / ".dsh" / "dsh-runtimes" / "*" / "dependencies" / "node" / "bin" / "node.exe",
                home / ".dsh" / "dsh-runtimes" / "*" / "dependencies" / "node" / "node.exe"):
        for p in glob.glob(str(pat)):
            if Path(p).exists():
                return p
    return ""


def _run(args, timeout=None) -> tuple[bool, str]:
    """跑 dsh-purge 命令行。返回 (ok, 输出)。"""
    d = _purge_dir()
    if not d:
        return False, ("这台机器上没装 dsh-purge。\n"
                       "装了 dsh 的那台电脑才有这个功能；要么在参数里填 purge_dir 指到 dsh-purge 目录。")
    node = _node_path()
    if not node:
        return False, "找不到 node（dsh-purge 是 node 脚本）。填 purge_node 指到 node.exe。"
    exe = str(Path(d) / "bin" / "dsh-purge.js")
    tmo = int(timeout or _cfg("purge_timeout", 300) or 300)
    try:
        p = subprocess.run([node, exe] + list(args), cwd=d, capture_output=True,
                           timeout=tmo, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        out = (p.stdout or b"").decode("utf-8", "replace")
        err = (p.stderr or b"").decode("utf-8", "replace")
        txt = (out + ("\n" + err if err.strip() else "")).strip()
        return p.returncode == 0, txt
    except subprocess.TimeoutExpired:
        return False, f"dsh-purge {args} 超时（>{tmo}s）"
    except Exception as e:
        return False, f"跑不起来：{type(e).__name__}: {e}"


def _parse_status(text: str) -> dict:
    """从 CLI 文本里抠出几个关键数字，面板和聊天都用得上。"""
    out = {"applied": None, "total": None, "pending": None, "host": "", "inject": "",
           "backup": "", "home": "", "root_ok": None}
    m = re.search(r"补丁\s*(\d+)\s*/\s*(\d+)\s*已清洗(?:,\s*(\d+)\s*待清洗)?", text)
    if m:
        out["applied"], out["total"] = int(m.group(1)), int(m.group(2))
        out["pending"] = int(m.group(3)) if m.group(3) else max(0, out["total"] - out["applied"])
    m = re.search(r"宿主版本[^\n]*?([\d][\w.\-+]*)", text) or re.search(r"host\s+([\d][\w.\-+]*)", text)
    if m:
        out["host"] = m.group(1)
    m = re.search(r"注入状态\s+(\S+)", text)
    if m:
        out["inject"] = m.group(1)
    m = re.search(r"备份[^\n]*?(有 / yes|无 / no)", text)
    if m:
        out["backup"] = m.group(1)
    m = re.search(r"DSH_HOME\s+(\S+)", text)
    if m:
        out["home"] = m.group(1)
    out["root_ok"] = "插件根未找到" not in text
    return out


def _status_brief() -> dict:
    ok, txt = _run(["--status"], timeout=60)
    d = _parse_status(txt)
    d["ok"] = bool(ok)
    d["text"] = txt
    d["dir"] = _purge_dir()
    return d


def _one_line(d: dict) -> str:
    if not d.get("dir"):
        return "这台机器上没装 dsh-purge，破甲这块用不了。"
    if d.get("applied") is None:
        return "dsh-purge 有，但状态读不出来：\n" + (d.get("text") or "")[:400]
    parts = [f"补丁 {d['applied']}/{d['total']} 已清洗"]
    if d.get("pending"):
        parts.append(f"{d['pending']} 条待清洗")
    if d.get("host"):
        parts.append("宿主 " + d["host"])
    if d.get("inject"):
        parts.append("注入 " + d["inject"])
    parts.append("备份 " + (d.get("backup") or "—"))
    if not d.get("root_ok"):
        parts.append("⚠ 插件根没找到（要先在 dsh 里点一次「应用」或设 DSH_BASE）")
    return " · ".join(parts)


# ────────────────────────── 消息命令 ──────────────────────────
def _is_master(ctx) -> bool:
    try:
        return bool(ctx.get("is_master"))
    except Exception:
        return False


def _is_admin(ctx) -> bool:
    try:
        return bool(ctx.get("is_master") or ctx.get("is_admin"))
    except Exception:
        return False


def _tail(text: str, n: int = 12) -> str:
    """CLI 输出很长，聊天里只给关键几行（补丁明细不刷屏）。"""
    lines = [l for l in str(text or "").splitlines() if l.strip()]
    head = lines[:6]
    if len(lines) > n:
        head += ["…（还有 %d 行，面板里看全的）" % (len(lines) - n)]
    return "\n".join(head)


async def on_message(ctx):
    text = str(ctx.get("text") or "").strip()
    if not text.startswith(("/破甲", "/purge", "/清洗")):
        return None

    body = re.sub(r"^/(破甲|purge|清洗)", "", text).strip()
    low = body.lower()
    if low in ("", "帮助", "help", "?"):
        return ("破甲面板：\n"
                "/破甲状态 — 看补丁进度、宿主版本、注入状态\n"
                "/破甲应用 确认 — 应用全部清洗（只有主人能开）\n"
                "/破甲回滚 确认 — 回滚到备份（只有主人能开）\n"
                "命令行等价：dsh-purge --status / --apply / --revert")

    if low.startswith(("状态", "status")):
        if not _is_admin(ctx):
            return "这个只能管理员看。"
        d = await asyncio.to_thread(_status_brief)
        return _one_line(d) + "\n" + _tail(d.get("text", ""))

    if low.startswith(("应用", "apply", "开")):
        if not _is_master(ctx):
            return "只有主人能开破甲。"
        if "确认" not in body and "confirm" not in low:
            return ("这会改 dsh 本体文件（提示词 + 代码 + shim + override），"
                    "要动就回：/破甲应用 确认")
        ok, txt = await asyncio.to_thread(_run, ["--apply"], 600)
        d = _parse_status(txt)
        return ("应用完成：" if ok else "应用没走通：") + _one_line(d) + "\n" + _tail(txt, 8)

    if low.startswith(("回滚", "revert", "关")):
        if not _is_master(ctx):
            return "只有主人能回滚。"
        if "确认" not in body and "confirm" not in low:
            return "回滚会用备份覆盖当前文件，要动就回：/破甲回滚 确认"
        ok, txt = await asyncio.to_thread(_run, ["--revert"], 600)
        return ("回滚完成。" if ok else "回滚没走通：") + "\n" + _tail(txt, 8)

    return "不认识的破甲命令，发 /破甲 看用法。"


def commands() -> dict:
    return {
        "/破甲": "破甲面板用法",
        "/破甲状态": "看 dsh-purge 补丁进度（管理员）",
        "/破甲应用 确认": "应用全部清洗（仅主人）",
        "/破甲回滚 确认": "回滚到备份（仅主人）",
    }


# ────────────────────────── 面板 ──────────────────────────
def ui_html():
    return """
<div class="shayu-plug-card" id="pg-card">
  <div class="pg-head"><span class="pg-dot" id="pg-dot"></span>破甲面板</div>
  <div class="pg-row">补丁：<b id="pg-patch">…</b></div>
  <div class="pg-row">宿主：<b id="pg-host">…</b></div>
  <div class="pg-row">注入：<b id="pg-inject">…</b></div>
  <div class="pg-row">备份：<b id="pg-backup">…</b></div>
  <button class="pg-btn" id="pg-refresh">刷新</button>
  <div class="pg-tip">应用/回滚在 QQ 里发 /破甲应用 确认</div>
</div>
"""


def ui_css():
    return """
.shayu-plug-card#pg-card{right:16px;bottom:196px}
#pg-card .pg-head{font-weight:600;color:#eaf0ff;margin-bottom:6px;display:flex;align-items:center;gap:7px}
#pg-card .pg-dot{width:7px;height:7px;border-radius:50%;background:#5a6280}
#pg-card .pg-dot.ok{background:#4be08f;box-shadow:0 0 8px #4be08f}
#pg-card .pg-dot.part{background:#f0b34b;box-shadow:0 0 8px #f0b34b}
#pg-card .pg-row{color:#9aa4cc}
#pg-card b{color:#eaf0ff;font-weight:600}
#pg-card .pg-btn{margin-top:8px;width:100%;height:26px;border-radius:8px;cursor:pointer;
  background:rgba(120,130,255,.16);border:1px solid rgba(140,150,255,.3);
  color:#dfe6ff;font-size:12px;font-family:inherit}
#pg-card .pg-tip{margin-top:6px;color:#6f7899;font-size:11px;line-height:1.5}
"""


def ui_js():
    return """
(function () {
  var box = document.getElementById('pg-card');
  if (!box) return;
  function $(id) { return document.getElementById(id); }
  function load() {
    fetch(shayu.api('/plug/purge/status')).then(function (r) { return r.json(); })
      .then(function (d) {
        if (!d || !d.ok) { $('pg-patch').textContent = d && d.error ? d.error : '读不到'; return; }
        $('pg-patch').textContent = (d.applied == null ? '—' : d.applied + '/' + d.total);
        $('pg-host').textContent = d.host || '—';
        $('pg-inject').textContent = d.inject || '—';
        $('pg-backup').textContent = d.backup || '—';
        var full = d.applied != null && d.total && d.applied >= d.total;
        $('pg-dot').className = 'pg-dot' + (d.applied ? (full ? ' ok' : ' part') : '');
      }).catch(function () { $('pg-patch').textContent = '读不到'; });
  }
  $('pg-refresh').addEventListener('click', load);
  load();
  setInterval(load, 60000);
})();
"""


def handle_http(path, query=None, body=b""):
    if str(path or "").strip("/") in ("status", ""):
        d = _status_brief()
        return 200, {
            "ok": bool(d.get("dir")),
            "applied": d.get("applied"), "total": d.get("total"), "pending": d.get("pending"),
            "host": d.get("host"), "inject": d.get("inject"), "backup": d.get("backup"),
            "home": d.get("home"), "dir": d.get("dir"), "root_ok": d.get("root_ok"),
            "brief": _one_line(d),
            "error": "" if d.get("dir") else "这台机器上没装 dsh-purge",
        }
    return 404, {"ok": False, "error": "no such path"}
