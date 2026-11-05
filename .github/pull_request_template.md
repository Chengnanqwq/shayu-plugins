# 提交一个插件

## 是什么

- **插件名**：
- **做了什么事**（一句话）：

## 清单

- [ ] 文件放在 `plugins/<名字>.py`，文件名只用字母数字下划线横线
- [ ] 有 `NAME` 和 `VERSION`
- [ ] 有 `on_message(ctx)` 或 `commands()`
- [ ] `index.json` 里加了对应条目（`id` / `file` / `name` / `version` / `desc` / `url`）
- [ ] 没有写死本机路径、没有密钥、没有读取用户隐私
- [ ] 出错时不会把机器人主循环带崩

## 自测

```bash
python -c "import ast,pathlib; ast.parse(pathlib.Path('plugins/你的插件.py').read_text(encoding='utf-8'))"
```

## 备注

（依赖了什么库、测过什么版本、有没有已知问题）
