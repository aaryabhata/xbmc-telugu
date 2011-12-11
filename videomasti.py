import sys
import os
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import urllib
import urllib2
import re
import htmlentitydefs
import urlresolver
from string import ascii_lowercase

try:
    import json
except ImportError:
    import simplejson as json

AddonName = "VideoMasti:"

DEBUGLEVEL = 1
Addon = xbmcaddon.Addon(id=os.path.basename(os.getcwd()))

user_agent = 'Mozilla/5.0 (X11; Linux i686; rv:8.0) Gecko/20100101 Firefox/8.0'

#regexes for getting videoids for different sites
regexp = {
    'youtube.1': re.compile(r'<param name="movie" value="https?://www.youtube.com/v/(.*?)&'),
    'youtube.2': re.compile(r'<param name="movie" value="https?://www.youtube.com/v/(.*?)\?'),
    
    'videozer.1': re.compile(r'<param name="movie" value="http://(?:www\.)?videozer.com/e(?:mbed)?/(.*?)"'),
    'videozer.2' : re.compile(r'<meta content="http://videozer.com/video/(.*?)"'),
    
    'videobb.1': re.compile(r'<param name="movie" value="http://(?:www\.)?videobb.com/e(?:mbed)?/(.*?)"'),
    'videobb.2' : re.compile(r'<meta content="http://videobb.com/video/(.*?)"'),
      
    'videobb.3' : re.compile('''<param name="movie" value="http://www.videobb.com/player/player.swf\?setting=(.*?)" >'''),
    'hostingbulk': re.compile(r'http://hostingbulk.com/(.*?).html'),
    'megavideo.1' : re.compile(r'''<param name="movie" value="http://www.megavideo.com/v/(.*?)"'''),
    'zshare.1' : re.compile(r'''<iframe src="http://www.zshare.net/(.*)"''')
}

#regexes for different urls
vmregex = {
    'Recently Written' : '''<li><a href='(.*?)' title=(.*?)</a></li>''',
    'Telugu Movies' : '''<li><a href="(.*?)"><span class="head">(.*?)</span></a></li>'''
    }

def Msg(message):
    print AddonName + message
    
def debug(message):
    if DEBUGLEVEL >= 0:
        Msg(message) 

def info(message):
    if DEBUGLEVEL >= 1:
        Msg(message)

def trace(message):
    if DEBUGLEVEL >=2:
        Msg(message)

class SmartRedirectHandler(urllib2.HTTPRedirectHandler):     
    def http_error_301(self, req, fp, code, msg, headers):  
        result = urllib2.HTTPRedirectHandler.http_error_301( 
            self, req, fp, code, msg, headers)              
        result.status = code                                 
        return result                                       

    def http_error_302(self, req, fp, code, msg, headers):   
        result = urllib2.HTTPRedirectHandler.http_error_302(
            self, req, fp, code, msg, headers)              
        result.status = code                                
        return result
    
                   
