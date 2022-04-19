#!/usr/bin/python3.8
#-*- coding:utf-8 -*-

import requests, socket, logging
import hashlib, hmac, json, os, time
from datetime import datetime

#使用前请先完善以下信息，若不适用钉钉通知，则可以忽略dingtalk_webhook
secret_id = "AKIDxxxxxxxx"
secret_key = "xxxxxxxx"
domain = "example.com"
subdomain = "example"
dingtalk_webhook = "https://oapi.dingtalk.com/robot/send?access_token=xxxxxxxx"

service = "dnspod"
host = "dnspod.tencentcloudapi.com"
endpoint = "https://" + host
version = "2021-03-23"
algorithm = "TC3-HMAC-SHA256"

timestamp = int(time.time())
date = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")

# 来源  https://cloud.tencent.com/document/api/1427/56189#Python
def get_autiorization_info(service, host, algorithm, timestamp, date, params):

    # ************* 步骤 1：拼接规范请求串 *************
    http_request_method = "POST"
    canonical_uri = "/"
    canonical_querystring = ""
    ct = "application/json; charset=utf-8"
    payload = json.dumps(params)
    canonical_headers = "content-type:%s\nhost:%s\n" % (ct, host)
    signed_headers = "content-type;host"
    hashed_request_payload = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    canonical_request = (http_request_method + "\n" +
                        canonical_uri + "\n" +
                        canonical_querystring + "\n" +
                        canonical_headers + "\n" +
                        signed_headers + "\n" +
                        hashed_request_payload)
    #print(canonical_request)

    # ************* 步骤 2：拼接待签名字符串 *************
    credential_scope = date + "/" + service + "/" + "tc3_request"
    hashed_canonical_request = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
    string_to_sign = (algorithm + "\n" +
                    str(timestamp) + "\n" +
                    credential_scope + "\n" +
                    hashed_canonical_request)
    #print(string_to_sign)


    # ************* 步骤 3：计算签名 *************
    # 计算签名摘要函数
    def sign(key, msg):
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()
    secret_date = sign(("TC3" + secret_key).encode("utf-8"), date)
    secret_service = sign(secret_date, service)
    secret_signing = sign(secret_service, "tc3_request")
    signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
    #print(signature)

    # ************* 步骤 4：拼接 Authorization *************
    authorization = (algorithm + " " +
                    "Credential=" + secret_id + "/" + credential_scope + ", " +
                    "SignedHeaders=" + signed_headers + ", " +
                    "Signature=" + signature)
    #print(authorization)

    return authorization

def request_post(url, header, data):
    response = requests.post(url, data = data, headers = header)

    response = json.loads(response.text)
    return response

def get_domain_record(params):

    record_list = {}

    payload = json.dumps(params)
    authorization_info = get_autiorization_info(service, host, algorithm, timestamp, date, params)

    headers = {"Authorization" : authorization_info, "Content-Type": "application/json; charset=utf-8", "Host" : host, "X-TC-Action" : "DescribeRecordList", "X-TC-Timestamp" : str(timestamp), "X-TC-Version" :version}
    qcloud_response = request_post(endpoint, headers, payload)

    for record in qcloud_response["Response"]["RecordList"]:
        record_list[record["Type"]] = {"value" : record["Value"], "RecordId": record["RecordId"]}

    return record_list


def modfily_domain_record(params):

    payload = json.dumps(params)

    authorization_info = get_autiorization_info(service, host, algorithm, timestamp, date, params)

    headers = {"Authorization" : authorization_info, "Content-Type": "application/json; charset=utf-8", "Host" : host, "X-TC-Action" : "ModifyRecord", "X-TC-Timestamp" : str(timestamp), "X-TC-Version" :version}
    
    qcloud_response = request_post(endpoint, headers, payload)
    #print(qcloud_response)
    logging.info(qcloud_response)


def get_network_interface_ip():
    public_ip = {}
    interface_ip = os.popen("ifconfig pppoe0 | grep inet | awk '{print $2}'").read()
    interface_ip = interface_ip.split("\n")

    for ip in interface_ip:
        try:
            socket.inet_pton(socket.AF_INET, ip)
            public_ip["A"] = ip
        except:
            if ip.startswith("f") or ip == "":
                continue
            else:
                public_ip["AAAA"] = ip
    return public_ip

def dingmessage(ip):
    date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    header = {
        "Content-Type": "application/json",
        "Charset": "UTF-8"
    }
    tex = f"From: Opnesense Router\nDate: {date}\nCurrent IP: {ip}"
    message ={
        "msgtype": "text",
        "text": {
            "content": tex
        },
        "at": {
            "isAtAll": False
        }
    }
    message_json = json.dumps(message)
    info = requests.post(url = dingtalk_webhook, data = message_json, headers = header)
    logging.info(info.text)

if __name__ == "__main__":
    logging.basicConfig(filename='/var/log/ddns.log', format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s', level=logging.DEBUG, filemode='a')

    try:
        current_record = get_domain_record({"Domain":domain, "Subdomain":subdomain})

        pppoe_ip = get_network_interface_ip()

        for record_type in current_record:
            if current_record[record_type]["value"] != pppoe_ip[record_type]:
                logging.info("\033[1;33m " + record_type + " Record Need To Be Changed\033[0m")

                modfily_body = {"Domain":domain, "RecordType": record_type, "RecordLine": "默认", "Value": pppoe_ip[record_type], "RecordId": current_record[record_type]["RecordId"], "SubDomain": subdomain, "TTL": 600}
            
                logging.info(modfily_body)
                modfily_domain_record(modfily_body)

                #如果不需要钉钉通知可以取消注释掉下面这个（记得完善钉钉 WebHook)
                #dingmessage(pppoe_ip[record_type])
            
            else:
                logging.info("\033[1;34m" + record_type + " IP Record Are The Same\033[0m")

    except Exception as e:
        logging.warning("\033[1;31m ERROR \033[0m")
        logging.warning(e)
