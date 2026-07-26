# best-cf-ips-personal

这是基于 [LancelotRar/best-cf-ips](https://github.com/LancelotRar/best-cf-ips)
建立的个人自用迁移版本。

- 原作者：LancelotRar
- 参考提交：`2c43ab86b2403a9b60abb94ac0a72245ca8717e0`
- 本仓库不代表原作者官方版本，也不冒充原作者
- 地址数据来自公开第三方来源，各来源仍受其自身规则和使用条件约束

## 地址池

公开 Raw 文件：

```text
https://raw.githubusercontent.com/254057007-eng/best-cf-ips-personal/main/best-cf-ipv4.txt
```

输出格式：

```text
bestips updated at#YYYY-MM-DD HH:MM
IPv4:443#国家代码
```

时间使用北京时间。每个 IPv4 只保留一次，端口统一为 443。

## 采集方式

1. 依次获取 10 个公开来源的原始网页、JSON 或文本；
2. 使用 IPv4 正则提取候选地址；
3. 使用 Python 标准 `ipaddress` 库验证 IPv4；
4. 使用集合按 IPv4 去重；
5. 通过 `https://ipinfo.io/{ip}/country` 并发查询国家代码；
6. 地区查询失败时写入 `XX`，不删除对应 IPv4；
7. 使用临时文件写入并原子替换正式文件；
8. 稳定排序，减少内容未变化时的无意义提交。

详细来源和第三方说明见 [THIRD_PARTY.md](THIRD_PARTY.md)。

本项目不解析域名、节点协议、订阅、UUID、Host、SNI 或路径，不执行测速、
TCP、TLS、WebSocket 或代理连通性测试。

## 自动更新

GitHub Actions 每 3 小时运行一次，也支持手动执行：

- 先运行单元测试；
- 再采集和标注地址；
- 验证格式、数量、固定端口、重复项及非公网地址；
- 仅在 `best-cf-ipv4.txt` 内容变化时提交。

工作流只申请 `contents: write`，不使用仓库 Secret，不部署 GitHub Pages、
Cloudflare Pages 或 Worker。

## 本地运行

```text
python -m pip install -r requirements.txt
python -m unittest discover -s tests -p "test_*.py" -v
python scripts/best-cf-ipv4-collector.py
python scripts/validate_output.py best-cf-ipv4.txt --min-count 50
```
