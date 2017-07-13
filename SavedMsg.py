# !/usr/bin/env python
# -*- coding: utf-8 -*-


class SavedMsg(object):
    '''
    缓存在本地的消息类
    '''

    def __init__(self):
        self.create_time = None  # 展示给用户的，接收消息时的本地时间 2017/03/03 13:23:53
        self.time = None
        self.type = None  # 消息类型
        self.content = None  # 根据消息类型不同，消息内容不同
        self.link = None  # 分享类消息url
        self.from_user = None
        self.group_name = None

    # 是否是包含文件的消息
    def has_file(self):
        return self.type in ['Picture', 'Recording', 'Video', 'Attachment']

    # 是否是包含链接的消息
    def is_sharing(self):
        return self.type == 'Sharing'

    # 构建撤回消息的文本
    def get_send_text(self):
        group_text = ''.join(['#', self.group_name, '  ']) if self.group_name else ''
        link_text = ''.join(['\n链接：', self.link]) if self.link else ''
        recalled_text = '\n撤回文件如下⬇️' if self.has_file() else ''

        send_text = ''.join([
            '新的撤回消息!\n',
            '撤回人：', group_text, self.from_user, '\n',
            '撤回时间：', self.time, '\n',
            '消息类型：', self.type, '\n',
            '消息内容：', self.content,
            link_text,
            recalled_text
        ])

        return send_text
