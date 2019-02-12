
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    LineBotApiError, InvalidSignatureError
)
from firebase import firebase
from linebot.models import (
    SourceUser,SourceGroup,SourceRoom,LeaveEvent,JoinEvent,
    TemplateSendMessage,PostbackEvent,AudioMessage,LocationMessage,
    ButtonsTemplate,LocationSendMessage,AudioSendMessage,ButtonsTemplate,
    ImageMessage,URITemplateAction,MessageTemplateAction,ConfirmTemplate,
    PostbackTemplateAction,ImageSendMessage,MessageEvent, TextMessage, 
    TextSendMessage,StickerMessage, StickerSendMessage,DatetimePickerTemplateAction,
    CarouselColumn,CarouselTemplate,VideoSendMessage,ImagemapSendMessage,BaseSize,
    URIImagemapAction,MessageImagemapAction,ImagemapArea,ImageCarouselColumn,ImageCarouselTemplate,
    FlexSendMessage, BubbleContainer, ImageComponent, BoxComponent,
    TextComponent, SpacerComponent, IconComponent, ButtonComponent,
    SeparatorComponent,URIAction,LocationAction,QuickReply,QuickReplyButton,
    DatetimePickerAction,PostbackAction,MessageAction,CameraAction,CameraRollAction

)
from imgurpython import ImgurClient
import re
from bs4 import BeautifulSoup as bf
import requests
import random
import os,tempfile
from datetime import timedelta, datetime
from time import sleep
import json
from selenium import webdriver
from urllib.parse import quote
from urllib import parse
from flask import Flask, request, render_template, make_response, abort
#from flask_bootstrap import Bootstrap
#from PIL import Image
#import warnings
#warnings.simplefilter('error', Image.DecompressionBombWarning)

client_id = os.getenv('client_id',None)
client_secret = os.getenv('client_secret',None)
album_id = os.getenv('album_id',None)
access_token = os.getenv('access_token',None)
refresh_token = os.getenv('refresh_token',None)
client = ImgurClient(client_id, client_secret, access_token, refresh_token)
url = os.getenv('firebase_bot',None)
fb = firebase.FirebaseApplication(url,None)


line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN',None))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET', None))

app = Flask(__name__)
#bootstrap = Bootstrap(app)



@app.route('/list')
def do_get():
    return render_template('list.html')


#@app.route('/2')
#def do_get():
#    return render_template('index2.html')

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    bodyjson=json.loads(body)
    #app.logger.error("Request body: " + bodyjson['events'][0]['message']['text'])
#    app.logger.error("Request body: " + body)
    #insertdata
#    print('-----in----------')
#    add_data = usermessage(
#            id = bodyjson['events'][0]['message']['id'],
#            user_id = bodyjson['events'][0]['source']['userId'],
#            message = bodyjson['events'][0]['message']['text'],
#            birth_date = datetime.fromtimestamp(int(bodyjson['events'][0]['timestamp'])/1000)
#        )
#    db.session.add(add_data)
#    db.session.commit()
    # handle webhook body
    try:
        handler.handle(body,signature)
    except LineBotApiError as e:
        print("Catch exception from LINE Messaging API: %s\n" % e.message)
        for m in e.error.details:
            print("ERROR is %s: %s" % (m.property, m.message))
        print("\n")
    except InvalidSignatureError:
        abort(400)
    return 'OK'



def movie_template():
            buttons_template = TemplateSendMessage(
            alt_text='電影 template',
            template=ButtonsTemplate(
                title='服務類型',
                text='請選擇',
                thumbnail_image_url='https://i.imgur.com/zzv2aSR.jpg',
                actions=[
                    MessageTemplateAction(
                        label='近期上映電影',
                        text='近期上映電影'
                    ),
                    MessageTemplateAction(
                        label='依莉下載電影',
                        text='eyny'
                    ),
                    MessageTemplateAction(
                        label='觸電網-youtube',
                        text='觸電網-youtube'
                    ),
                    MessageTemplateAction(
                        label='Marco體驗師-youtube',
                        text='Marco體驗師'
                    )
                ]
            )
        )
            return buttons_template


def apple_news():
    target_url = 'https://tw.appledaily.com/new/realtime'
    print('Start parsing appleNews....')
    rs = requests.session()
    res = rs.get(target_url, verify=False)
    soup = bf(res.text, 'html.parser')
    content = ""

    for index, data in enumerate(soup.select('.rtddt a'), 0):
        if index == 5:
            return content
        title = data.select('font')[0].text
        link = data['href']
        content += '{}\n{}\n'.format(title,link)
    return content


def youtube_page(keyword):
    url = []
    title = []
    pic = []
    target_url = 'https://www.youtube.com/results?search_query={}&sp=EgIQAQ%253D%253D'.format(quote(keyword))
    rs = requests.session()
    res = rs.get(target_url)
    soup = bf(res.text, 'html.parser')
    for data in soup.select('.yt-lockup-title'):
        if len(data.find('a')['href']) > 20:
            continue
        url.append('https://www.youtube.com{}'.format(data.find('a')['href']))
        title.append(data.find('a')['title'])
        pic.append('https://i.ytimg.com/vi/{}/0.jpg'.format(data.find('a')['href'][9:]))
    return url,title,pic


def yvideo(url):
    url = 'https://qdownloader.net/download?video={}'.format(url)
    res = requests.get(url)
    soup = bf(res.text,'html.parser')
    t = soup.select('.col-md-8 td a' )
    c = 0
    url = t[c]['href']
    while re.search(r'.*googlevideo.*',url) == None:
        url = t[c]['href']
        c += 1
    t = soup.select('.info.col-md-4 img' )
    img = t[0]['src']
    url = re.search(r'.*&title',url).group()[:-6]
    return url,img


def yout_download(_id):
    print('in')
    url = 'http://www.youtube.com/get_video_info?eurl=http%3A%2F%2Fkej.tw%2F&sts=17885&video_id={}'.format(str(_id))
    res = requests.get(url).text
    a = parse.parse_qs(res)
#    img =  'http://i.ytimg.com/vi/{}/0.jpg'.format(_id)
#    title =  (a['title']) 
    b = parse.parse_qs(a['url_encoded_fmt_stream_map'][0])
    url = b['url'][0]
    print('out----'+url)
    return url

def buttons_template_yout(page,keyword):
    confirm_template = TemplateSendMessage(
            alt_text = 'video template',
            template = ConfirmTemplate(
                    text = '請選擇一下',
                    actions = [
                            MessageTemplateAction(
                                    label = '推薦',
                                    text = '台北暗殺星奪冠之路yout'
                                    ),
                            PostbackTemplateAction(
                                    label = '再來10部',
                                    data = 'carousel/{}/{}'.format(page,keyword)
                                    )
                            ]
                    )
            )
    return confirm_template


def carousel_template(keyword,page=0):
    pass_url = []
    video_url,title,img_url = youtube_page(keyword)
    if page!=0:
        if page%2 == 0:
            pass
        else:
            temp = 10
            video_url = [i for i in video_url[temp:]]
            title = [i for i in title[temp:]]
            img_url = [i for i in img_url[temp:]]
    pass_url = [i[32:] for i in video_url]
    if len(title)<10:
        buttons_template = porn_video_template(keyword)
        return buttons_template 
    
    Image_Carousel = TemplateSendMessage(
        alt_text='Carousel_template',
        template=ImageCarouselTemplate(
        columns=[
            ImageCarouselColumn(
                image_url=img_url[0],
                action=PostbackTemplateAction(
                    label=title[0][:12],
                    text='請等待一下...',
                    data = 'video/{}/{}'.format(keyword,pass_url[0])
                )
            ),
            ImageCarouselColumn(
                image_url=img_url[1],
                action=PostbackTemplateAction(
                    label=title[1][:12],
                    text='請等待一下...',
                    data = 'video/{}/{}'.format(keyword,pass_url[1])
                )
            ),
            ImageCarouselColumn(
                image_url=img_url[2],
                action=PostbackTemplateAction(
                    label=title[2][:12],
                    text='請等待一下...',
                    data = 'video/{}/{}'.format(keyword,pass_url[2])
                )
            ),
            ImageCarouselColumn(
                image_url=img_url[3],
                action=PostbackTemplateAction(
                    label=title[3][:12],
                    text='請等待一下...',
                    data = 'video/{}/{}'.format(keyword,pass_url[3])
                )
            ),
            ImageCarouselColumn(
                image_url=img_url[4],
                action=PostbackTemplateAction(
                    label=title[4][:12],
                    text='請等待一下...',
                    data = 'video/{}/{}'.format(keyword,pass_url[4])
                )
            ),
            ImageCarouselColumn(
                image_url=img_url[5],
                action=PostbackTemplateAction(
                    label=title[5][:12],
                    text='請等待一下...',
                    data = 'video/{}/{}'.format(keyword,pass_url[5])
                )
            ),
            ImageCarouselColumn(
                image_url=img_url[6],
                action=PostbackTemplateAction(
                    label=title[6][:12],
                    text='請等待一下...',
                    data = 'video/{}/{}'.format(keyword,pass_url[6])
                )
            ),
            ImageCarouselColumn(
                image_url=img_url[7],
                action=PostbackTemplateAction(
                    label=title[7][:12],
                    text='請等待一下...',
                    data = 'video/{}/{}'.format(keyword,pass_url[7])
                )
            ),
            ImageCarouselColumn(
                image_url=img_url[8],
                action=PostbackTemplateAction(
                    label=title[8][:12],
                    text='請等待一下...',
                    data = 'video/{}/{}'.format(keyword,pass_url[8])
                )
            ),
            ImageCarouselColumn(
                image_url=img_url[9],
                action=PostbackTemplateAction(
                    label=title[9][:12],
                    text='請等待一下...',
                    data = 'video/{}/{}'.format(keyword,pass_url[9])
                )
            )
        ]
    )
    )
    return [Image_Carousel,buttons_template_yout(page,keyword)]
 
