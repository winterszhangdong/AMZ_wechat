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
import logging.config
import config
import sqlite3
import datetime

# NORMAL_MSG = [TEXT, PICTURE, MAP, CARD, SHARING, RECORDING, ATTACHMENT, VIDEO, FRIENDS]
# {msg_id:(msg_from,msg_to,msg_time,msg_time_touser,msg_type,msg_content,msg_url)}
msg_dict = {}
type_dict = {'Recording': '@fil',
             'Attachment': '@fil',
             'Video': '@vid',
             'Picture': '@img'}
download_folder = config.download_folder
qr_folder = config.qr_folder
recalled_file_folder = config.recalled_file_folder
status_storage_folder = config.status_storage_folder
pid_file = config.pid_file

identifier = None

# log配置文件
logging.config.fileConfig('logging.conf')
# 创建logger
logger = logging.getLogger('wechatLogger')


# 记录正在运行进程的pid
def pid_logger(pid, mode='a'):
    info_text = ('追加pid：%d' % pid) if os.path.exists(pid_file) else ('pid.txt文件不存在，创建并追加pid：%d' % pid)
    # if os.path.exists(pid_file):
    #     logger.info('追加pid：' + pid)
    # else:
    #     logger.info('pid.txt文件不存在，创建并追加pid：' + pid)
    logger.info(info_text)

    with open('./pid.txt', mode) as f:
        f.write('%d\n' % pid)


# 获取下载文件的文件路径
def get_download_path(filename):
    global identifier

    # return '{dfolder}{id}_{filename}'.format(dfolder=download_folder, id=identifier, filename=filename)
    return download_folder + identifier + '_' + filename


# _clear_timeout_msg用于清理消息字典，把超时消息清理掉
# 为减少资源占用，此函数只在有新消息动态时调用
def _clear_timeout_msg():
    if not len(msg_dict):
        return

    for msgid in list(msg_dict):
        if time.time() - msg_dict.get(msgid, None)["msg_time"] > 180.0:  # 超时三分钟
            item = msg_dict.pop(msgid)
            # print("超时的消息：", item['msg_content'])
            # 可下载类消息，并删除相关文件
            if item['msg_type'] in ['Picture', 'Recording', 'Video', 'Attachment']:
                file_path = get_download_path(item['msg_content'])
                if os.path.exists(file_path):
                    # print "要删除的文件：", item['msg_content']
                    logger.debug('要删除的文件：%s' % file_path)
                    os.remove(item['msg_content'])
                else:
                    # print '要删除的文件不存在：', item['msg_content']
                    logger.debug('要删除的文件不存在：%s' % file_path)


# 从接受的信息中获取必要的字段，处理后返回信息字典
def _get_saving_msg(msg, chat_type):
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
        msg['Text'](get_download_path(msg['FileName']))
    elif msg['Type'] == 'Card':
        msg_content = msg['RecommendInfo']['NickName'].encode('ascii', 'ignore') + ' 的名片'
    elif msg['Type'] == 'Map':
        x, y, location = re.search("<location x=\"(.*?)\" y=\"(.*?)\".*label=\"(.*?)\".*",
                                   msg['OriContent'].encode('ascii', 'ignore')).group(1, 2, 3)
        msg_content = location if location else ''.join(['纬度->', x, ' ', '经度->', y])
    elif msg['Type'] == 'Sharing':
        msg_content = msg['Text']
        msg_url = msg['Url']
    elif msg['Type'] == 'Recording':
        msg_content = msg['FileName']
        msg['Text'](get_download_path(msg['FileName']))
    elif msg['Type'] == 'Attachment':
        msg_content = '' + msg['FileName']
        msg['Text'](get_download_path('' + msg['Filename']))
    elif msg['Type'] == 'Video':
        msg_content = msg['FileName']
        msg['Text'](get_download_path(msg['Filename']))
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
    if chat_type == 'friendChat':
        friend_name = msg['FromUserName']
        msg_from = itchat.search_friends(userName=friend_name)['NickName']  # 消息发送人昵称
        saving_msg["msg_from"] = msg_from
    elif chat_type == 'groupChat':
        # friendUserName = msg['ActualUserName']
        # msg_from = itchat.search_friends(userName=friendUserName)['NickName']  # 消息发送人昵称
        msg_from = msg.get('ActualNickName', u'Winters先生').encode('ascii', 'ignore')
        group_name = msg['FromUserName']
        msg_group = itchat.search_chatrooms(userName=group_name).get('NickName', u'未保存到通讯录的群').encode('ascii', 'ignore')
        saving_msg["msg_group"] = msg_group
        saving_msg["msg_from"] = msg_from
    else:
        raise Exception('传入的参数msgFrom不符合要求!')

    return saving_msg


