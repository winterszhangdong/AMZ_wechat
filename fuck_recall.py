#!usr/bin/python2
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

# NORMAL_MSG = [TEXT, PICTURE, MAP, CARD, SHARING, RECORDING, ATTACHMENT, VIDEO, FRIENDS]
# {msg_id:(msg_from,msg_to,msg_time,msg_time_touser,msg_type,msg_content,msg_url)}
msg_dict = {}
type_dict = {'Recording': '@fil',
             'Attachment': '@fil',
             'Video': '@vid',
             'Picture': '@img'}

# ClearTimeOutMsg用于清理消息字典，把超时消息清理掉
# 为减少资源占用，此函数只在有新消息动态时调用
def ClearTimeOutMsg():
    if not len(msg_dict):
        return

    for msgid in list(msg_dict): #由于字典在遍历过程中不能删除元素，故使用此方法
        if time.time() - msg_dict.get(msgid, None)["msg_time"] > 130.0: #超时两分钟
            item = msg_dict.pop(msgid)
            #print("超时的消息：", item['msg_content'])
            #可下载类消息，并删除相关文件
            if item['msg_type'] in ['Picture', 'Recording', 'Video', 'Attachment']:
                print "要删除的文件：", item['msg_content']
                os.remove(item['msg_content'])


# 从接受的信息中获取必要的字段，处理后返回信息字典
def getSavingMsg(msg, chatType):
    # 展示给用户的，接收消息时的本地时间 2017/03/03 13:23:53
    msg_time_touser = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
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
        msg_content = msg['RecommendInfo']['NickName'] + u' 的名片'
    elif msg['Type'] == 'Map':
        x, y, location = re.search("<location x=\"(.*?)\" y=\"(.*?)\".*label=\"(.*?)\".*",
                                   msg['OriContent']).group(1, 2, 3)
        if location is None:
            msg_content = u'纬度->' + x.__str__() + u' 经度->' + y.__str__()
        else:
            msg_content = u'' + location
    elif msg['Type'] == 'Sharing':
        msg_content = msg['Text']
        msg_url = msg['Url']
    elif msg['Type'] == 'Recording':
        msg_content = msg['FileName']
        msg['Text'](msg['FileName'])
    elif msg['Type'] == 'Attachment':
        msg_content = u'' + msg['FileName']
        msg['Text'](msg['FileName'])
    elif msg['Type'] == 'Video':
        msg_content = msg['FileName']
        msg['Text'](msg['FileName'])
    elif msg['Type'] == 'Friends':
        msg_content = msg['Text']


    # 缓存在本地的消息
    saving_msg = {
        "msg_time": msg_time,
        "msg_time_touser": msg_time_touser,
        "msg_type": msg_type,
        "msg_content": msg_content,
        "msg_url": msg_url
    }
    # 根据是否是群聊消息，消息发送人昵称的获取方式有所不同
    if chatType == 'friendChat':
        friendUserName = msg['FromUserName']
        msg_from = itchat.search_friends(userName=friendUserName)['NickName']  # 消息发送人昵称
        saving_msg["msg_from"] = msg_from
    elif chatType == 'groupChat':
        # friendUserName = msg['ActualUserName']
        # msg_from = itchat.search_friends(userName=friendUserName)['NickName']  # 消息发送人昵称
        msg_from = msg.get('ActualNickName', u'Winters先生')
        groupName = msg['FromUserName']
        msg_group = itchat.search_chatrooms(userName=groupName).get('NickName', u'未保存到通讯录的群')
        saving_msg["msg_group"] = msg_group
        saving_msg["msg_from"] = msg_from
    else:
        raise Exception('传入的参数msgFrom不符合要求!')

    return saving_msg


# 将已撤回的消息发给文件传输助手
def SendRecalledMsg(old_msg):
    # print(old_msg_id, old_msg)
    # 如果是群消息
    if not old_msg:
        raise Exception('撤回的消息不在本地暂存的消息列表中!')
    elif old_msg.get('msg_group'):
        group_name = u'#' + old_msg['msg_group'] + u'  '
    else:
        group_name = u''

    msg_send = ('新的撤回消息!\n' +
                '撤回人：' + group_name + old_msg.get('msg_from', '') + '\n' +
                '撤回时间：' + old_msg.get('msg_time_touser', '') + '\n' +
                '消息类型：' + old_msg.get('msg_type', '') + '\n' +
                '消息内容：' + old_msg.get('msg_content',''))

    # 撤回消息是分享链接
    if old_msg['msg_type'] == "Sharing":
        msg_send += '\n链接：' + old_msg.get('msg_url', '')
        itchat.send(msg_send, toUserName='filehelper')  # 将撤回消息的通知以及细节发送到文件助手
    # 撤回消息是可保存的文件类型
    elif old_msg['msg_type'] in ['Recording', 'Video', 'Attachment', 'Picture']:
        msg_send += '\n撤回文件如下⬇️'
        file_name = old_msg['msg_content']
        shutil.move(file_name, r"./recalled_file/")
        itchat.send(msg_send, toUserName='filehelper')  # 将撤回消息的通知以及细节发送到文件助手
        itchat.send(msg=type_dict[old_msg['msg_type']]+'@recalled_file/'+file_name, toUserName='filehelper')
        # file_url = getSavedFileUrl(old_msg['msg_content'])
        # msg_send += '\n文件地址：' + file_url
    # 撤回消息是普通文本消息
    else:
        itchat.send(msg_send, toUserName='filehelper')  # 将撤回消息的通知以及细节发送到文件助手

    print 'msg_send: ---------->', msg_send


# 将接收到的消息存放在字典中，当接收到新消息时对字典中超时的消息进行清理
# 没有注册note（通知类）消息，通知类消息一般为：红包 转账 消息撤回提醒等，不具有撤回功能
# 处理朋友消息
@itchat.msg_register([TEXT, PICTURE, MAP, CARD, SHARING, RECORDING, ATTACHMENT, VIDEO, FRIENDS],
                     isFriendChat=True)
def SaveFriendsMsg(msg):
    print 'received message!'
    msg_id = msg['MsgId']  # 消息ID

    saving_msg = getSavingMsg(msg, 'friendChat')
    # 更新字典
    # {msg_id:(msg_from,msg_time,msg_time_touser,msg_type,msg_content,msg_url)}
    msg_dict.update({msg_id: saving_msg})
    # 清理缓存消息列表
    ClearTimeOutMsg()


# 处理群消息
@itchat.msg_register([TEXT, PICTURE, MAP, CARD, SHARING, RECORDING, ATTACHMENT, VIDEO, FRIENDS],
                     isGroupChat=True)
def SaveGroupsMsg(msg):
    print 'received message!'
    msg_id = msg['MsgId']  # 消息ID

    saving_msg = getSavingMsg(msg, 'groupChat')
    # 更新字典
    # {msg_id:(msg_group,msg_from,msg_time,msg_time_touser,msg_type,msg_content,msg_url)}
    msg_dict.update({msg_id: saving_msg})
    # 清理缓存消息列表
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
    if re.search(u'.*撤回了一条消息', msg['Text']) is not None:
        if not re.search(u';msgid&gt;(.*?)&lt;/msgid', msg['Content']):
            old_msg_id = re.search(u'\<msgid\>(.*?)\<\/msgid\>', msg['Content']).group(1)
        else:
            old_msg_id = re.search(u';msgid&gt;(.*?)&lt;/msgid', msg['Content']).group(1)

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