def porn_video_template(keyword,index=0):
        video_url,title,img_url = youtube_page(keyword)
        pass_url = video_url[index][32:]
        title = title[index]
        buttons_template = TemplateSendMessage(
        alt_text='video template',
        template=ButtonsTemplate(
            title = title[:40],
            text='請選擇',
            thumbnail_image_url=img_url[index],
            actions=[
                PostbackTemplateAction(
                    label='觀看~請耐心等待.....',
                    data = 'video/{}/{}/{}'.format(str(index),keyword,pass_url)
                ),
                PostbackTemplateAction(
                    label='下一部',
                    data = 'porn/{}/{}'.format(str(index),keyword)
                )
            ]))
        return buttons_template
    
#更改
def drink_menu(text):
    pattern = r'.*menu$'
    web = []
    if re.search(pattern,text.lower()):
        temp = get_image_link(text)
        print('fun'+str(temp))
        for t in temp:
            web.append(ImageSendMessage(original_content_url=t,preview_image_url=t))
        return web
    
def google_picture(text):
    pattern = r'.*pic$'
    web = []
    if re.search(pattern,text.lower()):
        temp = get_image_link(text)
        for t in temp:
            web.append(ImageSendMessage(original_content_url=t,preview_image_url=t))
        return web

def movie():
    target_url = 'http://www.atmovies.com.tw/movie/next/0/'
    print('Start parsing movie ...')
    rs = requests.session()
    res = rs.get(target_url, verify=False)
    res.encoding = 'utf-8'
    soup = bf(res.text, 'html.parser')
    content = ""
    for index, data in enumerate(soup.select('ul.filmNextListAll a')):
        if index == 20:
            return content
        title = data.text.replace('\t', '').replace('\r', '')
        link = "http://www.atmovies.com.tw" + data['href']
        content += '{}\n{}\n'.format(title, link)
    return content


def pattern_mega(text):
    patterns = [
        'mega', 'mg', 'mu', 'ＭＥＧＡ', 'ＭＥ', 'ＭＵ',
        'ｍｅ', 'ｍｕ', 'ｍｅｇａ', 'GD', 'MG', 'google',
    ]
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
        
def eyny_movie():
    target_url = 'http://www.eyny.com/forum-205-1.html'
    rs = requests.session()
    res = rs.get(target_url, verify=False)
    soup = bf(res.text, 'html.parser')
    content = ''
    for titleURL in soup.select('.bm_c tbody .xst'):
        if pattern_mega(titleURL.text):
            title = titleURL.text
            if '11379780-1-3' in titleURL['href']:
                continue
            link = 'http://www.eyny.com/' + titleURL['href']
            data = '{}\n{}\n\n'.format(title, link)
            content += data
    return content

def panx():
    target_url = 'https://panx.asia/'
    print('Start parsing ptt hot....')
    rs = requests.session()
    res = rs.get(target_url, verify=False)
    soup = bf(res.text, 'html.parser')
    content = ""
    for data in soup.select('div.container div.row div.desc_wrap h2 a'):
        title = data.text
        link = data['href']
        content += '{}\n{}\n\n'.format(title, link)
    return content

def magazine():
    target_url = 'https://www.cw.com.tw/'
    rs = requests.session()
    res = rs.get(target_url, verify=False)
    res.encoding = 'utf-8'
    soup = bf(res.text, 'html.parser')
    temp = ""
    for v ,date in enumerate(soup.select('.caption h3 a'),0):
        url = date['href']
        title = date.text.strip()
        temp += '{}\n{}\n'.format(title,url)
        if(v>4):
            break
    return temp
def lottery():
#    url = 'https://www.pilio.idv.tw/ltobig/drawlist/drawlist.asp'
#    url2 = 'https://www.pilio.idv.tw/lto539/drawlist/drawlist.asp'
#    url3 = 'https://www.pilio.idv.tw/lto/drawlist/drawlist.asp'
    name = ['ltobig','lto539','lto']
    for i in name:
        url = 'https://www.pilio.idv.tw/{}/drawlist/drawlist.asp'.format(i)
        res = requests.get(url)
        res.encoding = 'utf-8'
        soup = bf(res.text,'html.parser')
        t = soup.select('.inner td')
        if i == 'ltobig':
            big = [t[i].text.strip() for i in range(4,10,1)]
        elif i == 'lto539':
            b539 = [t[i].text.strip() for i in range(3,7,1)]
        elif i == 'lto':
            bwei = [t[i].text.strip() for i in range(3,7,1)]

    return big,b539,bwei

