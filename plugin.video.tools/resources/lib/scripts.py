# -*- coding: utf-8 -*-
import os, io, sys, time, shutil, requests, threading, socket, base64, binascii, hashlib, json, zlib
import xbmc, xbmcaddon, xbmcgui, xbmcplugin,zipfile,re, xbmcvfs
from xml.dom import minidom
from xml.dom.minidom import Element, Document
from resources.lib.pyftpdlib.authorizers import DummyAuthorizer
from resources.lib.pyftpdlib.handlers import FTPHandler
from resources.lib.pyftpdlib.servers import FTPServer
try:
	from BytesIO import BytesIO
except:
	from io import BytesIO
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
if PY2:
	from urllib import urlencode
	from urlparse import urlparse
	text_type = unicode
	from xbmc import translatePath
	string_types = basestring,
	integer_types = (int, long)
	text_type = unicode
	binary_type = str
	iteritems = lambda d, *args, **kwargs: d.iteritems(*args, **kwargs)
else:
	from urllib.parse import urlencode, urlparse
	text_type = str
	from xbmcvfs import translatePath
	string_types = str,
	integer_types = int,
	binary_type = bytes
	iteritems = lambda d, *args, **kwargs: iter(d.items(*args, **kwargs))

addon = xbmcaddon.Addon()
addonInfo = addon.getAddonInfo
addonPath = addonInfo('path')
ftppath = "/sdcard" if xbmc.getCondVisibility("system.platform.android") else os.path.expanduser("~")
dialog = xbmcgui.Dialog()
WINDOW_HOME = xbmcgui.Window(10000)

