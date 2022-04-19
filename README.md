# Opnsense-DNSPod-DDNS
自用 Opnsense DNSPod DDNS 脚本

读取本地 PPPoE 接口信息获取 IP 地址，支持 IPv6，使用 crontab 执行

---
## 前置条件
1. 你有腾讯云的账号
2. 你有在腾讯云上购买或是托管解析的域名
3. 你能在腾讯云账号上新建用户（如果你想用主账号ASAK的话，这一步可以省，但出于安全原因不建议这么干）
4. 你的OPNsense路由系统版本 >= 21.x

---
## 使用方法
1. 获取 DnsPod AKAS
    - 腾讯云控制台 -> 访问管理 -> 用户 -> 用户列表 -> 新建用户 -> 自定义创建
      - 可访问资源并接受消息
      - 用户名自定，备注/手机号/邮箱可选（此次无关）
      - 访问方式：编程访问
      - 授权策略：QcloudDOMAINFullAccess（你自己新建策略也可以，但不在此README范围内）
    - 注意保存 SecretId：AKIDxxxxx 及 SecretKey：xxxx
2. 在控制台上创建一个域名解析（如果已经有解析可以跳过）
    - DNS解析 DNSPod -> 我的域名 -> <你想修改的域名> -> 添加记录
      - 主机记录：你自己定
      - 记录类型：IPv4 -- A    IPv6 -- AAAA
      - 线路类型：默认（或是看你需求）
      - 记录值：目前不重要，随便写一个内网地址上去就行
      - TTL：600
3. 修改脚本（不要删除双引号）
    - secret_id 填写上面拿到的 AKID
    - secret_key 填写上面拿到的 SecretKey
    - domain 填写你刚刚添加记录的域名或是已有记录的域名
    - subdomain 填写你刚刚添加记录或是已有记录
    - dingtalk_webhook 如果你需要在每次IP地址变化后有一个钉钉机器人通知，完善此项，并取消后面 `dingmessage(pppoe_ip[record_type])` 部分注释
4. 上传到 OPNsense 中（SSH登陆），然后放到一个不会删除的地方（我放在了 /usr/local/ddns/ddns.py 这里）
    - 上传后尝试执行下 `python3 /usr/local/ddns/ddns.py`, 并注意查看腾讯云控制台的记录是否有更改
    - 日志文件在 `/var/log/ddns.log`
5. 修改crontab（修改 /etc/crontab ，不要使用 crontab -e，后者重启系统后会恢复修改前的状态）
    - 在最后另起一行添加以下记录
    - `*	*	*	*	*	root	python3 /usr/local/ddns/ddns.py`

---
## Tips
1. 修改 /etc/crontab 文件的方式在系统更新后会失效，需要重新添加记录
