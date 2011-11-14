import web, dacp, itunes, random, pylast, cgi, json, unicodedata

from BeautifulSoup import BeautifulSoup

API_KEY = "eb10930c856506bfdcfdf148fa126dd2"
API_SECRET = "97773028f5011fe95c1afc1883edca58"
USERNAME = "elsmorian"

SERVICE_NAME = 'WebDACP'



network = pylast.LastFMNetwork(api_key=API_KEY, api_secret=API_SECRET)

render = web.template.render('templates/') # Tells web.py where the template directory is.

urls = (
  '/', 'index',
  '/remote', 'remote',
  '/albumart', 'albumArt',
  '/pair', 'pair',
  '/pair2', 'paircode',
  '/login', 'login',
  '/get', 'get',
  '/volume', 'volume'
)

app = web.application(urls, globals())

q = None
p = None
c = None
DACPConfig = {'pair-code':None, 'guid':None, 'service-pair':None, 'service-name':SERVICE_NAME, 'paired':False, 'paired-host':None}
iTunes = {'iTunesControl':None, 'loggedin':False}

last_artist = None
bio = ""

if __name__ == "__main__": app.run()

class index:
    def GET(self):
        return render.index("BOB")
        
class remote:
    def GET(self):
        i = web.input(action=None)
        if iTunes['loggedin'] == True:
            if i.action == 'playpause':
                print 'playpause'
                iTunes['iTunesControl'].play_pause()
            elif i.action == 'nextitem':
                print 'nextitem'
                iTunes['iTunesControl'].next_item()
            elif i.action == 'previtem':
                print 'previtem'
                iTunes['iTunesControl'].prev_item()
            #print DACPConfig
            #print iTunes
            art = iTunes['iTunesControl'].artwork(320, 320)
            #print 'art number = '+str(art)
            if type(art) == int: #Type checking possibly a bad idea!?
                #if art == 204 or art == 404: #No content
                artavalible = False
            else:
                tmp = open('static/artwork.png', 'wb')
                tmp.write(art)
                tmp.close()
                tmpo = open('/Users/elsmorian/Sites/remote/static/artwork.png', 'wb')
                tmpo.write(art)
                tmpo.close()
                artavalible = True
            return render.remote(i.action,iTunes['iTunesControl'].status().string('cana'),iTunes['iTunesControl'].status().string('cann')
,iTunes['iTunesControl'].status().string('canl'),artavalible)
        else:
            print DACPConfig
            print iTunes
            return 'not logged in!'
        
class albumArt:
    def GET(self):
        return "artwork here"
        
class get:
    def GET(self):
        if iTunes['loggedin'] == True:
            art = iTunes['iTunesControl'].artwork(600, 600)
            if type(art) == int: #Type checking possibly a bad idea!?
                #if art == 204 or art == 404: #No content
                artavalible = False
            else:
                tmp = open('static/artwork.png', 'wb')
                tmp.write(art)
                tmp.close()
                artavalible = True
                
            out_item = iTunes['iTunesControl'].status().string('cann')
            out_artist = iTunes['iTunesControl'].status().string('cana')
            out_album = iTunes['iTunesControl'].status().string('canl')
            out_length = str(iTunes['iTunesControl'].status().int('cant'))
            out_remaining = str(iTunes['iTunesControl'].status().int('cast'))
            
            global last_artist
            global bio
            if (last_artist != out_artist):
                artist = network.get_artist(out_artist)
                last_artist = out_artist
                bio = ''.join(BeautifulSoup(artist.get_bio_summary()).findAll(text=True))
            
            if (bio[:13] == "Incorrect tag"):
                bio = ""
            
            thejson = {}
            
            
            #if (out_item): thejson['item'] = unicodedata.normalize('NFKD', out_item).encode('ascii','ignore')
            #if (out_artist): thejson['artist'] = unicodedata.normalize('NFKD', out_artist).encode('ascii','ignore')
            #if (out_album): thejson['album'] = unicodedata.normalize('NFKD', out_album).encode('ascii','ignore')
            if (out_item): thejson['item'] = out_item
            if (out_artist): thejson['artist'] = out_artist
            if (out_album): thejson['album'] = out_album
            if (out_length and out_length != None): thejson['length'] = int(out_length)
            if (out_remaining and out_remaining != None): thejson['remaining'] = int(out_remaining)
            if (bio and (len(bio) > 40)): thejson['bio'] = unicodedata.normalize('NFKD', bio).encode('ascii','ignore')
            
            thejson['artwork'] = str(artavalible)
            
            #string += "\",\"artwork\" : \""+str(artavalible)
            #string += "\",\"playing\" : \""+str(iTunes['iTunesControl'].status().string('caps'))
            #string += "\",\"shuffle\" : \""+str(iTunes['iTunesControl'].status().int('cash'))
            #string += "\",\"repeat\" : \""+str(iTunes['iTunesControl'].status().int('carp'))
            #string += "\",\"length\" : "
            #if (out_length or out_length != None): string += out_length
            #string += ",\"remaining\" : "
            #if (out_remaining or out_remaining != None): string += out_remaining
            #string += ",\"bio\" : "
            #if (bio): string += "\""+bio+"\""
            #string += "}"
            
            print json.dumps(thejson)
            return json.dumps(thejson)
        
