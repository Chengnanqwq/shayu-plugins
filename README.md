# 傻鱼插件商店

这是【傻鱼 ShaYu】的插件商店仓库本身：`index.json` 是索引，`plugins/*.py` 是插件本体。

面板里的「插件市场 → 商店」就是读这个仓库，公开仓库不需要登录、不需要 token。

- 主项目：[Chengnanqwq/shayu](https://github.com/Chengnanqwq/shayu)
- 本地优先：装插件只是把一个 `.py` 落到安装目录的 `plugins/`，不联网、不上传

---

## 怎么用

在傻鱼面板 →「参数设置 → 其他设置」里填：

| 键 | 值 |
|---|---|
| `store_repo` | `Chengnanqwq/shayu-plugins` |
| `store_branch` | `main` |
| `store_path` | `plugins/`（默认，可留空） |

保存后回到「插件市场」，右上会多出一个「商店 N」标签，里面就是这个仓库的插件。
点「安装」直接下载写入 `plugins/`，点「更新到 vX」换成新版；卸载只是移到 `plugins/_removed/`。

> 想换成自己的商店：fork 这个仓库，把 `store_repo` 改成 `你的名字/shayu-plugins`。
> 也可以直接填一个直链：`store_repo = https://example.com/shayu/index.json`。

---


## 怎么投稿（三种，都不用我加你权限）

| 方式 | 适合谁 | 怎么做 |
|---|---|---|
| **1. 提 PR** | 会 git | fork → 放 `plugins/xxx.py` → 改 `index.json` → 提 PR，CI 自动校验 |
| **2. 填表单** | 不想碰 git | 点 [新建 Issue](../../issues/new?template=plugin-submission.yml) 选「投稿一个插件」，把代码贴进去 |
| **3. 面板分享** | 装着傻鱼的人 | 参数里填 `store_token`（只给这个仓库 Contents 写权限），插件卡片点「分享」 |

三种方式都要过同一套校验（见 `.github/workflows/validate.yml`）：

```
只收 .py · ≤256 KB · 文件名合规 · ast.parse 通过 · 有 on_message/commands
index.json：每条必须有 id，id 不重复，path/file 必须指向真实文件
```

通过后：并进 `main` → 所有人的面板「商店」标签里立刻出现（不需要发版）。

> 我没有开「任何人可直接 push」——那样谁都能改 `index.json` 把别人的插件指到奇怪的地方。
> PR + CI 是这里唯一安全的开放方式。

## 目录约定

```
index.json                    插件列表（面板读它）
plugins/<file>.py             插件本体
.github/workflows/validate.yml PR 自动校验
```

`index.json` 里每一项：

```json
{
  "file": "memes.py",                     // 必须和 plugins/ 下的文件名一致
  "name": "表情图库",                      // 展示名
  "version": "1.1.0",                     // 和插件里的 VERSION 对齐
  "author": "ShaYu",
  "desc": "一句话说清它干什么",
  "tags": ["聊天", "娱乐"],
  "url": "https://raw.githubusercontent.com/Chengnanqwq/shayu-plugins/main/plugins/memes.py"
}
```

## 分享一个插件

**方式一：提 PR（推荐，不需要 token）**

1. fork 本仓库
2. 把插件放到 `plugins/你的插件.py`
3. 在 `index.json` 的 `plugins` 数组里加一条（`url` 指向 raw 地址）
4. 提 PR —— CI 会检查：只收 `.py`、≤256 KB、文件名规范、`ast.parse` 通过、必须有
   `on_message` 或 `commands`、index 里的条目必须都能对应到文件

**方式二：面板里点「分享」**

面板 →「参数设置」填 `store_token`（一个有写权限的 GitHub token，只需这个仓库）→
在已装插件卡片上点「分享」，会自动提交插件并更新 `index.json`。

---

## 收录标准

- 单文件 `.py`，无第三方重依赖（标准库 + `websockets` + `requests` 即可）
- 不写死本机路径（用 `Path(__file__).parent` 往上找安装目录）
- 不读、不外传用户数据；不内置任何密钥
- 出错要能优雅降级：报错别把机器人主循环带崩
- 文件名：字母数字下划线横线，不要下划线开头

## 许可

MIT，见 [LICENSE](LICENSE)。贡献者提交 PR 即表示同意以 MIT 分发。
