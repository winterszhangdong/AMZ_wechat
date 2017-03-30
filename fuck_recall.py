#!usr/bin/env python
# -*- coding:utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import os
import re
import shutil
import time
import itchat
from itchat.content import *
import hashlib
import config

# {msg_id:(msg_from,msg_to,msg_time,msg_time_touser,msg_type,msg_content,msg_url)}
msg_dict = {}

# ClearTimeOutMsg用于清理消息字典，把超时消息清理掉
# 为减少资源占用，此函数只在有新消息动态时调用
def ClearTimeOutMsg():
    if msg_dict.__len__() > 0:
        for msgid in list(msg_dict): #由于字典在遍历过程中不能删除元素，故使用此方法
            if time.time() - msg_dict.get(msgid, None)["msg_time"] > 130.0: #超时两分钟
                item = msg_dict.pop(msgid)
                #print("超时的消息：", item['msg_content'])
                #可下载类消息，并删除相关文件
                if item['msg_type'] == "Picture" \
                        or item['msg_type'] == "Recording" \
                        or item['msg_type'] == "Video" \
                        or item['msg_type'] == "Attachment":
                    print("要删除的文件：", item['msg_content'])
                    os.remove(item['msg_content'])

# 获取保存图片的地址
def getPicUrl(file_name):
    m = hashlib.md5()
    m.update(file_name + 'winters')
    md5_code = m.hexdigest()
    pic_url = config.SERVER + ':' + config.PORT + '/' + md5_code + '/' + file_name
    print 'pic_url ------>', pic_url
    return pic_url

# 从接受的信息中获取必要的字段，处理后返回信息字典
def getSavingMsg(msg, msgType):
    mytime = time.localtime()  # 这儿获取的是本地时间
    # 获取用于展示给用户看的时间 2017/03/03 13:23:53
    msg_time_touser = mytime.tm_year.__str__() \
                      + "/" + mytime.tm_mon.__str__() \
                      + "/" + mytime.tm_mday.__str__() \
                      + " " + mytime.tm_hour.__str__() \
                      + ":" + mytime.tm_min.__str__() \
                      + ":" + mytime.tm_sec.__str__()
    msg_time = msg['CreateTime']  # 消息时间

    msg_type = msg['Type']  # 消息类型
    msg_content = None  # 根据消息类型不同，消息内容不同
    msg_url = None  # 分享类消息有url
    # 图片 语音 附件 视频，可下载消息将内容下载暂存到当前目录
    if msg['Type'] == 'Text':
        msg_content = msg['Text']
    elif msg['Type'] == 'Picture':
        msg_content = msg['FileName']
        msg['Text'](msg['FileName'])
    elif msg['Type'] == 'Card':
        msg_content = msg['RecommendInfo']['NickName'] + u" 的名片"
    elif msg['Type'] == 'Map':
        x, y, location = re.search("<location x=\"(.*?)\" y=\"(.*?)\".*label=\"(.*?)\".*",
                                   msg['OriContent']).group(1, 2, 3)
        if location is None:
            msg_content = u"纬度->" + x.__str__() + u" 经度->" + y.__str__()
        else:
            msg_content = u"" + location
    elif msg['Type'] == 'Sharing':
        msg_content = msg['Text']
        msg_url = msg['Url']
    elif msg['Type'] == 'Recording':
        msg_content = msg['FileName']
        msg['Text'](msg['FileName'])
    elif msg['Type'] == 'Attachment':
        msg_content = u"" + msg['FileName']
        msg['Text'](msg['FileName'])
    elif msg['Type'] == 'Video':
        msg_content = msg['FileName']
        msg['Text'](msg['FileName'])
    elif msg['Type'] == 'Friends':
        msg_content = msg['Text']

    if msgType == 'friendChat':
        friendUserName = msg['FromUserName']
        msg_from = itchat.search_friends(userName=friendUserName)['NickName']  # 消息发送人昵称
        saving_msg = {
            "msg_from": msg_from,
            "msg_time": msg_time,
            "msg_time_touser": msg_time_touser,
            "msg_type": msg_type,
            "msg_content": msg_content,
            "msg_url": msg_url
        }
    elif msgType == 'groupChat':
        # friendUserName = msg['ActualUserName']
        # msg_from = itchat.search_friends(userName=friendUserName)['NickName']  # 消息发送人昵称
        msg_from = msg.get('ActualNickName', u'Winters先生')
        groupName = msg['FromUserName']
        msg_group = itchat.search_chatrooms(userName=groupName).get('NickName', u'未保存到通讯录的群')
        saving_msg = {
            "msg_group": msg_group,
            "msg_from": msg_from,
            "msg_time": msg_time,
            "msg_time_touser": msg_time_touser,
            "msg_type": msg_type,
            "msg_content": msg_content,
            "msg_url": msg_url
        }
    else:
        raise Exception('传入的参数msgType不符合要求!')

    return saving_msg