def lottery_stat(type_lottery,year):
    if type_lottery == 'big-lotto':
        div = 4
    elif type_lottery == 'power':
        div = 5
    elif type_lottery == 'daily539':
        div = 7
    url = 'http://lotto.auzonet.com/lotto_balllist_{}_{}.html'.format(type_lottery,year)
    res = requests.get(url)
    res.encoding = 'utf-8'
    soup = bf(res.text,'html.parser')
    num = ''
    for c,i in enumerate(soup.select('.forumline tr td')[3:],1):
        if c%3 == 2:
            continue
        elif c%3 == 1:
            num += ' '+i.text.strip()+'         '
        else:
            if len(i.text.strip()) < 2:
                num += '0{}次   {}\n'.format(i.text.strip(),'🎈️'*((int(i.text.strip()))//div))         
            else:
                num += '{}次   {}\n'.format(i.text.strip(),'🎈️'*((int(i.text.strip()))//div))          
    return num

def lottery_all_num(type_lottery):
    if type_lottery == 'big-lotto':
        type_lottery = 'listltobigbbk'
        start = 4
        div = 4
    elif type_lottery == 'power':
        type_lottery =  'listlto'
        start = 4
        div = 4
    elif type_lottery == 'daily539':
        type_lottery = 'listlto539bbk'
        start = 3
        div = 3
    url = 'https://www.lotto-8.com/{}.asp'.format(type_lottery)
    res = requests.get(url)
    res.encoding = 'utf-8'
    soup = bf(res.text,'html.parser')
    num = ''
    for c,i in enumerate(soup.select('.auto-style4 tr td')[start:],1):
        if c % div == 1:
            num += i.text.strip()
        elif c % div == 2:
            num += '    {}\n'.format(i.text.strip())
        elif c % div == 3:
            if type_lottery == 'listltobigbbk':
                num += '💰️特別號 : {}\n'.format(i.text.strip())
            elif type_lottery == 'listlto':
                num += '💰️第二區 : {}\n'.format(i.text.strip())
    return num

def lottery_year(type_lottery):
    if type_lottery == 'big-lotto':
        t = '大樂透'
    elif type_lottery == 'power':
        t = '威力彩'
    elif type_lottery == 'daily539':
         t = '今彩539'
    Carousel_template = TemplateSendMessage(
        alt_text='Carousel template',
        template=CarouselTemplate(
        columns=[
            CarouselColumn(
                thumbnail_image_url='https://i.imgur.com/zp75S87.jpg',
                title=t+'--各個年份的統計',
                text='請選擇年份',
                actions=[
                    PostbackTemplateAction(
                        label='2019',
                        data='ball_st/{}/{}'.format('2019',type_lottery)
                    ),
                    PostbackTemplateAction(
                        label='2018',
                        data='ball_st/{}/{}'.format('2018',type_lottery)
                    ),
                    PostbackTemplateAction(
                        label='2017',
                        data='ball_st/{}/{}'.format('2017',type_lottery)
                    )
                ]
            ),
            CarouselColumn(
                thumbnail_image_url='https://i.imgur.com/zp75S87.jpg',
                title='各個年份的統計',
                text='請選擇年份',
                actions=[
                    PostbackTemplateAction(
                        label='2016',
                        data='ball_st/{}/{}'.format('2016',type_lottery)
                    ),
                    PostbackTemplateAction(
                        label='2015',
                        data='ball_st/{}/{}'.format('2015',type_lottery)
                    ),
                    PostbackTemplateAction(
                        label='2014',
                        data='ball_st/{}/{}'.format('2014',type_lottery)
                    ),
                ]
            )
        ]
    )
    )
    return Carousel_template           

def check_pic(img_id):
    Confirm_template = TemplateSendMessage(
    alt_text='要給你照片標籤描述嗎?',
    template=ConfirmTemplate(
    title='注意',
    text= '要給你照片標籤描述嗎?\n要就選Yes,並且回覆\n-->id+描述訊息(這張照片id是'+ str(img_id) +')',
    actions=[                              
            PostbackTemplateAction(
                label='Yes',
                text='I choose YES',
                data='action=buy&itemid=1'
            ),
            MessageTemplateAction(
                label='No',
                text='I choose NO'
            )
        ]
    )
    )
    return Confirm_template


#判斷是西洋還是華語歌曲 如果為西洋category是390 而華語是297
def type_music(category,range_num=5):
    template = []
    yesterday = datetime.today() + timedelta(-1)
    yesterday_format = yesterday.strftime('%Y-%m-%d')
    t = 'https://kma.kkbox.com/charts/api/v1/daily?category='+str(category)+'&date='+yesterday_format+'&lang=tc&limit=50&terr=tw&type=song'
    res = requests.get(t).json()
    for i in range(range_num-5,range_num):
        print('processing='+str(i))
        template.append(process_mp3_template(res['data']['charts']['song'][i]['song_name'],i+1,res['data']['charts']['song'][i]['cover_image']['normal'],res['data']['charts']['song'][i]['artist_name'],res['data']['charts']['song'][i]['song_url'],process_mp3_url('https://www.kkbox.com/tw/tc/ajax/wp_songinfo.php?type=song&crypt_id='+res['data']['charts']['song'][i]['song_id']+'&ver=2'),range_num,category))
    return template

#處理kkbox抓來的mp3網址
def process_mp3_url(url):
    res = requests.get(url).json()
    try:
        t = res['data'][0]['mp3_url']
        return t
    except:
        return '音樂版權未授權~'
#一個模板來放抓來的音樂並顯示連結
def process_mp3_template(title,rank,album_image,singer,song_url,listen_url,range_num,category):
    if song_url == '#':
        label = '無介紹與歌詞'
        song_url = 'https://github.com/kevin1061517?tab=repositories'
    else:
        label = '介紹及歌詞'
    buttons_template = TemplateSendMessage(
        alt_text='mp3_template',
        template=ButtonsTemplate(
            title = '排行榜第{}名'.format(rank),
            text='歌手:{}\n歌名:{}'.format(singer,title)[:60],
            thumbnail_image_url = album_image,
            actions=[
                URITemplateAction(
                    label = label,
                    uri = song_url
                ),
                PostbackTemplateAction(
                    label='試聽30秒',
                    data = 'listen'+listen_url,
                    
                ),
                PostbackTemplateAction(
                    label = '再看看{}名~{}名 歌曲'.format(range_num+1,range_num+5),
                    data = 'next'+str(range_num+5)+str(category)
                )
            ]
         )
    )
    return buttons_template
  



def look_up(tex):
    content = ''
    target_url = 'https://tw.dictionary.search.yahoo.com/search;_ylt=AwrtXG86cTRcUGoAESt9rolQ?p={}&fr2=sb-top'.format(tex)
    res =  requests.get(target_url)
    soup = bf(res.text,'html.parser')
    try:
        content += '{}\n'.format(soup.select('.lh-22.mh-22.mt-12.mb-12.mr-25.last')[0].text)
        for i in soup.select('.layoutCenter .lh-22.mh-22.ml-50.mt-12.mb-12'):
            if i.select('p  span') != []:   
                content += '{}\n{}\n'.format(i.select('.fz-14')[0].text,i.select('p  span')[0].text)
            else:
                content += '{}\n'.format(i.select('.fz-14')[0].text)
        if content == '':
            for i in soup.select('.layoutCenter .ml-50.mt-5.last'):
                content += i.text
    except IndexError:
        content = '查無此字'
    return content


def integer_word(word):
    content = look_up(word)
    if content != '查無此字':
        content = [TextComponent(text='🔍英文單字查詢',weight='bold', align='center',size='md',wrap=True,color='#000000'),SeparatorComponent(margin='lg'),TextComponent(text=content, size='sm',wrap=True,color='#000000')]
        audio_button = [
                    SeparatorComponent(),
                    ButtonComponent(
                        style='link',
                        height='sm',
                        action=PostbackAction(label='📢 美式發音', data='audio/{}'.format(word))
                    )
                    ]
        bubble = get_total_flex(content,audio_button)
        message = FlexSendMessage(alt_text="hello", contents=bubble)
    else:
        message = TextSendMessage(text=content)
    return message

def process_draw(user_id):
        start = fb.get('/{}/start'.format(user_id),None)
        if not start:
            start = 0
        else:
            start = list(start.values())[0]
        end = fb.get('/{}/end'.format(user_id),None)
        if not end:
            end = 0
        else:
            end = list(end.values())[0]
        bubble = BubbleContainer(
            direction='ltr',
            body=BoxComponent(
                layout='vertical',
                contents=[
                    TextComponent(text= '抽數字',size='xl',color='#000000'),
                    TextComponent(text= '按照步驟來隨機產生幸運數字', size='sm',color='#888888'),
                    # review
                    SeparatorComponent(color='#000000'),
                    # info
                    BoxComponent(
                        layout='vertical',
                        color = '#FFFF00',
                        spacing='sm',
                        contents=[
                            BoxComponent(
                                layout='baseline',
                                contents=[
                                    TextComponent(
                                        text='起始',
                                        color='#000000',
                                        size='xxl',
                                        flex = 5
                                    ),
                                    TextComponent(
                                        text=str(start),
                                        size='xxl',
                                        flex = 5
                                    )
                                ],
                            ),
                            BoxComponent(
                                layout='baseline',
                                contents=[
                                    TextComponent(
                                        text='結束',
                                        color='#000000',
                                        size='xxl',
                                        flex = 5
                                    ),
                                    TextComponent(
                                        text=str(end),
                                        size='xxl',
                                        flex = 5
                                    )
                                ],
                            )
                        ],
                    ),
                ],
            ),
            footer=BoxComponent(
                layout='vertical',
                spacing='xs',
                contents=[
                    # websiteAction
                    ButtonComponent(
                        style='secondary',
                        color='#FFEE99',
                        height='sm',
                        action=MessageAction(label='設定起始數字',text='請輸入起始數字-----------')
                    ),
                    SeparatorComponent(color='#000000'),
                    # websiteAction
                    ButtonComponent(
                        style='secondary',
                        color='#FFEE99',
                        height='sm',
                        action=MessageAction(label='設定結束數字(包含)',text='請輸入結束數字-----------')
                    ),
                    SeparatorComponent(color='#000000'),
                    # websiteAction
                    ButtonComponent(
                        style='secondary',
                        color='#FFEE99',
                        height='sm',
                        action=PostbackAction(label='開始抽籤',text='抽籤結果!!',data='random/{}/{}'.format(start,end))
                    )
                ]
            ),
        )
        return bubble
    
def process_choose(user_id):
    t = fb.get('/{}/opti_num'.format(user_id),None)
    t1 = fb.get('/{}/ques_num'.format(user_id),None)
    if not t or not t1:
        print('-------not')
        return
    temp_ques = list(t1.values())[0]
    temp_opti = list(t.values())[0]
    temp_opti = temp.split(';')
    texts = [TextComponent(
                text='{}\n'.format(i),
                color='#000000',
                size='lg'
                ) for i in temp_opti]
    bubble = BubbleContainer(
            direction='ltr',
            body=BoxComponent(
                layout='vertical',
                contents=[
                    TextComponent(text= '如果都確定好就按下為下面的抽籤按鈕', weight='bold',size='xl',color='#000000'),
                    TextComponent(text= '結果好不好交給老天爺', size='md',color='#888888'),
                    # review
                    SeparatorComponent(color='#000000'),
                    # info
                    BoxComponent(
                        layout='vertical',
                        spacing='sm',
                        contents=[
                            BoxComponent(
                                layout='baseline',
                                contents=[
                                    TextComponent(
                                        text='問題:{}'.format(temp_ques),
                                        color='#000000',
                                        size='lg'
                                    ),
                                    TextComponent(
                                        text='選項:',
                                        color='#000000',
                                        gravity = 'center',
                                        size='lg'
                                    ),
                                    texts,
                                    SeparatorComponent(color='#000000')
                                ],
                            )
                        ],
                    ),
                ],
            ),
            footer=BoxComponent(
                layout='vertical',
                spacing='xs',
                contents=[
                    ButtonComponent(
                        style='secondary',
                        color='#5555FF',
                        height='sm',
                        action=PostbackAction(label='隨機選擇',data='other',text='請選擇一下喔~')
                    ),
                    ButtonComponent(
                        style='secondary',
                        color='#5555FF',
                        height='sm',
                        action=MessageAction(label='設定問題',text='請輸入要設定抉擇的問題:')
                    ),
                    SeparatorComponent(color='#000000'),
                    ButtonComponent(
                        style='secondary',
                        color='#5555FF',
                        height='sm',
                        action=MessageAction(label='設定選項',text='請輸入要設定的選項，各個選項以分號區隔~')
                    )
                ]
            ),
        )
    message = FlexSendMessage(alt_text="hello", contents=bubble)
    return message
@handler.add(PostbackEvent)
def handle_postback(event):
    temp = event.postback.data
    if temp[:5] == 'audio':
        print('-----------')
        t = temp.split('/')
        word = t[1]
        url = 'https://s.yimg.com/bg/dict/dreye/live/f/{}.mp3'.format(word)
        line_bot_api.reply_message(
                event.reply_token,
                AudioSendMessage(original_content_url=url,duration=3000)
            )
    elif temp[:5] == 'first':
        print('--------in-----')
        temp = temp.split('/')
        _type = temp[1]
        text = ''
        text = '開始'
        action = PostbackAction(label='開始選擇',data='first/{}/start'.format(_type),text='為你選出最佳選擇')
        color = ['#AAAAAA','#AAAAAA']
        point = ['👈','👈']
        if  _type == 'yesno':
            t = ['要','不要']
        elif _type == 'buy':
            t = ['買','不買']
        elif _type == 'yes':
            t = ['是','不是']

        if 'start' in temp:
            text = '其他選擇'
            r = random.randint(0,1)
            print('----------'+str(r))
            point[r] = ' '
            color[1-r] = '#000000'
            action = MessageAction(label='其他選擇',text='choose')
        bubble = BubbleContainer(
            direction='ltr',
            body=BoxComponent(
                layout='vertical',
                contents=[
                    TextComponent(text= '隨機選擇',gravity='center',size='xl',color='#000000'),
                    TextComponent(text= '{}請按最下面按鈕'.format(text), size='sm',gravity='center',color='#888888'),
                    # review
                    SeparatorComponent(color='#000000'),
                    # info
                    BoxComponent(
                        layout='vertical',
                        color = '#FFFF00',
                        spacing='sm',
                        contents=[
                            BoxComponent(
                                layout='baseline',
                                contents=[
                                    TextComponent(
                                        text=t[0],
                                        color=color[0],
                                        size='xl',
                                        flex = 5
                                    ),
                                    TextComponent(
                                        text=point[0],
                                        size='xl',
                                        flex = 5
                                    )
                                ],
                            ),
                            BoxComponent(
                                layout='baseline',
                                contents=[
                                    TextComponent(
                                        text=t[1],
                                        color=color[1],
                                        size='xl',
                                        flex = 5
                                    ),
                                    TextComponent(
                                        text=point[1],
                                        size='xl',
                                        flex = 5
                                    )
                                ],
                            )
                        ],
                    ),
                ],
            ),
            footer=BoxComponent(
                layout='vertical',
                spacing='xs',
                contents=[
                    # websiteAction
                    ButtonComponent(
                        style='secondary',
                        color='#FFEE99',
                        height='sm',
                        action=action
                    )
                ]
            ),
        )
        message = FlexSendMessage(alt_text="hello", contents=bubble)
        line_bot_api.reply_message(
            event.reply_token,
            message
        )
    elif temp[:6] == 'random':
        profile = line_bot_api.get_profile(event.source.user_id)
        user_name = profile.display_name
        user_id = event.source.user_id
        bubble = process_draw(user_id)
        t = temp.split('/')
        start = int(t[1])
        end = int(t[2])
        if start >= end:
             message = FlexSendMessage(alt_text="hello", contents=bubble)
             line_bot_api.reply_message(
                event.reply_token,
                [TextSendMessage(text='咦!{}要注意起始不能大於等於最後一個數字喔!!'.format(user_name)),message])
             return
        r = random.randint(start,end)
        bubble = BubbleContainer(
            direction='ltr',
            body=BoxComponent(
                layout='vertical',
                contents=[
                    TextComponent(text= '隨機選擇',size='xl',color='#000000'),
                    TextComponent(text= '🔔🔔🔔', size='sm'),
                    # review
                    SeparatorComponent(color='#000000'),
                    # info
                    BoxComponent(
                        layout='vertical',
                        color = '#FFFF00',
                        spacing='sm',
                        contents=[
                                    TextComponent(
                                        text='由{}到{}隨機產生的號碼'.format(start,end),
                                        color='#000000',
                                        size='lg',
                                        flex = 5
                                    ),
                                    BoxComponent(
                                        layout='baseline',
                                        color = '#FFFF00',
                                        spacing='sm',
                                        contents=[
                                               TextComponent(
                                                       text=' ',
                                                       color='#000000',
                                                       size='xl',
                                                       flex = 4
                                                ),
                                                TextComponent(
                                                       text=str(r),
                                                       color='#000000',
                                                       weight = 'bold',
                                                       size='xxl',
                                                       flex = 5
                                                )
                                        ]
                                    )    
                                    
                        ],
                        
                    ),
                ],
            ),
            footer=BoxComponent(
                layout='vertical',
                spacing='xs',
                contents=[
                    # websiteAction
                    ButtonComponent(
                        style='secondary',
                        color='#FFEE99',
                        height='sm',
                        action=PostbackAction(label='再抽一次',text='抽籤結果!!',data='random/{}/{}'.format(start,end))
                    ),
                    ButtonComponent(
                        style='secondary',
                        color='#FFEE99',
                        height='sm',
                        action=MessageAction(label ='重設範圍',text='draw',)
                    )
                ]
            ),
        )
        message = FlexSendMessage(alt_text="hello", contents=bubble)
        line_bot_api.reply_message(
            event.reply_token,
            message
        )
        
    elif temp[:6] == 'choose':
        bubble = BubbleContainer(
            direction='ltr',
            body=BoxComponent(
                layout='vertical',
                contents=[
                    TextComponent(text= '請把要老天爺幫你選擇的選項回覆給我，然後每一項以分號區隔', weight='bold',size='xl',color='#000000'),
                    TextComponent(text= '希望能夠解決你的選擇障礙...', size='md',wrap=True,color='#888888'),
                    # review
                    SeparatorComponent(color='#000000'),
                    # info
                    BoxComponent(
                        layout='vertical',
                        spacing='sm',
                        contents=[
                            BoxComponent(
                                layout='baseline',
                                contents=[
                                    TextComponent(
                                        text='設定問題-範例:選擇飲料店:',
                                        color='#000000',
                                        size='md'
                                    ),
                                    TextComponent(
                                        text='設定選項-範例:50嵐;清新福全;coco;茶湯會',
                                        color='#000000',
                                        size='md',
                                        wrap=True
                                    ),
                                    SeparatorComponent(color='#000000')
                                ],
                            ),
                            BoxComponent(
                                layout='baseline',
                                contents=[
                                    TextComponent(
                                        text='設定問題-範例:選擇雞排店',
                                        color='#000000',
                                        size='md'
                                    ),
                                    TextComponent(
                                        text='設定選項-範例:豪大雞排;派克雞排;蔥Ya雞;胖老爹雞排',
                                        color='#000000',
                                        size='md'
                                    ),
                                    SeparatorComponent(color='#000000')
                                ],
                            )
                        ],
                    ),
                ],
            ),
            footer=BoxComponent(
                layout='vertical',
                spacing='xs',
                contents=[
                    ButtonComponent(
                        style='secondary',
                        color='#5555FF',
                        height='sm',
                        action=PostbackAction(label='內建問題',data='other',text='請選擇一下喔~')
                    ),
                    ButtonComponent(
                        style='secondary',
                        color='#5555FF',
                        height='sm',
                        action=MessageAction(label='設定問題',text='請輸入要設定抉擇的問題:')
                    ),
                    SeparatorComponent(color='#000000'),
                    ButtonComponent(
                        style='secondary',
                        color='#5555FF',
                        height='sm',
                        action=MessageAction(label='設定選項',text='請輸入要設定的選項，各個選項以分號區隔~')
                    )
                ]
            ),
        )
        message = FlexSendMessage(alt_text="hello", contents=bubble)
        line_bot_api.reply_message(
            event.reply_token,
            message
        )
    elif temp == 'other':
        bubble = BubbleContainer(
            direction='ltr',
            body=BoxComponent(
                layout='vertical',
                contents=[
                    TextComponent(text= '請把選擇需要解決的選擇', weight='bold',size='xl',color='#000000'),
                    TextComponent(text= '希望能夠解決你的選擇障礙...', size='md',wrap=True,color='#888888'),
                    # review
                    SeparatorComponent(color='#000000'),
                ],
            ),
            footer=BoxComponent(
                layout='vertical',
                spacing='xs',
                contents=[
                    ButtonComponent(
                        style='secondary',
                        color='#5555FF',
                        height='sm',
                        action=PostbackAction(label='內建問題',data='other',text='請選擇一下喔~')
                    ),
                    ButtonComponent(
                        style='secondary',
                        color='#5555FF',
                        height='sm',
                        action=MessageAction(label='設定問題',text='請輸入要設定抉擇的問題:')
                    ),
                    SeparatorComponent(color='#000000'),
                    ButtonComponent(
                        style='secondary',
                        color='#5555FF',
                        height='sm',
                        action=MessageAction(label='設定選項',text='請輸入要設定的選項，各個選項以分號區隔~')
                    )
                ]
            ),
        )
        message = FlexSendMessage(alt_text="hello", contents=bubble)
        line_bot_api.reply_message(
            event.reply_token,
            message
        )
            
    elif temp == 'result':     
        print('-------in---')
        t = temp.split('/')
        lot_year = t[1]
        lot_type = t[2]
        num = lottery_stat(lot_type,lot_year)
        if lot_type == 'big-lotto':
            t = '大樂透'
        elif lot_type == 'power':
            t = '威力彩'
        elif lot_type == 'daily539':
            t = '今彩539'
        bubble = BubbleContainer(
            direction='ltr',
            body=BoxComponent(
                layout='vertical',
                contents=[
                    TextComponent(text='爬蟲程式抓取奧索樂透網', size='xs',wrap=True,color='#888888'),
                    TextComponent(text= '{}年\n{}各號碼出現次數'.format(lot_year,t), weight='bold', wrap=True,size='xl',color='#000000'),
                    TextComponent(text= '各個號碼出現次數統計後的結果呈現，透過爬蟲程式免於開網頁慢慢搜尋....', size='xs',wrap=True,color='#888888'),
                    # review
                    SeparatorComponent(color='#000000'),
                    # info
                    BoxComponent(
                        layout='vertical',
                        margin='lg',
                        color = '#FFFF00',
                        spacing='sm',
                        contents=[
                            BoxComponent(
                                layout='vertical',
                                contents=[
                                    TextComponent(
                                        text='號碼   出現次數',
                                        color='#000000',
                                        size='md'
                                    ),
                                    TextComponent(
                                        text=num[:-1],
                                        color='#000000',
                                        size='md',
                                        wrap=True
                                    ),
                                    SeparatorComponent(color='#000000')
                                ],
                            ),          
                        ],
                    ),
                ],
            ),
            footer=BoxComponent(
                layout='vertical',
                spacing='xs',
                contents=[
                    # websiteAction
                    ButtonComponent(
                        style='secondary',
                        color='#DAA520',
                        height='sm',
                        action=PostbackAction(label='其他年份號碼出現次數',data='ball_year/{}'.format(lot_type),text='請稍等...')
                    ),
                    SeparatorComponent(color='#000000'),
                    ButtonComponent(
                        style='secondary',
                        color='#DAA520',
                        height='sm',
                        action=PostbackAction(label='其他遊戲號碼出現次數',data='ballyear',text='請稍等...')
                    )
                ]
            ),
        )
        message = FlexSendMessage(alt_text="hello", contents=bubble)
        line_bot_api.reply_message(
            event.reply_token,
            message
        )
        
    elif temp[:7] == 'ball_st':
        print('-------in---')
        t = temp.split('/')
        lot_year = t[1]
        lot_type = t[2]
        num = lottery_stat(lot_type,lot_year)
        if lot_type == 'big-lotto':
            t = '大樂透'
        elif lot_type == 'power':
            t = '威力彩'
        elif lot_type == 'daily539':
            t = '今彩539'
        bubble = BubbleContainer(
            direction='ltr',
            body=BoxComponent(
                layout='vertical',
                contents=[
                    TextComponent(text='爬蟲程式抓取奧索樂透網', size='xs',wrap=True,color='#888888'),
                    TextComponent(text= '{}年\n{}各號碼出現次數'.format(lot_year,t), weight='bold', wrap=True,size='xl',color='#000000'),
                    TextComponent(text= '各個號碼出現次數統計後的結果呈現，透過爬蟲程式免於開網頁慢慢搜尋....', size='xs',wrap=True,color='#888888'),
                    # review
                    SeparatorComponent(color='#000000'),
                    # info
                    BoxComponent(
                        layout='vertical',
                        margin='lg',
                        color = '#FFFF00',
                        spacing='sm',
                        contents=[
                            BoxComponent(
                                layout='vertical',
                                contents=[
                                    TextComponent(
                                        text='號碼   出現次數',
                                        color='#000000',
                                        size='md'
                                    ),
                                    TextComponent(
                                        text=num[:-1],
                                        color='#000000',
                                        size='md',
                                        wrap=True
                                    ),
                                    SeparatorComponent(color='#000000')
                                ],
                            ),          
                        ],
                    ),
                ],
            ),
            footer=BoxComponent(
                layout='vertical',
                spacing='xs',
                contents=[
                    # websiteAction
                    ButtonComponent(
                        style='secondary',
                        color='#DAA520',
                        height='sm',
                        action=PostbackAction(label='其他年份號碼出現次數',data='ball_year/{}'.format(lot_type),text='請稍等...')
                    ),
                    SeparatorComponent(color='#000000'),
                    ButtonComponent(
                        style='secondary',
                        color='#DAA520',
                        height='sm',
                        action=PostbackAction(label='其他遊戲號碼出現次數',data='ballyear',text='請稍等...')
                    )
                ]
            ),
        )
        message = FlexSendMessage(alt_text="hello", contents=bubble)
        line_bot_api.reply_message(
            event.reply_token,
            message
        )

    elif temp[:9] == 'ball_year':
        print('-------in---')
        print(temp)
        t = temp.split('/')
        lot_type = t[1]
        print(lot_type+'-----------')
        Carousel_template = lottery_year(lot_type)
        line_bot_api.reply_message(event.reply_token,Carousel_template)
         
    elif temp[:8] == 'ball_num':
        print('-------in---')
        t = temp.split('/')
        lot_type = t[1]
        num = lottery_all_num(lot_type)
        if lot_type == 'big-lotto':
            t = '大樂透'
        elif lot_type == 'power':
            t = '威力彩'
        elif lot_type == 'daily539':
            t = '今彩539'
        bubble = BubbleContainer(
            direction='ltr',
            body=BoxComponent(
                layout='vertical',
                contents=[
                    TextComponent(text='爬蟲程式抓取樂透雲內容', size='xs',wrap=True,color='#888888'),
                    TextComponent(text= '{}歷史開獎紀錄'.format(t), weight='bold', wrap=True,size='xl',color='#000000'),
                    TextComponent(text= '各個號碼個期紀錄，僅列出最近35筆紀錄，透過爬蟲程式免於開網頁慢慢搜尋....', size='xs',wrap=True,color='#888888'),
                    # review
                    SeparatorComponent(color='#000000'),
                    # info
                    BoxComponent(
                        layout='vertical',
                        margin='lg',
                        color = '#FFFF00',
                        spacing='sm',
                        contents=[
                            BoxComponent(
                                layout='vertical',
                                contents=[
                                    TextComponent(
                                        text='    日期          {}中獎號碼'.format(t),
                                        color='#000000',
                                        size='md'
                                    ),
                                    TextComponent(
                                        text=num,
                                        color='#000000',
                                        size='xs',
                                        wrap=True
                                    ),
                                    SeparatorComponent(color='#000000')
                                ],
                            ),          
                        ],
                    ),
                ],
            ),
            footer=BoxComponent(
                layout='vertical',
                spacing='xs',
                contents=[
                    # websiteAction
                    ButtonComponent(
                        style='secondary',
                        color='#DAA520',
                        height='sm',
                        action=MessageAction(label='近期開獎紀錄',text='lottery')
                    ),
                    SeparatorComponent(color='#000000'),
                    ButtonComponent(
                        style='secondary',
                        color='#DAA520',
                        height='sm',
                        action=PostbackAction(label='其他遊戲歷史開獎紀錄',data='ball_all_num',text='請稍等...')
                    )
                ]
            ),
        )
        message = FlexSendMessage(alt_text="hello", contents=bubble)
        line_bot_api.reply_message(
            event.reply_token,
            message
        )
        
    elif temp == 'ball_all_num':
        buttons_template = TemplateSendMessage(
            alt_text='歷史開獎紀錄',
            template=ButtonsTemplate(
                title='歷史開獎紀錄',
                text='請選擇要查詢的遊戲歷史開獎紀錄',
                thumbnail_image_url='https://i.imgur.com/sMu1PJN.jpg',
                actions=[
                    PostbackTemplateAction(
                        label='大樂透歷史紀錄',
                        data='ball_num/big-lotto',
                        text = '選擇了大樂透...'
                    ),
                    PostbackTemplateAction(
                        label='今彩539歷史紀錄',
                        data='ball_num/daily539',
                        text = '選擇了今彩539...'
                    ),
                    PostbackTemplateAction(
                        label='威力彩歷史紀錄',
                        data='ball_num/power',
                        text = '選擇了威力彩...'
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, buttons_template)
        
    elif temp == 'ballyear':
        buttons_template = TemplateSendMessage(
            alt_text='歷年號碼出現次數',
            template=ButtonsTemplate(
                title='歷年號碼出現次數',
                text='請選擇一下',
                thumbnail_image_url='https://i.imgur.com/sMu1PJN.jpg',
                actions=[
                    PostbackTemplateAction(
                        label='大樂透統計',
                        data='ball_year/big-lotto'
                    ),
                    PostbackTemplateAction(
                        label='今彩539統計',
                        data='ball_year/power'
                    ),
                    PostbackTemplateAction(
                        label='威力彩統計',
                        data='ball_year/daily539'
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, buttons_template)
   
    elif temp == 'ball':
        big = ''
        r539 = ''
        r3 = ''
        print('---in--------')
        for i in  random.sample([str(i) for i in range(1,50)],6):
            if len(i) !=2 :
                big += '0{},'.format(i)
            else:
                big += '{},'.format(i)
        for i in random.sample([str(i) for i in range(1,40)],5):
            if len(i) !=2 :
                r539 += '0{},'.format(i)
            else:
                r539 += '{},'.format(i)
        
        for i in  random.sample([str(i) for i in range(1,39)],6):
            if len(i) !=2 :
                r3 += '0{},'.format(i)
            else:
                r3 += '{},'.format(i)
        r3 = r3[:-1] + '\n第二區:0{}'.format(random.sample([i for i in range(1,8)],1)[0])
        print(r3)
        bubble = BubbleContainer(
            direction='ltr',
            body=BoxComponent(
                layout='vertical',
                contents=[
                    TextComponent(text='僅供參考', size='sm',wrap=True,color='#008844'),
                    TextComponent(text='幸運號碼', size='xxl',color='#000000'),
                    SeparatorComponent(color='#000000'),
                    # review
                    SeparatorComponent(color='#000000'),
                    # info
                    BoxComponent(
                        layout='vertical',
                        margin='lg',
                        color = '#FFFF00',
                        spacing='sm',
                        contents=[
                            BoxComponent(
                                layout='baseline',
                                color = '#FFFF00',
                                contents=[
                                    TextComponent(
                                        text='大樂透',
                                        color='#000000',
                                        weight='bold',
                                        size='md',
                                        flex=2
                                    ),
                                    TextComponent(
                                        text=big[:-1],
                                        weight='bold',
                                        color='#FF3333',
                                        size='lg',
                                        flex=5
                                    )
                                ],
                            ),
                            BoxComponent(
                                layout='baseline',
                                color = '#FFFF00',
                                contents=[
                                    TextComponent(
                                        text='今彩539',
                                        color='#000000',
                                        weight='bold',
                                        size='md',
                                        flex = 2
                                    ),
                                    TextComponent(
                                        text=r539[:-1],
                                        weight='bold',
                                        color='#FF3333',
                                        size='lg',
                                        flex=5
                                    )
                                ],
                            ),
                            BoxComponent(
                                layout='horizontal',
                                color = '#FFFF00',
                                contents=[
                                    TextComponent(
                                        text='威力彩',
                                        color='#000000',
                                        weight='bold',
                                        size='md',
                                        gravity = 'center',
                                        flex=2
                                    ),
                                    TextComponent(
                                        text=r3,
                                        weight='bold',
                                        color='#FF3333',
                                        size='lg',
                                        wrap=True,
                                        flex=5
                                    )
                                ],
                            ),
                            
                        ],
                    ),
                ],
            ),
            footer=BoxComponent(
                layout='vertical',
                spacing='xs',
                contents=[
                    # websiteAction
                    ButtonComponent(
                        style='primary',
                        color='#DAA520',
                        height='sm',
                        action=PostbackAction(label='歷年號碼出現次數',data='ballyear',text='請稍等...')
                    ),
                    SeparatorComponent(color='#000000'),
                    ButtonComponent(
                        style='primary',
                        height='sm',
                        color='#DAA520',
                        action=PostbackAction(label='再來一組', data='ball',text='好運到來...')
                    )
                ]
            ),
        )
        message = FlexSendMessage(alt_text="hello", contents=bubble)

        line_bot_api.reply_message(
            event.reply_token,
            message
        )

    elif temp[:8] == 'carousel':
        t = temp.split('/')
        pa = int(t[1])
        print('--------be else-------{}---{}'.format(pa,str(type(pa))))
        pa += 1
        print('--------af else-------{}'.format(pa))
        keyword = t[2]
        t = carousel_template(keyword,page=pa)
        line_bot_api.reply_message(
            event.reply_token,
            t)

    elif temp[0:6] == 'listen':
        url = temp[6:]
        if url == '音樂版權未授權~':
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text='音樂版權未授權~'))
        else:
            line_bot_api.reply_message(
                event.reply_token,
                AudioSendMessage(original_content_url=url,duration=30000)
            )
    elif temp[0:4] == 'next':
        range_num = int(temp[4:-3])
        if range_num > 50:
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text='已經到底了喔!!'))
        else:
            category = int(temp[-3:])
            template = type_music(category,range_num)    
            line_bot_api.reply_message(event.reply_token,template)
    elif temp[0:4] == 'porn':
        print('------in------')
        t = temp.split('/')
        index = int(t[1])
        keyword = t[2]
        index += 1
        try:
            buttons_template = porn_video_template(keyword,judge,index)
            line_bot_api.reply_message(event.reply_token, buttons_template)
        except IndexError:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text='已經到底了喔'))
    elif temp[0:5] == 'video':
        t = temp.split('/')
        print('----t-----'+str(t))
        keyword = t[1]
        video_url = t[2]
        video_url = 'https://www.youtube.com/watch?v={}'.format(video_url)
        video_url,img = yvideo(video_url)
        line_bot_api.reply_message(
                event.reply_token,
                VideoSendMessage(
                    original_content_url=video_url,
                    preview_image_url=img))
    elif temp[:5] == 'image':
     print('------postback'+str(temp))
     t = temp.split('/')
     path = '/{}/{}'.format(t[2],t[3])
     print('postback---------'+str(path))
     img_id = 1
     t = fb.get('/pic',None)
     if t!=None:
         count = 1
         for key,value in t.items():
            if count == len(t):#取得最後一個dict項目
                img_id = int(value['id'])+1
            count+=1
     try:

        client = ImgurClient(client_id, client_secret, access_token, refresh_token)
        config = {
            'album': album_id,
            'name' : img_id,
            'title': img_id,
            'description': 'Cute kitten being cute on'
        }
        client.upload_from_path(path, config=config, anon=False)
        os.remove(path)
        image_reply = check_pic(img_id)
        line_bot_api.reply_message(event.reply_token,[TextSendMessage(text='上傳成功'),image_reply])
     except  Exception as e:
        t = '上傳失敗'+str(e.args)
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text=t))



# 處理圖片
@handler.add(MessageEvent,message=ImageMessage)
def handle_msg_img(event):
    message_content = line_bot_api.get_message_content(event.message.id)
    with tempfile.NamedTemporaryFile(prefix='jpg-', delete=False) as tf:
        for chunk in message_content.iter_content():
            tf.write(chunk)
        tempfile_path = tf.name
    path = tempfile_path

    buttons_template = template_img(path)
    line_bot_api.reply_message(event.reply_token,buttons_template)



# 處理訊息:
@handler.add(MessageEvent, message=TextMessage)
def handle_msg_text(event):
    profile = line_bot_api.get_profile(event.source.user_id)
    user_name = profile.display_name
    picture_url = profile.picture_url
    user_id = event.source.user_id
#    if True:
#        if fb.get('/{}'.format(event.source.user_id),None) != None:
#            line_bot_api.reply_message(
#            event.reply_token,
#            TextSendMessage(text='successful'+event.message.text))
#        else:
#            print('no')
#    ----------------抽數字-----------------------
    if event.message.text == '請輸入起始數字-----------':
        t = '起始數字'
        fb.post('/{}/temp'.format(user_id),'起始數字')  
    elif event.message.text == '請輸入結束數字-----------':
        t = '結束數字'
        fb.post('/{}/temp'.format(user_id),'結束數字')
    elif event.message.text.isdigit():
        temp = int(event.message.text)
        t = fb.get('/{}/temp'.format(user_id),None)
        if not t:
            return
        elif '起始數字' in list(t.values()):
            fb.post('/{}/start'.format(user_id),temp)
        else:
            fb.post('/{}/end'.format(user_id),temp)
        fb.delete('/{}/temp'.format(user_id),None)
        bubble = process_choose(user_id)
        message = FlexSendMessage(alt_text="hello", contents=bubble)
        line_bot_api.reply_message(
                event.reply_token,
                [TextSendMessage(text='{}為{}'.format(list(t.values())[0],temp)),message])
#    -----------------自訂的問題-----------------------
    elif event.message.text == '請輸入要設定抉擇的問題:':
        fb.post('/{}/num'.format(user_id),'問題')  
    elif event.message.text == '請輸入要設定的選項，各個選項以分號區隔~':   
        fb.post('/{}/num'.format(user_id),'選項')  
    elif True:
        t = fb.get('/{}/num'.format(user_id),None)
        if not t:
            print('in')
        elif '問題' in list(t.values()):
            fb.post('/{}/ques_num'.format(user_id),event.message.text)
        else:
            fb.post('/{}/opti_num'.format(user_id),event.message.text)
        fb.delete('/{}/num'.format(user_id),None)
        bubble = process_draw(user_id)
        message = FlexSendMessage(alt_text="hello", contents=bubble)
        line_bot_api.reply_message(
                event.reply_token,
                [TextSendMessage(text='{}為{}'.format(list(t.values())[0],temp)),message])
    else:
        t = fb.get('/{}/temp'.format(user_id),None)
        if t != None:
            if len(list(t.values())) != 0:
                line_bot_api.reply_message(
                    event.reply_token,
                    [TextSendMessage(text='請輸入正確的起始及結束數字'),TextSendMessage(text='只能是數字，不能包含文字喔🙏')])
        print('------out------')
    if event.message.text.lower() == "eyny":
        content = eyny_movie()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))

    elif event.message.text.lower() == 'draw':
        fb.delete('/{}/end'.format(user_id),None)
        fb.delete('/{}/start'.format(user_id),None)
        print('in')
        bubble = process_draw(user_id)
        message = FlexSendMessage(alt_text="hello", contents=bubble)
        line_bot_api.reply_message(
            event.reply_token,
            message
        )
        
    elif event.message.text.lower() == "choose":
        
        if fb.get('/{}'.format(event.source.user_id),None) == None:
            fb.post('/{}'.format(event.source.user_id), {'DB':'yes'})
        buttons_template = TemplateSendMessage(
            alt_text='抉擇領域template',
            template=ButtonsTemplate(
                title='抉擇類型',
                text='請選擇一下，想要老天爺替你選擇的問題',
                thumbnail_image_url='https://i.imgur.com/ISBqTUQ.jpg',
                actions=[                              
                    PostbackTemplateAction(
                        label='要不要問題',
                        data='first/yesno'
                    ),
                    PostbackTemplateAction(
                        label='買不買問題',
                        data='first/buy'
                    ),
                    PostbackTemplateAction(
                        label='是不是問題',
                        data='first/yes'
                    ),
                    PostbackTemplateAction(
                        label='新增問題',
                        data='choose'
                    )
                ]
            )
        )
        line_bot_api.reply_message(
            event.reply_token,
            [TextSendMessage(text=' -------已經進入抉擇領域了------- '),buttons_template])
