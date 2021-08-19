#https://bottender.js.org/docs/en/1.3.1/channel-telegram-sending-messages
import StringIO
import json
import logging
import random
import urllib
import urllib2

# for sending images
from PIL import Image
import multipart

# standard app engine imports
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
import webapp2

TOKEN = YOUR_BOT_TOKEN_HERE

BASE_URL = 'https://api.telegram.org/bot' + TOKEN + '/'

#https://apps.timwhitlock.info/emoji/tables/unicode
SMILEY = '\xF0\x9F\x98\x81'

# ================================

class EnableStatus(ndb.Model):
    # key name: str(chat_id)
    enabled = ndb.BooleanProperty(indexed=False, default=False)


# ================================

def setEnabled(chat_id, yes):
    es = EnableStatus.get_or_insert(str(chat_id))
    es.enabled = yes
    es.put()

def getEnabled(chat_id):
    es = EnableStatus.get_by_id(str(chat_id))
    if es:
        return es.enabled
    return False


# ================================

class MeHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getMe'))))


class GetUpdatesHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getUpdates'))))


class SetWebhookHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        url = self.request.uri
        if url:
            self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'setWebhook', urllib.urlencode({'url': self.request.uri.replace('setWebhook','webhook')})))))


class WebhookHandler(webapp2.RequestHandler):
    def post(self):
        urlfetch.set_default_fetch_deadline(60)
        body = json.loads(self.request.body)
        logging.info('request body:')
        logging.info(body)
        self.response.write(json.dumps(body))

        update_id = body['update_id']
        try:
            message = body['message'] #handle message
            data = ''
        except:
            message = body['callback_query']['message'] #handle callback
            data = body['callback_query']['data']
            
        message_id = message.get('message_id') #Message IDs are unique per channel and otherwise unique per account. Different channels will obviously share the same IDs, but they're unique within the channel.
        date = message.get('date')
        text = message.get('text')
        fr = message.get('from')
        chat = message['chat']
        chat_id = chat['id'] #chat_id will always be unique for each user connecting to your bot. If the same user sends messages to different bots, they will always 'identify' themselves with their unique id 

        def reply(msg=None, raw=None, img=None, endPoint='sendMessage'):
            if msg:
                resp = urllib2.urlopen(BASE_URL + endPoint, urllib.urlencode({
                    'chat_id': str(chat_id),
                    'text': msg.encode('utf-8'),
                    'disable_web_page_preview': 'true',
                    'reply_to_message_id': str(message_id),
                })).read()
            elif img:
                resp = multipart.post_multipart(BASE_URL + endPoint, [
                    ('chat_id', str(chat_id)),
                    ('reply_to_message_id', str(message_id)),
                ], [
                    ('photo', 'image.jpg', img),
                ])
            elif raw:
                resp = urllib2.urlopen(BASE_URL + endPoint, urllib.urlencode(raw)).read()            
            else:
                logging.error('no msg, img or raw specified')
                resp = None

            logging.info('send response:')
            logging.info(resp)
            
        if data:
            reply('I got your callback data {}'.format(data))

        elif text.startswith('/'):
            if text == '/start':
                reply('Bot enabled')
                setEnabled(chat_id, True)
            elif text == '/stop':
                reply('Bot disabled')
                setEnabled(chat_id, False)
            elif text == '/image':
                img = Image.new('RGB', (512, 512))
                base = random.randint(0, 16777216)
                pixels = [base+i*j for i in range(512) for j in range(512)]  # generate sample image
                img.putdata(pixels)
                output = StringIO.StringIO()
                img.save(output, 'JPEG')
                reply(img=output.getvalue(), endPoint='sendPhoto')
            elif text == '/image1':
                reply(raw={'chat_id' : str(chat_id),
                    'photo':'https://akcdn.detik.net.id/community/media/visual/2020/09/17/logo-detikcom.png?d=1',
                    'caption': 'logo detik.com'}, endPoint='sendPhoto')
            elif text == '/loc':
                reply(raw={'chat_id' : str(chat_id),
                    'latitude': 3.597031,
                    'longitude': 98.678513 }, endPoint='sendLocation')
            elif text == '/poll':
                options = '["soto","pecel","indomie","nasi padang"]'
                reply(raw={'chat_id' : str(chat_id),
                    'question': 'what is your favourite food?',
                    'options': options }, endPoint='sendPoll')                
            elif text == '/url':
                reply(raw={'chat_id' : str(chat_id),
                    'text' : 'Click to Open [URL](http://example.com)',
                    'parse_mode' : "markdown",
                    'reply_to_message_id': str(message_id)})            
            elif text == '/url1':
                #inline keyboard, open URL
                keyboard = '{"inline_keyboard" : [[{"text" : "Open link", "url" : "http://example.com"}]]}'
                reply(raw={'chat_id' : str(chat_id),
                    'text' : 'Click to Open URL',
                    'parse_mode' : 'markdown',
                    'reply_to_message_id': str(message_id),
                    'reply_markup' : keyboard })
            elif text == '/key1':
                #inline keyboard sample, parse_mode='markdown' https://core.telegram.org/bots/api#formatting-options
                keyboard = '{"inline_keyboard" : [[{"text" : "keyboard", "callback_data" : "ini callback data"}]]}'
                reply(raw={'chat_id' : str(chat_id),
                    'text' : 'Click to Open *URL*',
                    'parse_mode' : 'markdown',
                    'reply_to_message_id': str(message_id),
                    'reply_markup' : keyboard })
            elif text == '/key2':
                #inline keyboard sample, parse_mode='HTML' https://core.telegram.org/bots/api#formatting-options
                keyboard = '{"inline_keyboard" : [[{"text" : "keyboard", "callback_data" : "ini callback data"}]]}'
                reply(raw={'chat_id' : str(chat_id),
                    'text' : 'Click to Open <b>URL</b>',
                    'parse_mode' : 'HTML',
                    'reply_to_message_id': str(message_id),
                    'reply_markup' : keyboard })
            elif text == '/key2a':
                #inline keyboard sample with icon, parse_mode='HTML'
                keyboard = '{"inline_keyboard" : [[{"text" : "\xF0\x9F\x98\x81 keyboard", "callback_data" : "ini callback data"}]]}'
                reply(raw={'chat_id' : str(chat_id),
                    'text' : 'Click to Open <b>URL</b>',
                    'parse_mode' : 'HTML',
                    'reply_to_message_id': str(message_id),
                    'reply_markup' : keyboard })                       
            elif text == '/key3':
                #keyboard sample
                keyboard = '{"keyboard" : [[{"text" : "keyboard"}]]}'
                reply(raw={'chat_id' : str(chat_id),
                    'text' : 'Click to Open *URL*',
                    'parse_mode' : 'markdown',
                    'reply_to_message_id': str(message_id),
                    'reply_markup' : keyboard })
            elif text == '/key4':
                #keyboard sample
                keyboard = '{"keyboard" : [[{"text" : "atas"}], [{"text" : "kiri"},{"text" : "kanan"}]]}'
                reply(raw={'chat_id' : str(chat_id),
                    'text' : 'Click to Open *URL*',
                    'parse_mode' : 'markdown',
                    'reply_to_message_id': str(message_id),
                    'reply_markup' : keyboard })
            elif text == '/key5':
                #keyboard sample, one_time_keyboard
                keyboard = '{"keyboard" : [[{"text" : "atas"}], [{"text" : "kiri"},{"text" : "kanan"}]],"resize_keyboard":true,"one_time_keyboard":true}'
                reply(raw={'chat_id' : str(chat_id),
                    'text' : 'Click to Open *URL*',
                    'parse_mode' : 'markdown',
                    'reply_to_message_id': str(message_id),
                    'reply_markup' : keyboard })
            elif text == '/key6':
                #remove keyboard
                keyboard = '{"remove_keyboard":true}'
                reply(raw={'chat_id' : str(chat_id),
                    'text' : 'Remove keyboard /key4',
                    'parse_mode' : 'markdown',
                    'reply_to_message_id': str(message_id),
                    'reply_markup' : keyboard })                    
            else:
                reply(text)

        # CUSTOMIZE FROM HERE

        elif 'who are you' in text:
            reply('telebot starter kit, created by yukuku: https://github.com/yukuku/telebot')
        elif 'what time' in text:
            reply('look at the corner of your screen!')
        else:
            if getEnabled(chat_id):
                reply('I got your message {}! (but I do not know how to answer)'.format(text))
            else:
                logging.info('not enabled for chat_id {}'.format(chat_id))


app = webapp2.WSGIApplication([
    ('/me', MeHandler),
    ('/updates', GetUpdatesHandler),
    ('/setWebhook', SetWebhookHandler),
    ('/webhook', WebhookHandler),
], debug=True)


