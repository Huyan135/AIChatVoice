#!/usr/bin/env python
# coding: utf-8

from wxbot import *
import ConfigParser
import json

class TulingWXBot(WXBot):
        
    def __init__(self):
        WXBot.__init__(self)

        self.tuling_key = ""
        self.robot_switch = True
        self.temp_pwd  =  os.path.join(os.getcwd(),'temp')
        self.person_user_id = "" # temp var for save contact
        self.voicePath="" #temp voice path for 小冰


        try:
            whitelist_cf = ConfigParser.ConfigParser()
            whitelist_cf.read(u'whitelist.ini')
            self.contacts = whitelist_cf.get('contacts', 'contact').split(',')

            cf = ConfigParser.ConfigParser()
            cf.read('conf.ini')
            self.tuling_key = cf.get('main', 'key')
           
        except Exception:
            pass
        print 'tuling_key:', self.tuling_key
        
    def save_to_file(file_name, contents):
        fh = open(file_name, 'w')
        fh.write(contents)
        fh.close()


    def tuling_auto_reply(self, uid, msg):
        if self.tuling_key:
            url = "http://www.tuling123.com/openapi/api"
            user_id = uid.replace('@', '')[:30]
            body = {'key': self.tuling_key, 'info': msg.encode('utf8'), 'userid': user_id}
            r = requests.post(url, data=body)
            respond = json.loads(r.text)
            result = ''
            if respond['code'] == 100000:
                result = respond['text'].replace('<br>', '  ')
                result = result.replace(u'\xa0', u' ')
            elif respond['code'] == 200000:
                result = respond['url']
            elif respond['code'] == 302000:
                for k in respond['list']:
                    result = result + u"【" + k['source'] + u"】 " +\
                        k['article'] + "\t" + k['detailurl'] + "\n"
            else:
                result = respond['text'].replace('<br>', '  ')
                result = result.replace(u'\xa0', u' ')

            print '    ROBOT:', result
            return result
        else:
            return u"知道啦"

    def auto_switch(self, msg):
        msg_data = msg['content']['data']
        stop_cmd = [u'退下', u'走开', u'关闭', u'关掉', u'休息', u'滚开', u'儿子你该睡觉了']
        start_cmd = [u'出来', u'启动', u'工作', u'儿子你在哪']
        if self.robot_switch:
            for i in stop_cmd:
                if i == msg_data:
                    self.robot_switch = False
                    self.send_msg_by_uid(u'[Robot]' + u'爸爸不要我了！[流泪]', msg['to_user_id'])
        else:
            for i in start_cmd:
                if i == msg_data:
                    self.robot_switch = True
                    self.send_msg_by_uid(u'[Robot]' + u'爸爸我来啦，啦啦啦[转圈]！', msg['to_user_id'])

    def handle_msg_all(self, msg):      
        if not self.robot_switch and msg['msg_type_id'] != 1:
            return
        if msg['msg_type_id'] == 1 and msg['content']['type'] == 0:  # reply to self
            self.auto_switch(msg)
        elif msg['msg_type_id'] == 4:  # text message from contact
            # 图灵
            #self.send_msg_by_uid(self.tuling_auto_reply(msg['user']['id'], msg['content']['data']), msg['user']['id'])
            for name in self.contacts:   #白名单
                if name == msg['user']['name']:
                    self.person_user_id = msg['user']['id']
                    if msg['content']['type'] == 0:
                        self.send_msg('小冰',msg['content']['data'],False)
                    elif msg['content']['type'] == 6: #动图
                        self.get_msg_img(msg['msg_id'])	
                        image = os.path.join(self.temp_pwd,'img_'+msg['msg_id']+'.png')
                        aiApiUserId = self.get_user_id('小冰')
                        self.send_img_msg_by_uid(image, aiApiUserId)

                    elif msg['content']['type'] in [4,7]: #语音
                        self.send_msg_by_uid('我还不会语音识别，请发文字吧', msg['user']['id'])
                    elif msg['content']['type'] == 3: #图片
                        #self.send_msg_by_uid('图片消息', msg['user']['id'])
                        image = os.path.join(self.temp_pwd,'img_'+msg['msg_id']+'.png')
                        aiApiUserId = self.get_user_id('小冰')
                        self.send_img_msg_by_uid(image, aiApiUserId)


        elif msg['msg_type_id'] == 5:  # reply to 公众号
            if self.get_user_id('小冰') == msg['user']['id']:
                if  msg['content']['type'] == 0:
                    self.send_msg_by_uid(msg['content']['data'], self.person_user_id)
                elif msg['content']['type'] == 4: #语音
                    voice = os.path.join(self.temp_pwd,'voice_'+msg['msg_id']+'.mp3')
                    self.send_file_msg_by_uid(voice, self.person_user_id)
                elif msg['content']['type'] ==3: #图片
                    image = os.path.join(self.temp_pwd,'img_'+msg['msg_id']+'.png')
                    self.send_img_msg_by_uid(image, self.person_user_id)
           
        elif msg['msg_type_id'] == 3 and msg['content']['type'] == 0:  # group text message
            if 'detail' in msg['content']:
                my_names = self.get_group_member_name(msg['user']['id'], self.my_account['UserName'])
                if my_names is None:
                    my_names = {}
                if 'NickName' in self.my_account and self.my_account['NickName']:
                    my_names['nickname2'] = self.my_account['NickName']
                if 'RemarkName' in self.my_account and self.my_account['RemarkName']:
                    my_names['remark_name2'] = self.my_account['RemarkName']

                is_at_me = False
                for detail in msg['content']['detail']:
                    if detail['type'] == 'at':
                        for k in my_names:
                            if my_names[k] and my_names[k] == detail['value']:
                                is_at_me = True
                                break
                if is_at_me:
                    src_name = msg['content']['user']['name']
                    reply = '@' + src_name + ': '
                    if msg['content']['type'] == 0:  # text message
                        reply += self.tuling_auto_reply(msg['content']['user']['id'], msg['content']['desc'])
                    else:
                        reply += u"对不起，只认字，其他杂七杂八的我都不认识，,,Ծ‸Ծ,,"
                    self.send_msg_by_uid(reply, msg['user']['id'])


def main():
    bot = TulingWXBot()
    bot.DEBUG = True
    bot.conf['qr'] = 'png'

    bot.run()


if __name__ == '__main__':
    main()