# 将已撤回的消息发给文件传输助手
def _send_recalled_msg(old_msg):
    # print(old_msg_id, old_msg)
    global identifier

    # 如果是群消息
    if not old_msg:
        logger.error('撤回的消息不在本地暂存的消息列表中!')
    elif old_msg.get('msg_group'):
        group_name = '#' + old_msg['msg_group'] + '  '
    else:
        group_name = ''

    msg_send = ('新的撤回消息!\n' +
                '撤回人：' + group_name + old_msg.get('msg_from', '') + '\n' +
                '撤回时间：' + old_msg.get('msg_time_touser', '') + '\n' +
                '消息类型：' + old_msg.get('msg_type', '') + '\n' +
                '消息内容：' + old_msg.get('msg_content', ''))

    # 撤回消息是分享链接
    if old_msg['msg_type'] == "Sharing":
        msg_send += '\n链接：' + old_msg.get('msg_url', '')
        itchat.send(msg_send, toUserName='filehelper')  # 将撤回消息的通知以及细节发送到文件助手
    # 撤回消息是可保存的文件类型
    elif old_msg['msg_type'] in ['Recording', 'Video', 'Attachment', 'Picture']:
        msg_send += '\n撤回文件如下⬇️'
        file_name = old_msg['msg_content']
        shutil.move(get_download_path(file_name), recalled_file_folder)
        itchat.send(msg_send, toUserName='filehelper')  # 将撤回消息的通知以及细节发送到文件助手
        msg_file = type_dict[old_msg['msg_type']] + '@recalled_file/' + identifier + '_' + file_name
        itchat.send(msg=msg_file, toUserName='filehelper')
        # file_url = getSavedFileUrl(old_msg['msg_content'])
        # msg_send += '\n文件地址：' + file_url
    # 撤回消息是普通文本消息
    else:
        itchat.send(msg_send, toUserName='filehelper')  # 将撤回消息的通知以及细节发送到文件助手

    # print 'msg_send: ---------->', msg_send
    logger.debug('msg_send: ---------->' + msg_send)


# 登录完成后在数据库中插入一条用户数据
def _login_callback():
    # 清除二维码文件
    qr_dir = qr_folder + identifier + '.jpg'
    if os.path.exists(qr_dir):
        os.remove(qr_dir)
        logger.debug('清除二维码文件：%s' % qr_dir)

    # insert or update
    time_now = str(datetime.datetime.fromtimestamp(time.time()))
    ins_up_sql = "INSERT OR REPLACE INTO USER (username, isLogin, pid, lastLogin) VALUES ('%s', 1, %d, '%s')" % (
        identifier, os.getpid(), time_now)
    conn = sqlite3.connect(config.db)
    conn.execute(ins_up_sql)
    conn.commit()
    conn.close()

    logger.info('用户：%s 成功登陆' % identifier)


def _exit_callback():
    time_now = str(datetime.datetime.fromtimestamp(time.time()))
    logoff_sql = "UPDATE USER SET isLogin = 0, pid = -1, lastLogoff = '%s' WHERE username = '%s'" % (
        time_now, identifier)
    conn = sqlite3.connect(config.db)
    conn.execute(logoff_sql)
    conn.commit()
    conn.close()

    logger.info('用户：%s 退出' % identifier)