def getResponse(url):
    #opener = urllib2.build_opener(MyHTTPRedirectHandler)
    #urllib2.install_opener(opener)
    req = urllib2.Request(url)
    req.add_header('User-Agent', user_agent)
    req.add_header("Host", 'videomasti.net')
    req.add_header('Connection', "keep-alive")
    req.add_header('Accept-Language','en-us,en;q=0.5')
    req.add_header('Accept-Encoding','gzip, deflate')
    req.add_header('Accept-Charset','ISO-8859-1,utf-8;q=0.7,*;q=0.7')
    req.add_header('Accept','text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
    response = urllib2.urlopen(url)
    link = response.read()
    response.close()
    trace("Response  info %s" %(response.info()))
    return link

def videobb(videoid):
    import simplejson as json
    import base64
    url2='http://www.videobb.com/player_control/settings.php?v='+videoid
    settingsObj = json.load(urllib.urlopen(url2))['settings']
    imgUrl = str(settingsObj['config']['thumbnail'])
    finalurl = str(base64.b64decode(settingsObj['config']['token1']))
    return finalurl

def unescape(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)

#This function is invoked at startup
def STARTUP():    
    addDir('Recently Written', 'http://www.videomasti.net', 0, '')
    for c in ascii_lowercase:
        addDir('Telugu Movies-'+c.upper(), 'http://videomasti.net/telugu-movie-index-'+ c +'/', 0, '')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def CATEGORIES(title, url):
    debug("CATEGORIES called with url %s" %url)
    link = getResponse(url)
    
    if title == 'Recently Written':
        link = re.compile('''<h2>Recently Written</h2>.*?<ul>(.*?)</ul>''',re.I|re.MULTILINE|re.DOTALL).findall(link)[0]
    
    elif title.find('Telugu Movies')!= -1:
        link = re.compile('''<div class=(.*?)</div>''', re.I|re.MULTILINE|re.DOTALL).findall(link)[0]
    
    match = re.compile(vmregex[title.split('-')[0]]).findall(link)
    
    for url, title in match:
        if type(title) is str:
            title = unicode(title, errors = 'ignore')
        title = unescape(title).encode('ascii', 'ignore')
        addDir(title, url, 1, '')
    
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def SORTMETHOD(url):
    debug("SORTMETHOD: url is %s" %url)
    
    link = getResponse(url)
    match = []
    watchMatch = re.compile(r'''<a href=["'](.*?)['"]>(Wa.*?)</a>''',re.I).findall(link)
    
    if watchMatch:
        for tuple in watchMatch:
            if tuple[0].find('href') == -1:
                match.append(tuple) 

    partMatch = re.compile(r'''<a href=["'](.*?)["']>(Par.*?)</a>''',re.I).findall(link)
    
    if partMatch:
        for tuple in partMatch:
            match.append(tuple)
    
    debug("SORTMETHOD match is %s" %match)
    
    for link, title in match:
        addDir(title, link, 2,'')
        
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def VIDEOLIST(url):
    debug("VM:VIDEOLIST called with url %s" %url)
    
    if url[0] == "/":
        url = "http://www.videomasti.net" + url
    
    link = getResponse(url)
    
    for key, pat in regexp.items():
        m = pat.findall(link)
        if m:
            debug("VIDEOLIST match is %s" %m)
            if  key in ['youtube.2','videobb.1','videozer.1','videozer.2','videobb.2', 'youtube.1'] :
                try:
                    url = urlresolver.HostedMediaFile('', key.split('.')[0]+'.com', m[0]).resolve()
                except:
                    pass
            
            elif key in ['megavideo.1']:
                try:
                    url = urlresolver.HostedMediaFile('', key.split('.')[0]+'.com', m[0][0:8]).resolve()
                except:
                    pass
            addLink(key.split('.')[0], url, 3, "")
            break
    
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
          
def get_params():
    print "get_params enter"
    param = []
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if (params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]
    
    print "get_params: ret: %s" %param       
    return param

def addLink(name, url, mode, iconimage):
    debug("addLink called with  %s:%s"%(name,url))
    ok=True
    liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo( type="Video", infoLabels={ "Title": name } )
    liz.setProperty("IsPlayable","true")
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz,isFolder=False)
    ok=xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER).play(url, liz)
    return ok

def addDir(name, url, mode, iconimage):
    debug("addDir called with %s" %url)
    u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode) + "&name=" + urllib.quote_plus(name)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok


def main():
    
    params = get_params()
    url = None
    name = None
    mode = None
    page = 1

    try:
        url = urllib.unquote_plus(params["url"])
    except:
        pass
    try:
        name = urllib.unquote_plus(params["name"])
    except:
        pass
    try:
        mode = int(params["mode"])
    except:
        pass
    try:
        page = int(params["page"])
    except:
        pass
    
    if mode == None or url == None or len(url) < 1:
        STARTUP()
    
    elif mode == 0:
        CATEGORIES(name, url)
           
    elif mode == 1:
        SORTMETHOD(url)
            
    elif mode == 2:
        VIDEOLIST(url)


if __name__ == "__main__":
    main()