#    elif event.message.text.lower() == "get":
#        result = fb.get('note',None)
#        result2 = firebase.get('note', None, {'print': 'pretty'}, {'X_FANCY_HEADER': 'VERY FANCY'})
#        line_bot_api.reply_message(
#            event.reply_token,
#            TextSendMessage(text=str(result)+str(result2)))
#        
#    elif event.message.text.lower() == "save":
#         data = {'name': 'Ozgur Vatansever', 'age': 26,
#            'created_at': datetime.datetime.now()}
#         snapshot = firebase.post('/users', data)
#         print(snapshot['name'])
#    elif event.message.text.lower() == 'test':
#        print('-----------in')
#        data_UserData = usermessage.query.all()
#        history_dic = {}
#        history_list = []
#        for _data in data_UserData:
#            history_dic['id'] = _data.id
#            history_dic['User_Id'] = _data.user_id
#            history_dic['Mesaage'] = _data.message
#            history_dic['Date'] = _data.birth_date
#            history_list.append(history_dic)
#            history_dic = {}
#        line_bot_api.reply_message(event.reply_token,TextSendMessage(text= str(history_list)))  
#    elif event.message.text.lower() == 'clear':
#        t = db.session.query(usermessage).delete()
#        db.session.commit()
#        print('end------------',str(t))
#        line_bot_api.reply_message(event.reply_token,TextSendMessage(text= 'successfully'))  
#              
#    elif event.message.text.lower() == 'input':
#        print('-----------in')
#        data_UserData = usermessage.query.filter_by(message='hi').first()
#        print('end------------',str(data_UserData))
#        line_bot_api.reply_message(event.reply_token,TextSendMessage(text= str(data_UserData)))  
#           
        
    elif google_picture(event.message.text) != None:
        image = google_picture(event.message.text)
        line_bot_api.reply_message(event.reply_token,image)
        return
   
    elif event.message.text == "PanX泛科技":
        content = panx()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))

    elif drink_menu(event.message.text) != None:
        image = drink_menu(event.message.text)
        image.append(button_template(user_name,event.message.text[:-4],'請問一下~','有想要進一步的資訊嗎?',picture_url))
        line_bot_api.reply_message(event.reply_token,image)
        return
    elif event.message.text == "近期上映電影":
        content = movie()
        template = movie_template()
        line_bot_api.reply_message(
            event.reply_token,[
                    TextSendMessage(text=content),
                    template
            ]
        )