# 将已撤回的消息发给文件传输助手
def SendRecalledMsg(old_msg):
    # print(old_msg_id, old_msg)
    # 如果是群消息
    if not old_msg:
        raise Exception('撤回的消息不在本地暂存的消息列表中!')
    elif old_msg.get('msg_group'):
        group_text = u'从群【' + old_msg['msg_group'] + u'】中'
    else:
        group_text = u''

    msg_send = u"您的好友：" \
               + old_msg.get('msg_from', '') \
               + u"  在 [" + old_msg.get('msg_time_touser', '') \
               + u"], " + group_text + u"撤回了一条 [" + old_msg['msg_type'] + u"] 消息, 内容如下:" \
               + old_msg.get('msg_content', '')

    if old_msg['msg_type'] == "Sharing":
        msg_send += u", 链接: " + old_msg.get('msg_url', '')
    elif old_msg['msg_type'] == 'Picture':
        shutil.move(old_msg['msg_content'], r"./static/")
        pic_url = getPicUrl(old_msg['msg_content'])
        msg_send += ' ' + pic_url
    elif old_msg['msg_type'] == 'Recording' \
            or old_msg['msg_type'] == 'Video' \
            or old_msg['msg_type'] == 'Attachment':
        msg_send += u", 存储在当前目录下Revocation文件夹中"
        shutil.move(old_msg['msg_content'], r"./static/")
        if old_msg.get('msg_group'):
            group_text = u'从群【' + old_msg['msg_group'] + u'】中'
        else:
            group_text = u''

        msg_send = u"您的好友：" \
                   + old_msg.get('msg_from', '') \
                   + u"  在 [" + old_msg.get('msg_time_touser', '') \
                   + u"], " + group_text + u"撤回了一条 ["+old_msg['msg_type'] + u"] 消息, 内容如下:" \
                   + old_msg.get('msg_content', '')
        if old_msg['msg_type'] == "Sharing":
            msg_send += u", 链接: " + old_msg.get('msg_url', '')
        elif old_msg['msg_type'] == 'Picture':
            shutil.move(old_msg['msg_content'], r"./static/")
            pic_url = getPicUrl(old_msg['msg_content'])
            msg_send += ' ' + pic_url
        elif old_msg['msg_type'] == 'Recording' \
                or old_msg['msg_type'] == 'Video' \
                or old_msg['msg_type'] == 'Attachment':
            msg_send += u", 存储在当前目录下Revocation文件夹中"
            shutil.move(old_msg['msg_content'], r"./static/")

        print 'msg_send: ---------->', msg_send
        itchat.send(msg_send, toUserName='filehelper') #将撤回消息的通知以及细节发送到文件助手

    print 'msg_send: ---------->', msg_send
    itchat.send(msg_send, toUserName='filehelper')  # 将撤回消息的通知以及细节发送到文件助手


# 将接收到的消息存放在字典中，当接收到新消息时对字典中超时的消息进行清理
# 没有注册note（通知类）消息，通知类消息一般为：红包 转账 消息撤回提醒等，不具有撤回功能
# 处理朋友消息
@itchat.msg_register([TEXT, PICTURE, MAP, CARD, SHARING, RECORDING, ATTACHMENT, VIDEO, FRIENDS],
                     isFriendChat=True)
def SaveFriendsMsg(msg):
    print 'receive message'
    msg_id = msg['MsgId']  # 消息ID

    saving_msg = getSavingMsg(msg, 'friendChat')
    # 更新字典
    # {msg_id:(msg_from,msg_time,msg_time_touser,msg_type,msg_content,msg_url)}
    msg_dict.update({msg_id: saving_msg})
    # 清理字典
    ClearTimeOutMsg()

# 处理群消息
@itchat.msg_register([TEXT, PICTURE, MAP, CARD, SHARING, RECORDING, ATTACHMENT, VIDEO, FRIENDS],
                     isGroupChat=True)
def SaveGroupsMsg(msg):
    print 'receive message'
    msg_id = msg['MsgId']  # 消息ID

    saving_msg = getSavingMsg(msg, 'groupChat')
    # 更新字典
    # {msg_id:(msg_group,msg_from,msg_time,msg_time_touser,msg_type,msg_content,msg_url)}
    msg_dict.update({msg_id: saving_msg})
    # 清理字典
    ClearTimeOutMsg()

# 收到note类消息，判断是不是撤回并进行相应操作
@itchat.msg_register([NOTE], isFriendChat=True, isGroupChat=True)
def RecalledMsg(msg):
    # print(msg)
    print msg['Text']
    # 创建可下载消息内容的存放文件夹，并将暂存在当前目录的文件移动到该文件中
    if not os.path.exists("./static/"):
        os.mkdir("./static/")

    # if re.search(r"\<replacemsg\>\<\!\[CDATA\[.*撤回了一条消息\]\]\>\<\/replacemsg\>", msg['Content']) != None:
    if re.search(u".*撤回了一条消息", msg['Text']) != None:
        if not re.search(u";msgid&gt;(.*?)&lt;/msgid", msg['Content']):
            old_msg_id = re.search(u"\<msgid\>(.*?)\<\/msgid\>", msg['Content']).group(1)
        else:
            old_msg_id = re.search(u";msgid&gt;(.*?)&lt;/msgid", msg['Content']).group(1)

        # 从暂存的消息列表中获取撤回的消息
        old_msg = msg_dict.get(old_msg_id)
        # 将撤回的消息发给自己
        SendRecalledMsg(old_msg)
        msg_dict.pop(old_msg_id)
        ClearTimeOutMsg()

if __name__ == '__main__':
    # 启动程序，并且设置二维码的保存路径
    itchat.auto_login(hotReload=True, enableCmdQR=True, picDir='./static/QR.png')
    itchat.run()