# 判断当前用户是否已经登陆
def _is_login():
    is_login_sql = "SELECT isLogin FROM USER WHERE USERNAME = '%s'" % identifier
    conn = sqlite3.connect(config.db)
    cursor = conn.execute(is_login_sql)
    is_login = cursor.fetchone()[0]
    conn.close()

    return True if is_login == 1 else False


# 将接收到的消息存放在字典中，当接收到新消息时对字典中超时的消息进行清理
# 没有注册note（通知类）消息，通知类消息一般为：红包 转账 消息撤回提醒等，不具有撤回功能
# 处理朋友消息
@itchat.msg_register([TEXT, PICTURE, MAP, CARD, SHARING, RECORDING, ATTACHMENT, VIDEO, FRIENDS],
                     isFriendChat=True)
def save_friends_msg(msg):
    msg_id = msg['MsgId']  # 消息ID

    saving_msg = _get_saving_msg(msg, 'friendChat')
    # 更新字典
    # {msg_id:(msg_from,msg_time,msg_time_touser,msg_type,msg_content,msg_url)}
    msg_dict.update({msg_id: saving_msg})
    # 清理缓存消息列表
    _clear_timeout_msg()


# 处理群消息
@itchat.msg_register([TEXT, PICTURE, MAP, CARD, SHARING, RECORDING, ATTACHMENT, VIDEO, FRIENDS],
                     isGroupChat=True)
def save_groups_msg(msg):
    msg_id = msg['MsgId']  # 消息ID

    saving_msg = _get_saving_msg(msg, 'groupChat')
    # 更新字典
    # {msg_id:(msg_group,msg_from,msg_time,msg_time_touser,msg_type,msg_content,msg_url)}
    msg_dict.update({msg_id: saving_msg})
    # 清理缓存消息列表
    _clear_timeout_msg()


# 收到note类消息，判断是不是撤回并进行相应操作
@itchat.msg_register([NOTE], isFriendChat=True, isGroupChat=True)
def recalled_msg(msg):
    logger.debug(msg['Text'])
    # 创建可下载消息内容的存放文件夹，并将暂存在当前目录的文件移动到该文件中
    if not os.path.exists(download_folder):
        os.mkdir(download_folder)

    if re.search(u'.*撤回了一条消息', msg['Text']) is not None:
        if not re.search(u';msgid&gt;(.*?)&lt;/msgid', msg['Content']):
            old_msg_id = re.search(u'\<msgid\>(.*?)\<\/msgid\>', msg['Content']).group(1)
        else:
            old_msg_id = re.search(u';msgid&gt;(.*?)&lt;/msgid', msg['Content']).group(1)

        # 从暂存的消息列表中获取撤回的消息
        old_msg = msg_dict.get(old_msg_id)
        # 将撤回的消息发给自己
        _send_recalled_msg(old_msg)
        msg_dict.pop(old_msg_id)
        _clear_timeout_msg()


def run(username):
    global identifier

    identifier = username

    if _is_login():
        return 1

    # 启动程序，并且设置二维码的保存路径
    qr_dir = qr_folder + identifier + '.jpg'
    status_storage_dir = status_storage_folder + identifier + '.pkl'

    pid = os.fork()
    # 如果是子进程
    if pid == 0:
        try:
            # 第二次fork避免僵尸进程
            child_pid = os.fork()
            if child_pid > 0:
                # 将第二个子进程pid记录下来
                pid_logger(pid, 'a')
                os._exit(0)

            itchat.auto_login(hotReload=True, statusStorageDir=status_storage_dir, enableCmdQR=True, picDir=qr_dir,
                              loginCallback=_login_callback, exitCallback=_exit_callback)
            itchat.run()

        except Exception as e:
            logger.exception('username: %s, pid %d' % (username, os.getpid()))
            _exit_callback()
    else:
        # 等待第一个子进程结束
        os.waitpid(pid, 0)

    return pid


if __name__ == '__main__':
    # 启动程序，并且设置二维码的保存路径
    itchat.auto_login(hotReload=True, enableCmdQR=True, picDir=qr_folder + 'aaa.png')
    itchat.run()