#https://kma.kkbox.com/charts/api/v1/daily?category=297&date=2018-12-17&lang=tc&limit=50&terr=tw&type=song
    elif event.message.text == "kkbox-華語":
        template = type_music(297)
        line_bot_api.reply_message(event.reply_token,template)
#https://kma.kkbox.com/charts/api/v1/daily?category=390&date=2018-12-17&lang=tc&limit=50&terr=tw&type=song
    elif event.message.text == "kkbox-西洋":
        template = type_music(390)
        line_bot_api.reply_message(event.reply_token,template)
    elif event.message.text == "kkbox-日語":
        template = type_music(308)
        line_bot_api.reply_message(event.reply_token,template)
    elif event.message.text == "kkbox-台語":
        template = type_music(304)
        line_bot_api.reply_message(event.reply_token,template)
    elif event.message.text.lower() == "kkbox":
            buttons_template = TemplateSendMessage(
            alt_text='kkbox template',
            template=ButtonsTemplate(
                title='kkbox歌曲熱門排行',
                text='請選擇需要選項',
                thumbnail_image_url='https://i.imgur.com/WWJ1ltx.jpg',
                actions=[
                    MessageTemplateAction(
                        label='華語',
                        text='kkbox-華語'
                    ),
                    MessageTemplateAction(
                        label='西洋',
                        text='kkbox-西洋'
                    ),
                    MessageTemplateAction(
                        label='日語',
                        text='kkbox-日語'
                    ),
                    MessageTemplateAction(
                        label='台語',
                        text='kkbox-台語'
                    )
                ]
            )
        )
            line_bot_api.reply_message(event.reply_token, buttons_template)

    
    elif event.message.text == "觸電網-youtube":
        target_url = 'https://www.youtube.com/user/truemovie1/videos'
        rs = requests.session()
        res = rs.get(target_url, verify=False)
        soup = bf(res.text, 'html.parser')
        seqs = ['https://www.youtube.com{}'.format(data.find('a')['href']) for data in soup.select('.yt-lockup-title')]
        template = movie_template()
        line_bot_api.reply_message(
            event.reply_token, [
                TextSendMessage(text=seqs[random.randint(0, len(seqs) - 1)]),
                TextSendMessage(text=seqs[random.randint(0, len(seqs) - 1)]),
                TextSendMessage(text=seqs[random.randint(0, len(seqs) - 1)]),
                template
            ])
   
    elif event.message.text.lower() == "ramdom picture":
        client = ImgurClient(client_id, client_secret)
        images = client.get_album_images(album_id)
        index = random.randint(0, len(images) - 1)
        url = images[index].link
        image_message = ImageSendMessage(
            original_content_url=url,
            preview_image_url=url
        )
        line_bot_api.reply_message(event.reply_token,image_message)


    elif event.message.text.lower() == "movie":
        buttons_template = movie_template()
        line_bot_api.reply_message(event.reply_token, buttons_template)
    elif event.message.text == "蘋果即時新聞":
        content = apple_news()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
        
    elif event.message.text.lower() == "news":
        buttons_template = TemplateSendMessage(
            alt_text='news template',
            template=ButtonsTemplate(
                title='新聞類型',
                text='請選擇',
                thumbnail_image_url='https://i.imgur.com/GoAYFqv.jpg',
                actions=[
                    MessageTemplateAction(
                        label='蘋果即時新聞',
                        text='蘋果即時新聞'
                    ),
                    MessageTemplateAction(
                        label='天下雜誌',
                        text='天下雜誌'
                    ),
                    MessageTemplateAction(
                        label='PanX泛科技',
                        text='PanX泛科技'
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, buttons_template)
    elif event.message.text == "天下雜誌":
        content = magazine()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=content))
 
    elif event.message.text.lower() == 'post':
        bubble = BubbleContainer(
            direction='ltr',
            hero=ImageComponent(
                    url='https://i.imgur.com/qXqg5qA.jpg',
                    size='full',
                    aspect_ratio='5:3',
                    aspect_mode='cover',
                    action=URIAction(uri='https://github.com/kevin1061517', label='label'),
            ),
            body=BoxComponent(
                layout='vertical',
                contents=[
                    # title
                    TextComponent(text='Content', weight='bold', size='xl',color='#006400'),
                    SeparatorComponent(margin='xl',color='#000000'),
                    # review
                    TextComponent(
                            text='''現在在練習python各種語法~藉由這次的project，讓我更加熟悉python語法與邏輯，這個LineBot有各種功能，可以把youtube網址拉進來，LineBot會傳來網址影片，你就可以利用右下角的下載鍵，以及抓出菜單等等功能，就可以下載到手機端了😜，如下:\n語法:\n1.阿滴英文yout\n關鍵字後面加上yout，就可以抓出影片了\n2.50嵐menu\n餐廳名字後面加上menu，就可以抓出餐廳單\n3.馬英九pic\n搜尋照片關鍵字加上pic，就可以馬上幫你抓到要搜尋的照片\n -------------------- 18禁 -------------------- \n4.李宗瑞porn\n搜尋關鍵字加上porn，就可以有成人影片彈出來🙏''',
                            size='sm',wrap=True,color='#2E8B57'
                    ),
                    SeparatorComponent(margin='xl',color='#000000'),
                    TextComponent(
                            text='承認不勇敢 你能不能別離開很多愛不能重來 我應該釋懷在街頭徘徊 下雨時為你撐傘對你的愛成阻礙 祝福你愉快',
                            size='sm',wrap=True,color='#2E8B57'
                    ),
                    SeparatorComponent(margin='xl',color='#000000'),
                    TextComponent(
                            text='承認不勇敢 你能不能別離開很多愛不能重來 我應該釋懷在街頭徘徊 下雨時為你撐傘對你的愛成阻礙 祝福你愉快',
                            size='sm',wrap=True,color='#2E8B57'
                    ),
                    # info
                    BoxComponent(
                        layout='vertical',
                        margin='lg',
                        color = '#FFFF00',
                        spacing='sm',
                        contents=[
                            BoxComponent(
                                layout='baseline',
                                color = '#FFFF00',
                                spacing='sm',
                                contents=[
                                    TextComponent(
                                        text='Developer',
                                        color='#000000',
                                        weight='bold',
                                        align="end",
                                        size='xxs',
                                        flex=5
                                    ),
                                    TextComponent(
                                        text='Kevin',
                                        wrap=True,
                                        weight='bold',
                                        align="end",
                                        color='#000000',
                                        size='xxs',
                                        flex=1
                                    )
                                ],
                            ), 
                        ],
                    ),
                    SeparatorComponent(),
                ],
            ),
            footer=BoxComponent(
                layout='vertical',
                spacing='sm',
                contents=[
                    # callAction, separator, websiteAction
#                    SpacerComponent(size='sm'),
                    # callAction
                    ButtonComponent(
                        style='primary',
                        color = '#FFFF00',
                        height='sm',
                        action=URIAction(label='CALL', uri='tel:0935593342'),
                    ),
                    # separator
                    SeparatorComponent(),
                    # websiteAction

                ]
            ),
        )
        message = FlexSendMessage(alt_text="hello", contents=bubble)

        line_bot_api.reply_message(
            event.reply_token,
            message
        )
    elif event.message.text.lower() == 'lottery':
        big,b539,bwei = lottery()
        big_txt = ''
        b539_txt = ''
        bwei = ''
        for t,c in enumerate(big,1):
            if t%3==0:
                big_txt += '特別號:'
            big_txt += str(c+'\n')
        big_txt = big_txt[:-1]
        for t,c in enumerate(b539,0):
            b539_txt +='{}\n'.format(str(c))
        b539_txt = b539_txt[:-1]
        for t,c in enumerate(big,1):
            if t%3==0:
                bwei += '二區:'
            bwei +='{}\n'.format(str(c))
        bwei = bwei[:-1]
        bubble = BubbleContainer(
            direction='ltr',
            hero=ImageComponent(
                    url='https://i.imgur.com/9IUzhOT.jpg',
                    aspectMode = 'cover',
                    aspect_ratio='11:3',
                    size='full',
                    backgroundColor = '#FFD700',
                    action=URIAction(uri='https://github.com/kevin1061517', label='label'),
            ),
            body=BoxComponent(
                layout='vertical',
                contents=[
                    TextComponent(text='祝你中獎', weight='bold', size='md'),
                    BoxComponent(
                        layout='vertical',
                        margin='lg',
                        spacing='xs',
                        contents=[
                            BoxComponent(
                                margin = 'sm',
                                layout='horizontal',
                                contents=[
                                   ImageComponent(
                                        url='https://i.imgur.com/T6rFvGm.png',
                                        size='md',
                                        aspect_ratio='5:5',
                                        flex=2,
                                        gravity='center',
                              
                                    ),
                                    TextComponent(
                                        text=big_txt,
                                        wrap=True,
                                        color='#666666',
                                        size='md',
                                        flex=5
                                    )
                                ],
                            ),
                            SeparatorComponent(color='#000000'),
                            BoxComponent(
                                layout='horizontal',
                                margin = 'sm',
                                contents=[
                                    ImageComponent(
                                        url='https://i.imgur.com/DQrt8Xz.png',
                                        size='md',
                                        aspect_ratio='5:5',
                                        flex=2,
                                        gravity='center'
                                     
                                    ),
                                    TextComponent(
                                        text=b539_txt,
                                        wrap=True,
                                        color='#666666',
                                        size='md',
                                        flex=5,
                                    ),
                                ],
                            ),
                            SeparatorComponent(color='#000000'),
                            BoxComponent(
                                layout='horizontal',
                                margin = 'sm',
                                contents=[
                                    ImageComponent(
                                        url='https://i.imgur.com/nXq6wrd.png',
                                        size='md',
                                        aspect_ratio='5:5',
                                        flex=2,
                                        gravity='center'
                                      
                                    ),
                                    TextComponent(
                                        text=bwei,
                                        wrap=True,
                                        color='#666666',
                                        size='md',
                                        flex=5,
                                    ),
                                ],
                            ),
                        ],
                    ),
                    SeparatorComponent(color='#000000'),
                ],
            ),
            footer=BoxComponent(
                layout='vertical',
                spacing='xs',
                contents=[
                    # websiteAction
                    ButtonComponent(
                        style='primary',
                        height='sm',
                        action=PostbackAction(label='歷年開獎紀錄',data='ball_all_num',text='歷年號碼~詳細內容參考至台彩官網')
                    ),
                    SeparatorComponent(color='#000000'),
                    ButtonComponent(
                        style='primary',
                        color='#DAA520',
                        height='sm',
                        action=PostbackAction(label='開門見喜💎️', data='ball',text='您的幸運號碼...')
                    )
                ]
            ),
        )
        message = FlexSendMessage(alt_text="hello", contents=bubble)
        line_bot_api.reply_message(
            event.reply_token,
            message
        )
    elif event.message.text.lower() == 'quick reply':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text='Quick reply',
                quick_reply=QuickReply(
                    items=[
                        QuickReplyButton(
                            action=MessageAction(label="第五人格", text="微博-第五人格")
                        ),
                        QuickReplyButton(
                            action=MessageAction(label="kkbox-華語", text="kkbox-華語")
                        ),
                        QuickReplyButton(
                            action=MessageAction(label="hank like2", text="hank like2")
                        ),
                        QuickReplyButton(
                            action=MessageAction(label="hank like3", text="hank like3")
                        ),
                        QuickReplyButton(
                            action=MessageAction(label="hank like5", text="hank like5")
                        ),
                        QuickReplyButton(
                            action=CameraAction(label="Camera")
                        ),
                        QuickReplyButton(
                            action=LocationAction(label="=Location")
                        ),
                    ])))

    elif re.search(r'yout$',event.message.text.lower())!=None:
        keyword = event.message.text.lower()[:-4]
        carousel = carousel_template(keyword)
        line_bot_api.reply_message(event.reply_token, carousel)

#    供下載影片
    elif re.search(r'^https://www.youtu.*',event.message.text) != None or re.search(r'^https://youtu.be.*',event.message.text) !=None:
        t = event.message.text 
        video_url,img = yvideo(t)
        line_bot_api.reply_message(
            event.reply_token,
            [TextSendMessage(text='供你下載製手機端，本人僅供學術用途，不負法律責任'),
             VideoSendMessage(
                     original_content_url=video_url,
                     preview_image_url=img)]
        )
    elif re.search(r'eng$',event.message.text.lower())!=None:
        keyword = event.message.text.lower()[:-3]
        keyword = keyword.replace(' ','')
        print('-----------'+keyword)
        message = integer_word(keyword)
        
        line_bot_api.reply_message(
            event.reply_token,
            message
        )
        
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
