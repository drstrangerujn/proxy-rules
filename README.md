# proxy-rules

自用分流规则。上游跟 [v2fly/domain-list-community](https://github.com/v2fly/domain-list-community)，每天自动更新一次，再补上上游没收录的域名。

## 规则集

| 名字 | 内容 | 条数 |
|---|---|---|
| `xai-grok` | xAI / Grok / Grok Bot / X（推特） | 见文件头 |
| `apple-intelligence` | Apple Intelligence / Siri（必须走美国节点） | 见文件头 |

`xai-grok` 比上游多的：

- `grokusercontent.com`：Grok 生成的图片、文件和 MCP 沙盒，上游 `xai` 没收
- `cursorvm.com`：Grok Bot 的云电脑。Grok Bot 跑在 Cursor 上，所以 Cursor 的域名也要一起走代理（来源：[Cursor 网络白名单](https://cursor.com/docs/enterprise/network-configuration)）

## 订阅地址

国内建议用 jsDelivr，把 `<name>` 换成规则集名字：

| 客户端 | 格式 | 地址 |
|---|---|---|
| Surge / Loon / 小火箭 | classical 文本 | `https://cdn.jsdelivr.net/gh/drstrangerujn/proxy-rules@main/rules/<name>.list` |
| mihomo（Clash Meta） | classical yaml | `https://cdn.jsdelivr.net/gh/drstrangerujn/proxy-rules@main/rules/<name>.yaml` |
| mihomo | domain mrs（更省内存，无关键词规则的才有） | `https://cdn.jsdelivr.net/gh/drstrangerujn/proxy-rules@main/rules/<name>.mrs` |
| sing-box | srs | `https://cdn.jsdelivr.net/gh/drstrangerujn/proxy-rules@main/rules/<name>.srs` |

GitHub 原地址把前缀换成 `https://raw.githubusercontent.com/drstrangerujn/proxy-rules/main/rules/` 即可。

### Surge

```ini
[Rule]
RULE-SET,https://cdn.jsdelivr.net/gh/drstrangerujn/proxy-rules@main/rules/xai-grok.list,AI
```

### mihomo

```yaml
rule-providers:
  xai-grok:
    type: http
    behavior: domain
    format: mrs
    url: https://cdn.jsdelivr.net/gh/drstrangerujn/proxy-rules@main/rules/xai-grok.mrs
    path: ./ruleset/xai-grok.mrs
    interval: 86400
rules:
  - RULE-SET,xai-grok,AI
```

### sing-box

```json
{
  "tag": "xai-grok",
  "type": "remote",
  "format": "binary",
  "url": "https://cdn.jsdelivr.net/gh/drstrangerujn/proxy-rules@main/rules/xai-grok.srs"
}
```

## 出口

xAI 不对中国大陆提供服务，`xai-grok` 建议走美国、日本、德国等节点。

## 怎么加规则

改 `sources/` 下的文件，push 后 Actions 会重新生成 `rules/`：

- `sources/*.yaml`：`upstream` 填 v2fly 的文件名，`extra` 填自己补的域名
- `sources/*.list`：手写的 classical 规则（DOMAIN / DOMAIN-SUFFIX / DOMAIN-KEYWORD）

本地预览：`pip install pyyaml && python3 build.py`