class volume:
    def GET(self):
        i = web.input(vol=None)
        if iTunes['loggedin'] == True:
            return  iTunes['iTunesControl'].volume(int(i.vol))
        
class pair:
    def GET(self):
        global q
        global p
        global c
        global DACPConfig
        
        DACPConfig['pair-code'] = str(random.randint(1000, 9999))
        q = dacp.DACPRemoteServer()
        p = dacp.DACPRemoteService(name=DACPConfig['service-name'])
        
        q.open()
        p.register()
        
        print 'server-guid:', q.guid
        print 'service-name:', p.name
        print 'service-pair:', p.pair
        print 'service-code:', DACPConfig['pair-code']
        
        print DACPConfig
        print iTunes
        return "<p>"+DACPConfig['pair-code']+"</p><p><a href=\"/pair2\">next</a></p>"
        
class paircode:
    def GET(self):
        global DACPConfig
        while True:
            c = q.request()
            
            if c.code == dacp.generate_pairing_code(p.pair, str(DACPConfig['pair-code'])):
                q.respond(c, dacp.PAIR_VALID)
                DACPConfig['paired'] = True
                DACPConfig['guid'] = q.guid
                DACPConfig['service-pair'] = p.pair
                DACPConfig['paired-host'] = c.host
                p.close()
                q.close()
                print ' paired with: %s, %s' % c.host
                print DACPConfig
                print iTunes
                return '<p><a href =\"/login\">login</a></p> paired with: %s, %s' % c.host
        
            else:
                q.respond(c, dacp.PAIR_INVALID)
                DACPConfig['paired'] = False
                DACPConfig['guid'] = None
                DACPConfig['service-pair'] = None
                DACPConfig['paired-host'] = None
                print DACPConfig
                print iTunes
                p.close()
                q.close()
                print ' wrong code: %s, %s' % c.host
                return '<p><a href =\"/pair\">pair</a></p>  wrong code: %s, %s' % c.host
                
#iTunes = {'iTunesControl':None, 'connected':False, 'loggedin':False}
class login:
    def GET(self):
        global iTunes
        if DACPConfig['paired'] == True:
            print 'attempting to log in to '+str(DACPConfig['paired-host'][0])
            iTunes['iTunesControl'] = itunes.ITunesController(host=DACPConfig['paired-host'][0])
            iTunes['iTunesControl'].connect()
            
            if iTunes['iTunesControl'].login(guid=DACPConfig['guid']):
                iTunes['loggedin'] = True
                print DACPConfig
                print iTunes
                return '<p>connected and logged in to: '+str(DACPConfig['paired-host'][0])+'</p><p><a href=\"/remote\">remote</a></p>'
            
            else:
                print DACPConfig
                print iTunes
                return 'error, bad GUID etc'
            
        elif DACPConfig['paired'] == False:
            print DACPConfig
            print iTunes
            return '<p>not paired!</p><p><a href=\"/pair\">pair</a></p>'