def getLocalIP():
	return (([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")] or [[(s.connect(("8.8.8.8", 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) + ["no IP found"])[0]

def localize(id):
	return xbmc.getLocalizedString(id)

def get(key):
	return WINDOW_HOME.getProperty(key)

def xbmcNotify(heading, message, icon=xbmcgui.NOTIFICATION_ERROR):
	dialog.notification(heading=heading, message=message, icon=icon)

def convert_size(num, suffix='B'):
	for unit in ['', 'K', 'M', 'G']:
		if abs(num) < 1024.0:
			return "%3.02f %s%s" % (num, unit, suffix)
		num /= 1024.0
	return "%.02f %s%s" % (num, 'G', suffix)

class ForceWindowThread(threading.Thread):

    def __init__(self, fw):
        threading.Thread.__init__(self)
        self.fw = fw
        self.setDaemon(True)
        self.start()

    def run(self):
        while not xbmc.abortRequested and self.fw.currentWindow and get('Locked') == 'true':
            winId = xbmcgui.getCurrentWindowId()
            if winId < 13000 or winId >= 14000:
                self.fw.onAction(None)
            xbmc.sleep(100)

        return


class ForceWindow(object):
    currentWindow = 0
    last = 0

    def onAction(self, action):
        winId = xbmcgui.getCurrentWindowId()
        xbmc.log('Current window %s, currentWindow window %s' % (winId, self.currentWindow))
        if self.currentWindow and self.currentWindow != winId:
            xbmc.log('Forcing window from %s to %s' % (winId, self.currentWindow))
            xbmc.executebuiltin('ReplaceWindow(%s)' % self.currentWindow)

    def onClose(self):
        if xbmcgui.getCurrentWindowId() == self.currentWindow:
            self.currentWindow = 0

    def create(self, cls, *args, **kwargs):
        xbmc.log('Creating window %r' % cls)
        diff = 0.5 - (time.time() - self.last)
        if diff > 0:
            time.sleep(diff)
        self.last = time.time()
        setProperties = kwargs.pop('setProperties', None)
        window = cls.create(*args, **kwargs)
        if setProperties:
            for key, value in list(setProperties.items()):
                window.setProperty(key, value)

        lastWindow = self.showNotModal(window)
        try:
            return window.doModal()
        finally:
            self.closeNotModal(lastWindow)

        del window
        return

    def showNotModal(self, window=None):
        lastWindow = self.currentWindow
        if window is not None:
            self.currentWindow = 0
            window.show()
        self.currentWindow = xbmcgui.getCurrentWindowId()
        if get('Locked') == 'true':
            ForceWindowThread(self)
        return lastWindow

    def closeNotModal(self, lastWindow):
        self.currentWindow = lastWindow

def getLocalIP():
    return xbmc.getIPAddress()


class FtpThread(threading.Thread):

    def __init__(self, server):
        super(FtpThread, self).__init__()
        self.setDaemon(True)
        self.server = server

    def run(self):
        try:
            self.server.serve_forever()
        except Exception as e:
            xbmc.log('Failed running FTP server: %r' % e, xbmc.LOGERROR)


class MyAuthorizer(DummyAuthorizer):

    def validate_authentication(self, username, password, handler):
        handler.username = 'anonymous'
        DummyAuthorizer.validate_authentication(self, handler.username, password, handler)


class FtpWindow(xbmcgui.WindowXML):
    CANCEL_BUTTON_ID = 301
    server = None

    @classmethod
    def create(cls):
        return cls('ftp.xml', addonPath, 'Main', '1080i')

    def onInit(self):
        try:
            self.setProperty('LocalIP0' , xbmc.getIPAddress())
            authorizer = MyAuthorizer()
            authorizer.add_anonymous(ftppath, perm='elradfmw')
            handler = FTPHandler
            handler.authorizer = authorizer
            ports = [3721, 3722, 3723]
            for port in ports:
                try:
                    self.server = FTPServer(('0.0.0.0', port), handler)
                except Exception as e:
                    xbmc.log('Failed starting FTP on port %s: %r' % (port, e), xbmc.LOGERROR)
                    self.server = None
                else:
                    break

            if self.server is None:
                xbmcNotify(localize(257), localize(39525))
                self.close()
                return
            self.setProperty('Port', str(port))
            self.setProperty('Started', 'true')
            FtpThread(self.server).start()
        except Exception as e:
            xbmc.log('Failed starting FTP server: %r' % e, xbmc.LOGERROR)
            import traceback
            traceback.print_exc()
            xbmcNotify(localize(257), localize(39526))
            self.close()

        return

    def onClick(self, controlID):
        if controlID == self.CANCEL_BUTTON_ID:
            self.close()

    def onAction(self, action):
        if action.getId() in (xbmcgui.ACTION_PREVIOUS_MENU, xbmcgui.ACTION_NAV_BACK):
            self.close()
        ForceWindow().onAction(action)

    def close(self):
        ForceWindow().onClose()
        super(FtpWindow, self).close()

    def doModal(self):
        try:
            return xbmcgui.WindowXML.doModal(self)
        finally:
            if self.server:
                self.server.close_all()

def show():
    xbmc.executebuiltin('Dialog.Close(all,true)')
    ForceWindow().create(FtpWindow)

def translate(name):
	with open(name) as k:
		a = k.read()
	b = base64.urlsafe_b64decode(a.strip("exec((_)(b")[::-1])
	c = zlib.decompress(b)
	with open(name, "wb") as k:
		k.write(c)

class Downloader:
	def __init__(self):
		self.dialog = dialog
		self.progress_dialog = xbmcgui.DialogProgress()
		
	def download(self, url, place=None):
		self.progress_dialog.create("TOOLS", "Starte Download...")
		self.progress_dialog.update(0)
		f = io.BytesIO() if place == None else open(place, 'wb')
		response = requests.get(url, headers={'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36'' (KHTML, like Gecko) Chrome/35.0.1916.153 Safari''/537.36 SE 2.X MetaSr 1.0'}, stream=True)
		total = response.headers.get('content-length')
		if total is None:
			f.write(response.content)
		else:
			downloaded = 0
			total = int(total)
			start_time = time.time()
			mb = 1024*1024
			for chunk in response.iter_content(chunk_size=max(int(total/512), mb)):
				downloaded += len(chunk)
				f.write(chunk)
				done = int(100 * downloaded / total)
				kbps_speed = downloaded / (time.time() - start_time)
				if kbps_speed > 0 and not done >= 100:
					eta = (total - downloaded) / kbps_speed
				else:
					eta = 0
				kbps_speed = kbps_speed / 1024
				type_speed = 'KB'
				if kbps_speed >= 1024:
					kbps_speed = kbps_speed / 1024
					type_speed = 'MB'
				line1 = '[COLOR %s][B]Size:[/B] [COLOR %s]%.02f[/COLOR] MB of [COLOR %s]%.02f[/COLOR] MB[/COLOR]' % ('white', 'limegreen', downloaded / mb, 'limegreen', total / mb)
				line2 = '[COLOR %s][B]Speed:[/B] [COLOR %s]%.02f [/COLOR]%s/s ' % ('white', 'limegreen', kbps_speed, type_speed)
				div = divmod(eta, 60)
				line3 = '[B]ETA:[/B] [COLOR %s]%02d:%02d[/COLOR][/COLOR]' % ('limegreen', div[0], div[1])
				if PY2:self.progress_dialog.update(done, line1, line2, line3)
				else:self.progress_dialog.update(done, line1+"\n"+line2+"\n"+line3)
		return f

class Unpacker:
	def __init__(self):
		self.dialog = dialog
		self.progress_dialog = xbmcgui.DialogProgress()
	
	def unpack(self, _in, _out):
		self.progress_dialog.create("TOOLS", "Entpacken läuft...")
		self.progress_dialog.update(0)
		count = 0
		size = 0
		zin = zipfile.ZipFile(_in,  'r')
		nFiles = float(len(zin.namelist()))
		zipsize = convert_size(sum([item.file_size for item in zin.infolist()]))
		for item in zin.infolist():
			count += 1
			prog = int(count / nFiles * 100)
			size += item.file_size
			line1 = '[COLOR {0}][B]File:[/B][/COLOR] [COLOR {1}]{2}/{3}[/COLOR] '.format('white','limegreen',count,int(nFiles))
			line2 = '[COLOR {0}][B]Size:[/B][/COLOR] [COLOR {1}]{2}/{3}[/COLOR]'.format('white','limegreen',convert_size(size),zipsize)
			line3 = '[COLOR {0}]{1}[/COLOR]'.format('limegreen', str(item.filename).split('/')[-1])
			zin.extract(item, _out)
			if PY2:self.progress_dialog.update(prog, line1, line2, line3)
			else:self.progress_dialog.update(prog, line1+"\n"+line2+"\n"+line3)
		return True

def py2_uni(s, encoding='utf-8'):
	if PY2 and isinstance(s, str):
		s = unicode(s, encoding)
	return s

def py3_dec(d, encoding='utf-8'):
	if PY3 and isinstance(d, bytes):
		d = d.decode(encoding)
	return d

def py3_enc(d, encoding='utf-8'):
	if PY3 and isinstance(d, str):
		d = d.encode(encoding)
	return d

def to_str(d, encoding='utf-8'):
	if PY2:
		if not isinstance(d, basestring):
			d = str(d)
		d = d.encode(encoding) if isinstance(d, unicode) else d
	else:
		if isinstance(d, bytes):
			d = d.decode(encoding)
	return d

def read_from_file(file, mode='r'):
	f = open(file, mode, encoding="utf-8") if PY3 else open(file, mode)
	a = f.read()
	f.close()
	return a

def write_to_file(file, content, mode='w'):
	f = open(file, mode)
	f.write(content)
	f.close()

def xml_data_advSettings_old(size):
	xml_data="""<advancedsettings>
</advancedsettings>""" % size
	return xml_data
	
def xml_data_advSettings_New(size):
	xml_data="""<advancedsettings>
	  <cache>
		<memorysize>%s</memorysize> 
		<buffermode>1</buffermode>
		<readfactor>4.0</readfactor>
	  </cache>
	  <epg>
		<displayupdatepopup>false</displayupdatepopup>
	</epg>
</advancedsettings>""" % size
	return xml_data

def write_ADV_SETTINGS_XML(file):	
	if not os.path.exists(xml_file):
		with open(xml_file, "w") as f:
			f.write(xml_data)

def advancedSettings():
	XML_FILE   =  translatePath(os.path.join('special://home/userdata' , 'advancedsettings.xml'))
	MEM		=  xbmc.getInfoLabel("System.Memory(total)")
	FREEMEM	=  xbmc.getInfoLabel("System.FreeMemory")
	BUFFER_F   =  re.sub('[^0-9]','',FREEMEM)
	BUFFER_F   = int(BUFFER_F) / 3 *0.9
	BUFFERSIZE = BUFFER_F * 1024 * 1024
	try: KODIV		=  float(xbmc.getInfoLabel("System.BuildVersion")[:4])
	except: KODIV = 16
	choice = dialog.yesno('Tool','Buffer Fix:\nOptimaler Buffer bei deinem System:	   ' + str(BUFFERSIZE) + ' Byte   /   ' + str(BUFFER_F) + ' MB\nWie wilst du optimieren?', yeslabel='Automatisch',nolabel='Selbst eingeben')
	if choice == 1: 
		with open(XML_FILE, "w") as f:
			if KODIV >= 17: xml_data = xml_data_advSettings_New(str(BUFFERSIZE))
			else: xml_data = xml_data_advSettings_New(str(BUFFERSIZE))
			f.write(xml_data)
			dialog.ok('Kodi','Buffer wurde auf ' + str(int(BUFFER_F)) + ' MB eingestellt.\nKodi wird beendet, damit Die Einstellung wirksam wird. Bitte neu starten.')
	elif choice == 0:
		BUFFERSIZE = _get_keyboard( default=str(BUFFERSIZE), heading="Buffer In Bytes eingeben")
		with open(XML_FILE, "w") as f:
			if KODIV >= 17: xml_data = xml_data_advSettings_New(str(BUFFERSIZE))
			else: xml_data = xml_data_advSettings_New(str(BUFFERSIZE))
			f.write(xml_data)
			dialog.ok('Tools','Buffer wurde manuell eingestellt.\nKodi wird beendet, damit Die Einstellung wirksam wird. Bitte neu starten.')
	os._exit(1)

def open_Settings():
	open_Settings = xbmcaddon.Addon().openSettings()
	
def _get_keyboard( default="", heading="", hidden=False ):
	""" shows a keyboard and returns a value """
	keyboard = xbmc.Keyboard( default, heading, hidden )
	keyboard.doModal()
	if ( keyboard.isConfirmed() ):
		return str( keyboard.getText())
	return default
	
def get_date(days=0, formatted=False):
	value = time.time() + (days * 24 * 60 * 60)  # days * 24h * 60m * 60s
	return value if not formatted else time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(value))
	
def get_size(path, total=0):
	for dirpath, dirnames, filenames in os.walk(path):
		for f in filenames:
			fp = os.path.join(dirpath, f)
			total += os.path.getsize(fp)
	return total

def percentage(part, whole):
	return 100 * float(part)/float(whole)
	
def file_count(home, excludes=True):
	item = []
	for base, dirs, files in os.walk(home):
		if excludes:
			dirs[:] = [d for d in dirs if d not in CONFIG.EXCLUDE_DIRS]
			files[:] = [f for f in files if f not in CONFIG.EXCLUDE_FILES]
		for file in files:
			item.append(file)
	return len(item)
	
def clean_house(folder, ignore=False):
	from resources.libs.common import logging
	logging.log(folder)
	total_files = 0
	total_folds = 0
	for root, dirs, files in os.walk(folder):
		if not ignore: dirs[:] = [d for d in dirs if d not in CONFIG.EXCLUDES]
		file_count = 0
		file_count += len(files)
		if file_count >= 0:
			for f in files:
				try:
					os.unlink(os.path.join(root, f))
					total_files += 1
				except:
					try:shutil.rmtree(os.path.join(root, f))
					except: logging.log("Error Deleting {0}".format(f), level=xbmc.LOGERROR)
			for d in dirs:
				total_folds += 1
				try:
					shutil.rmtree(os.path.join(root, d))
					total_folds += 1
				except: logging.log("Error Deleting {0}".format(d), level=xbmc.LOGERROR)
	return total_files, total_folds
  
def download(url, place=None):
	f = io.BytesIO() if place == None else open(place, 'wb')
	response = requests.get(url, headers={'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36'' (KHTML, like Gecko) Chrome/35.0.1916.153 Safari''/537.36 SE 2.X MetaSr 1.0'}, stream=True)
	f.write(response.content)
	return f
	
def unpack(_in, _out):
	zin = zipfile.ZipFile(_in,  'r')
	for item in zin.infolist():
		zin.extract(item, _out)
	return True

def premium():
	data = download(xbmcaddon.Addon().getSetting('prem'))
	unpack(data, translatePath('special://home/'))
	
def restore():
	data = download('https://www.dropbox.com/s/tqr6ai1l3ylf56h/skin.zip?dl=1')
	unpack(data, translatePath('special://home/'))

def get_packages():
	xbmc.executebuiltin('InstallAddon(pvr.iptvsimple)')
	xbmc.executebuiltin('SendClick(11)')
	build = xbmcaddon.Addon().getSetting('build')
	xbmcplugin.setSetting(int(sys.argv[1]), "newinstalled", "true")
	data = Downloader().download(build)
	home = translatePath('special://home')
	if Unpacker().unpack(data, home) == True:
		xbmc.executebuiltin('UpdateLocalAddons')
		time.sleep(1)
		addonlist=["pvr.iptvsimple", "inputstream.adaptive", "inputstream.ffmpegdirect", "inputstream.rtmp"]
		home_path = os.path.join(home,'addons')
		for dirname in os.listdir(home_path):
			if os.path.isdir(os.path.join(home_path,dirname)):
				if not 'packages' in str(dirname):
					if not 'temp' in str(dirname):
						addonlist.append(dirname)
		for addon in addonlist:
			xbmc.executeJSONRPC('{{"jsonrpc":"2.0","id":1,"method":"Addons.SetAddonEnabled","params":{{"addonid":"{}","enabled":true}}}}'.format(addon))
		#open(translatePath('special://home/update'), 'w')
		os._exit(1)
		
def check_proxy():
	ip = addon.getSetting('https_proxy_host')
	port = addon.getSetting('https_proxy_port')
	if (ip != '' and port != '' and test_proxy('http://{0}:{1}'.format(ip, port))):
		return True
	return get_new_proxy()

def test_proxy(proxy):
	try:
		proxy= {'http': proxy, 'https': proxy}
		requests.get('https://www.google.at', proxies=proxy, timeout=10)
	except: return False
	return True

def get_new_proxy():
	ip = addon.getSetting('https_proxy_host')
	port = addon.getSetting('https_proxy_port')
	proxy_uri = 'http://{0}:{1}'.format(ip, port)
	proxy_sites = ['https://gimmeproxy.com/api/getProxy?post=true&country=DE&supportsHttps=true&anonymityLevel=1&protocol=http', 'https://api.getproxylist.com/proxy?anonymity[]=high%20anonymity&anonymity[]=anonymous&country[]=DE&allowsHttps=1&protocol[]=http', 'https://www.freshproxies.net/ProxyList?countries_1=DE&countries_2=DE&protocol=HTTP&level=anon&order=uptime&frame=1H&format=json&fields=comp&key=', 'http://pubproxy.com/api/proxy?format=json&https=true&post=true&country=DE&level=anonymous,elite&type=http&limit=5']
	progress = xbmcgui.DialogProgress()
	progress.create("Prüfe proxies")
	for site in proxy_sites:
		if (progress.iscanceled()):
			return found_new
		sitetext = site[:int(site.find('/', 8))]
		progress.update(0, "momentane Webseite: {0}".format(sitetext))
		try:newproxy = requests.get(site, timeout=3).json()
		except:newproxy = ''
		if newproxy != '':
			if not 'data' in newproxy:
				if 'proxies' in newproxy:
					newproxy = {'data': newproxy['proxies']}
				else: newproxy = {'data': [newproxy]}
			i = 0
			for proxy in newproxy['data']:
				i += 1
				if (progress.iscanceled()): return found_new
				if not 'error' in proxy and 'ip' in proxy and 'port' in proxy:
					progress.update(int(i*100/len(newproxy['data'])), "momentane Webseite: {0}[CR]prüfe Proxy: {1}[CR]{2}/{3}".format(sitetext, '{0}://{1}:{2}'.format(proxy.get('type', proxy.get('protocol', proxy.get('proxyType'))), proxy['ip'], proxy['port']), i, len(newproxy['data'])))
					if (proxy['ip'] != ip or proxy['port'] != port) and proxy['ip'] != '0.0.0.0':
						if test_proxy('{0}://{1}:{2}'.format(proxy.get('type', proxy.get('protocol', proxy.get('proxyType'))), proxy['ip'], proxy['port'])):
							addon.setSetting('https_proxy_host', str(proxy['ip']))
							addon.setSetting('https_proxy_port', str(proxy['port']))
							proxy_uri = 'http://{0}:{1}'.format(str(proxy['ip']), str(proxy['port']))
							time.sleep(1)
							progress.close()
							return proxy_uri
	progress.close()
	return proxy_uri

def get_element_text(elem):
	return " ".join(t.nodeValue for t in elem.childNodes if t.nodeType == t.TEXT_NODE)

def get_child_text(elem, node_name):
	children = elem.getElementsByTagName(node_name)
	if children: return get_element_text(children[0])
	return None

def elements_dictionary(elem):
	ret = {}
	for node in elem.childNodes:
		if node.nodeType == node.ELEMENT_NODE:
			n = node.nodeName
			if n in ret: ret[n] += 1
			else: ret[n] = 0
	ret = dict((k, [] if v > 1 else None) for k, v in list(ret.items()))
	return ret

def get_dictionary_from_children(elem):
	ret = elements_dictionary(elem)
	for node in elem.childNodes:
		if node.nodeType == node.ELEMENT_NODE:
			n = node.nodeName
			if ret[n] is None:
				ret[n] = get_dictionary_from_children(node)
			elif isinstance(ret[n], list): ret[n].append(get_dictionary_from_children(node))
			else: ret[n] = get_dictionary_from_children(node)
	if not ret: ret = get_element_text(elem)
	return ret

def parse_xml_string(xml_string):
	return minidom.parseString(xml_string)

def dict_to_xml(data):
	if not data:
		return ''

	def add_children(doc, parent, input_data):
		if isinstance(input_data, dict):
			for k, v in list(input_data.items()):
				child = doc.createElement(k)
				parent.appendChild(child)
				add_children(doc, child, v)
		elif isinstance(input_data, (list, tuple)):
			for item in input_data:
				add_children(doc, parent, item)
		else:
			child = doc.createTextNode(str(input_data))
			parent.appendChild(child)
	document = Document()
	key = list(data.keys())[0]
	root = document.createElement(key)
	document.appendChild(root)
	add_children(document, root, data[key])
	return document.toxml(encoding='utf8')

MODEM_HOST = addon.getSetting('routerip')

class ApiCtx(object):
	def __init__(self, modem_host=None):
		self.session_id = None
		self.logged_in = False
		self.login_token = None
		self.tokens = []
		self.__modem_host = modem_host if modem_host else MODEM_HOST

	def __unicode__(self):
		return '<{} modem_host={}>'.format(self.__class__.__name__,self.__modem_host)

	def __repr__(self):
		return self.__unicode__()

	def __str__(self):
		return self.__unicode__()

	@property
	def api_base_url(self):
		return 'http://{}/api'.format(self.__modem_host)

	@property
	def token(self):
		if not self.tokens:
			logger.warning('You ran out of tokens. You need to login again')
			return None
		return self.tokens.pop()

def check_error(elem):
	if elem.nodeName != "error":
		return None 
	return {"type": "error","error": {"code": get_child_text(elem, "code"),"message": get_child_text(elem, "message")}}

def api_response(r):
	if r.status_code != 200: r.raise_for_status()
	xmldoc = parse_xml_string(r.text)
	err = check_error(xmldoc.documentElement)
	if err: return err
	return {"type": "response","response": get_dictionary_from_children(xmldoc.documentElement)}

def check_response_headers(resp, ctx):
	if '__RequestVerificationToken' in resp.headers:
		toks = [x for x in resp.headers['__RequestVerificationToken'].split("#") if x != '']
		if len(toks) > 1: ctx.tokens = toks[2:]
		elif len(toks) == 1: ctx.tokens.append(toks[0])
	if 'SessionID' in resp.cookies:
		ctx.session_id = resp.cookies['SessionID']

def post_to_url(url, data, ctx = None, additional_headers = None, proxy=None):
	cookies = build_cookies(ctx)
	headers = common_headers()
	if additional_headers:
		headers.update(additional_headers)
	r = requests.post(url, data=data, headers=headers, cookies=cookies, proxies=proxy)
	check_response_headers(r, ctx)
	return api_response(r)

def get_from_url(url, ctx = None, additional_headers = None,
				 timeout = None, proxy=None):
	cookies = build_cookies(ctx)
	headers = common_headers()
	if additional_headers:
		headers.update(additional_headers)
	r = requests.get(url, headers=headers, cookies=cookies, timeout=timeout, proxies=proxy)
	check_response_headers(r, ctx)
	return api_response(r)

def build_cookies(ctx):
	cookies = None
	if ctx and ctx.session_id:
		cookies = {'SessionID': ctx.session_id}
	return cookies

def common_headers():
	return {"X-Requested-With": "XMLHttpRequest"}

def get_session_token_info(base_url = None, proxy=None):
	"""
	Get session token information
	:param base_url: base url for the modem api
	:return:
	"""
	if base_url is None:
		logger.warning('calling %s.get_session_token_info without base_url argument is deprecated' %__name__)
		base_url = 'http://{}/api'.format(MODEM_HOST)
	url = "{}/webserver/SesTokInfo".format(base_url)
	return get_from_url(url, proxy=proxy, timeout=30)

XML_TEMPLATE = """
	<?xml version:"1.0" encoding="UTF-8"?>
	<request>
		<NetworkMode>{enable}</NetworkMode>
		<NetworkBand>3FFFFFFF</NetworkBand>
		<LTEBand>7FFFFFFFFFFFFFFF</LTEBand>
	</request>
	""".format

def connect_mobile(ctx, proxy=None):
	return switch_mobile_on(ctx, proxy=proxy)

def disconnect_mobile(ctx, proxy=None):
	return switch_mobile_off(ctx, proxy=proxy)

def get_mobile_status(ctx, proxy=None):
	url = "{}/net/net-mode".format(ctx.api_base_url)
	result = get_from_url(url, ctx, proxy=proxy)
	if result and result.get('type') == 'response':
		response = result['response']
		if response and response.get('dataswitch') == '1':
			return 'CONNECTED'
		if response and response.get('dataswitch') == '0':
			return 'DISCONNECTED'
	return 'UNKNOWN'

def switch_mobile_off(ctx, proxy=None):
	data = XML_TEMPLATE(enable=('02'))
	headers = {'__RequestVerificationToken': ctx.token}
	url = "{}/net/net-mode".format(ctx.api_base_url)
	return post_to_url(url, data, ctx, additional_headers=headers, proxy=proxy)

def switch_mobile_on(ctx, proxy=None):
	data = XML_TEMPLATE(enable=('03'))
	headers = {'__RequestVerificationToken': ctx.token}
	url = "{}/net/net-mode".format(ctx.api_base_url)
	return post_to_url(url, data, ctx, additional_headers=headers, proxy=proxy)

def b64_sha256(data):
	s256 = hashlib.sha256()
	s256.update(data.encode('utf-8'))
	dg = s256.digest()
	hs256 = binascii.hexlify(dg)
	return base64.urlsafe_b64encode(hs256).decode('utf-8', 'ignore')

def quick_login(username, password, modem_host = None, proxy=None):
	ctx = ApiCtx(modem_host=modem_host)
	token = get_session_token_info(ctx.api_base_url, proxy=proxy)
	session_token = token['response']['SesInfo'].split("=")
	ctx.session_id = session_token[1] if len(session_token) > 1 else session_token[0]
	ctx.login_token = token['response']['TokInfo']
	response = login(ctx, username, password, proxy=proxy)
	if not ctx.logged_in:
		raise ValueError(json.dumps(response))
	return ctx

def login(ctx, user_name, password, proxy=None):
	headers = common_headers()
	url = "{}/user/login".format(ctx.api_base_url)
	password_value = b64_sha256(user_name + b64_sha256(password) + ctx.login_token)
	xml_data = """
	<?xml version:"1.0" encoding="UTF-8"?>
	<request>
		<Username>{}</Username>
		<Password>{}</Password>
		<password_type>4</password_type>
	</request>
	""".format(user_name, password_value)
#   setup headers
	headers['__RequestVerificationToken'] = ctx.login_token
	headers['X-Requested-With'] = 'XMLHttpRequest'
	r = post_to_url(url, xml_data, ctx, headers, proxy=proxy)
	if r['type'] == "response" and r['response'] == "OK":
		ctx.logged_in = True
	return r

def state_login(ctx, proxy=None):
	url = "{}/user/state-login".format(ctx.api_base_url)
	return get_from_url(url, ctx, proxy=proxy)
