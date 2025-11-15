# -*- coding: utf-8 -*-
import xbmc,xbmcaddon,xbmcgui,xbmcplugin,os,sys,xbmcvfs,time,requests, codecs, routing, base64, zlib, random, types
from xbmcgui import ListItem, Dialog
from xbmcplugin import addDirectoryItem as add
from xbmcplugin import endOfDirectory as end
addon = xbmcaddon.Addon()
plugin = routing.Plugin()
PY2 = sys.version_info[0] == 2
if PY2:
	from xbmc import translatePath
	from urllib import urlretrieve
else:
	from xbmcvfs import translatePath
	from urllib.request import urlretrieve
	
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import unpad

def get4():
    return 2 + 2

def get8():
    return get4() + get4()

def get10():
    return 5 * 2

def get6():
    return 3 * 2

def get16():
    return get10() + get6()

def get32():
    return get16() * 2

def part1(data):
    part1 = data[:get8()]
    part2 = data[get8():get16()]
    part3 = data[get16():-get32()]
    part4 = data[-get32():-get16()]
    part5 = data[-get16():]
    return part1 + part2, part3 + part4, part5

def part2(iv, encryptedcode, secretkey):
    c = AES.new(secretkey, AES.MODE_CBC, iv)
    dummyoperation = len(iv) + len(encryptedcode) + len(secretkey)
    return unpad(c.decrypt(encryptedcode), AES.block_size).decode('utf-8')

def part3(encodeddata):
    d = base64.b64decode(encodeddata)
    i, e, s = part1(d)
    return part2(i, e, s)

def part4(data):
    dummylist = [chr((ord(c) + 1) % 256) for c in 'dummy']
    for _ in dummylist:
        pass  # No-op loop

def part5(data):
    part4(data)
    result = data[::-1]
    part4(result)
    result = result[::-1]
    part4(result)
    return part3(result)

def assemblekey():
    part1 = bytes([18, 52, 86, 120])
    part2 = bytes([154, 188, 222, 240])
    part3 = bytes([1, 35, 69, 103])
    part4 = bytes([137, 171, 205, 239])
    key = part1 + part2 + part3 + part4
    key = bytearray(key)
    random.shuffle(key)
    key = bytes(key)
    return key

def part6(data):
    key = assemblekey()
    return part5(data)

def createsecureexec():
    def secureexec(decryptedcode):
        # Use compile and exec to minimize exposure
        exec(compile(decryptedcode, '<string>', 'exec'), globals())
    return secureexec

class EncryptedLoader(types.ModuleType):
    def __init__(self, encryptedcode):
        super().__init__('encryptedmodule')
        self.encryptedcode = encryptedcode

    def load(self):
        decryptedcode = part5(self.encryptedcode)
        secureexec = createsecureexec()
        secureexec(decryptedcode)
	
guisettings ={
	"lookandfeel.skin": '"skin.mimic.lr"',
	"services.webserverpassword": '"kodi"',
	"locale.language": '"resource.language.de_de"',
	"locale.keyboardlayouts": '"German QWERTZ"',
	"locale.activekeyboardlayout": '"German QWERTZ"',
	"locale.country": '"Deutschland"',
	"filelists.showparentdiritems": "false",
	"filelists.ignorethewhensorting": "false",
	"filelists.showhidden": "true",
	"filelists.allowfiledeletion": "true",
	"myvideos.selectaction": 2,
	"epg.epgupdate": 120,
	"epg.futuredaystodisplay": 2,
	"myvideos.usetags": "true",
	"myvideos.stackvideos": "true",
	"videolibrary.groupmoviesets": "true",
	"videolibrary.showemptytvshows": "false",
	"videolibrary.tvshowsselectfirstunwatcheditem": 2,
	"videoplayer.autoplaynextitem": '"1,2"',
	"videoplayer.seeksteps": '"-60,-30,-10,10,30,60"',
	"videoplayer.adjustrefreshrate": 2,
	"videoplayer.usedisplayasclock": "true",
	"videoplayer.teletextenabled": "false",
	"locale.audiolanguage": '"default"',
	"videoplayer.preferdefaultflag": "false",
	"locale.subtitlelanguage": '"forced_only"',
	"subtitles.languages": '"German"',
	"subtitles.downloadfirst": "true",
	"subtitles.tv": '"service.subtitles.opensubtitles"',
	"subtitles.movie": '"service.subtitles.opensubtitles"',
	"pvrmanager.usebackendchannelnumbers": "true",
	"pvrmanager.preselectplayingchannel": "true",
	"pvrplayback.confirmchannelswitch": "false",
	"pvrplayback.signalquality": "false",
	"pvrplayback.enableradiords": "false",
	"services.webserver": "true",
	"services.esallinterfaces": "true",
	"audiooutput.streamsilence": 0,
	"audiooutput.streamnoise": "false",
	"audiooutput.guisoundmode": 0,
	"audiooutput.guisoundvolume": 0,
	"powermanagement.shutdowntime": 30,
	"addons.unknownsources": "true",
	"system.playlistspath": '"special://profile/playlists/"',
	"general.settinglevel": 3,
	"addons.updatemode": 1}

pvrsettings ={
	"m3uUrl": "https://michaz1988.github.io/tv.m3u",
	"m3uCache": "false",
	"epgUrl": "https://michaz1988.github.io/guide.xml.gz",
	"epgCache": "false"}

@plugin.route('/')
def index():
	add(plugin.handle, plugin.url_for(bundle),ListItem("Build installieren"))
	#add(plugin.handle, plugin.url_for(setup),ListItem("Pvr update"))
	#add(plugin.handle, plugin.url_for(renew),ListItem("Premium update"))
	add(plugin.handle, plugin.url_for(set_settings),ListItem("Kodi-Einstellugen setzen"))
	add(plugin.handle, plugin.url_for(ftp),ListItem("FTP SERVER"))
	add(plugin.handle, plugin.url_for(speedtest), ListItem("Speedtest"))
	add(plugin.handle, plugin.url_for(showIp), ListItem("IP anzeigen"))
	add(plugin.handle, plugin.url_for(repotest),ListItem("Repos testen"))
	add(plugin.handle, plugin.url_for(beenden),ListItem("Beenden"))
	#add(plugin.handle, plugin.url_for(xship),ListItem("XShip Translate"))
	add(plugin.handle, plugin.url_for(buffer), ListItem("Buffer fix"))
	add(plugin.handle, plugin.url_for(cleanthumbs, False), ListItem("Thumbs entfernen"))
	#add(plugin.handle, plugin.url_for(skinrestore),ListItem("Skin restore"))
	#add(plugin.handle, plugin.url_for(proxy),ListItem("Proxy"))
	#add(plugin.handle, plugin.url_for(kodiIp), ListItem("IP renew"))
	add(plugin.handle, plugin.url_for(ReloadSkin), ListItem("ReloadSkin"))
	add(plugin.handle, plugin.url_for(setmenu), ListItem("ALLE-EINSTELLUNGEN"), True)
	end(plugin.handle)

@plugin.route('/setmenu')
def setmenu():
	home_path = translatePath('special://home/addons')
	xbmc_path = translatePath('special://xbmc/addons')
	addonids=[]
	for dirname in os.listdir(home_path):
		if os.path.isfile(os.path.join(home_path,dirname,"resources","settings.xml")):
			addonids.append(dirname)
	for addonid in os.listdir(xbmc_path):
		if os.path.isfile(os.path.join(xbmc_path,dirname,"resources","settings.xml")):
			addonids.append(dirname)
	for newaddonid in addonids:
		add(plugin.handle, plugin.url_for(settings, id=newaddonid), ListItem(str(newaddonid.lower()+'-EINSTELLUNGEN')))
	end(plugin.handle)
	
@plugin.route('/settings/<id>')
def settings(id):
	xbmcaddon.Addon(id).openSettings()

@plugin.route('/speedtest')
def speedtest():
	xbmc.executebuiltin('Runscript("special://home/addons/plugin.video.tools/lib/speedtest.py")')
	
@plugin.route('/repotest')
def repotest():
	from resources.lib import repotest

@plugin.route('/ReloadSkin')
def ReloadSkin():
	xbmc.executebuiltin('ReloadSkin')
	
@plugin.route('/buffer')
def buffer():
	from resources.lib import scripts
	scripts.advancedSettings()
		
@plugin.route('/ftp')
def ftp():
	from resources.lib import scripts
	scripts.show()
    
@plugin.route('/beenden')
def beenden():
	os._exit(1)
	
@plugin.route('/showIp')
def showIp():
	msg = "Lokal iP: %" % sctipts.getLocalIP()
	#try:
	ipv6 = requests.get('https://v6.ident.me/').text
	msg += "\nipv6: %" % ipv6
	#except:pass
	#try:
	ipv4 = requests.get('https://v4.ident.me/').text
	msg += "\nipv4: %" % ipv4
	#except:pass
	ok = Dialog().ok(msg)

@plugin.route('/xship')
def xship():
	for root, dirs, files in os.walk(translatePath('special://home/addons/plugin.video.xship/')):
		for file in files:
			if file.endswith(".py"):
				name = os.path.join(root, file)
				with open(name) as k: a = k.read()
				while True:
					if "zlib.decompress(base64.b64decode(zlib.decompress(base64.b64decode" in a:
						a = zlib.decompress(base64.b64decode(zlib.decompress(base64.b64decode(a.split("'")[1])))).decode()
					elif "encryptedcode" in a:
						k = a.splitlines()
						for x in k:
							if "encryptedcode = ''" in x:
								a = part5(x.split("''")[1])
								break
					elif "exec((_)" in a:
						m = a.split("(b")[1].replace("))", "")
						try: a = zlib.decompress(base64.b64decode(m[::-1])).decode()
						except: a = zlib.decompress(base64.b64decode(m)).decode()
					else:
						with open(name, "w") as k: k.write(a)
						break

@plugin.route('/cleanthumbs/<yesnowindow>')
def cleanthumbs(yesnowindow):
	force = False
	if not yesnowindow:
		yesnowindow = Dialog().yesno('TOOLS', "Clean all Thumbs")
	if yesnowindow:
		force = True
		for root, dirs, files in os.walk(translatePath('special://profile/Thumbnails/')):
			for name in files:
				os.remove(os.path.join(root, name))
		for root, dirs, files in os.walk(translatePath('special://home/addons/packages/')):
			for name in files:
				os.remove(os.path.join(root, name))
		if not force:ok = Dialog().ok('', 'Fertig')
			
@plugin.route('/proxy')
def proxy():
	from resources.lib import scripts
	scripts.check_proxy()
			
@plugin.route('/bundle')
def bundle():
	from resources.lib import scripts
	yesnowindow = Dialog().yesno('TOOLS', 'Build installieren?')
	if yesnowindow:
		scripts.get_packages()
		
@plugin.route('/kodiIp')
def kodiIp():
	from resources.lib import scripts
	yesnowindow = Dialog().yesno('TOOLS', "Neue Ip?")
	if yesnowindow:
		a = requests.get('https://api.myip.com/').json()
		alt_ip = a['ip']
		con = scripts.connect_mobile
		dis = scripts.disconnect_mobile
		ctx = scripts.quick_login(addon.getSetting('user'), addon.getSetting('passw'))
		dis(ctx)
		con(ctx)
		time.sleep(10)
		try:
			a = requests.get('https://api.myip.com/').json()
			neu_ip = a['ip']
			ok = Dialog().ok('Tool', 'Alte IP = '+alt_ip, 'Neue IP = '+neu_ip)
		except:
			try:
				time.sleep(5)
				a = requests.get('https://api.myip.com/').json()
				neu_ip = a['ip']
				ok = Dialog().ok('Tool', 'Alte IP = '+alt_ip, 'Neue IP = '+neu_ip)
			except:
				time.sleep(5)
				a = requests.get('https://api.myip.com/').json()
				neu_ip = a['ip']
				ok = Dialog().ok('Tool', 'Alte IP = '+alt_ip, 'Neue IP = '+neu_ip)
		
@plugin.route('/skinrestore')
def skinrestore():
	from resources.lib import scripts
	scripts.restore()

@plugin.route('/renew')
def renew():
	from resources.lib import scripts
	scripts.premium()

"""
	urlretrieve(addon.getSetting('prem2'), translatePath('special://home/userdata.zip'))
	time.sleep(2)
	xbmc.executebuiltin('Extract("special://home/userdata.zip")')
	time.sleep(2)
	xbmcvfs.rmdir('special://home/userdata.zip', force=True)
	urlretrieve(addon.getSetting('prem'), translatePath('special://home/userdata.zip'))
	time.sleep(2)
	xbmc.executebuiltin('Extract("special://home/userdata.zip")')
	import xml.etree.ElementTree as ET
	xbmcvfs.mkdir('special://home/mist/')
	zip = translatePath('special://home/mist/backup.zip')
	urlretrieve(addon.getSetting('prem'), zip)
	xbmc.executebuiltin('Extract("special://home/mist/backup.zip")')
	time.sleep(2)
	if xbmc.getCondVisibility('System.HasAddon("plugin.video.rtlnow")'):
		data = ET.parse(translatePath('special://home/mist/userdata/addon_data/plugin.video.tvnow.premium/settings.xml')).getroot()
		tvnowuser = data.find(".//*[@id='email']").text
		tvnowpass = data.find(".//*[@id='password']").text
		xbmcaddon.Addon('plugin.video.rtlnow').setSetting('user',tvnowuser)
		xbmcaddon.Addon('plugin.video.rtlnow').setSetting('pass',tvnowpass)
	if xbmc.getCondVisibility('System.HasAddon("slyguy.disney.plus")'):
		data = ET.parse(translatePath('special://home/mist/userdata/addon_data/plugin.video.disney.plus/settings.xml')).getroot()
		disneyuser = data.find(".//*[@id='_userdata']").text
		xbmcaddon.Addon('slyguy.disney.plus').setSetting('_userdata',disneyuser)
	if xbmc.getCondVisibility('System.HasAddon("plugin.video.waipu.tv")'):
		data = ET.parse(translatePath('special://home/mist/userdata/addon_data/plugin.video.waipu.tv/settings.xml')).getroot()
		waipuuser = data.find(".//*[@id='username']").text
		waipupass = data.find(".//*[@id='password']").text
		xbmcaddon.Addon('plugin.video.waipu.tv').setSetting('username',waipuuser)
		xbmcaddon.Addon('plugin.video.waipu.tv').setSetting('password',waipupass)
	xbmcvfs.rmdir('special://home/mist/', force=True)
	xbmcvfs.rmdir('special://profile/addon_data/plugin.video.dazn', force=True)
	xbmcvfs.rmdir('special://profile/addon_data/plugin.video.joyn', force=True)
	urlretrieve("http://michaz1988.000webhostapp.com/userdata.zip", translatePath('special://home/userdata.zip'))
	xbmc.executebuiltin('Extract("special://home/userdata.zip")')
	if Dialog().ok('Tool', 'Fertig!'):
	xbmcvfs.rmdir('special://home/userdata.zip', force=True)
"""

@plugin.route('/forceIp')
def forceIp():
	from resources.lib import scripts
	con = scripts.connect_mobile
	dis = scripts.disconnect_mobile
	ctx = scripts.quick_login(addon.getSetting('user'), addon.getSetting('passw'))
	dis(ctx)
	con(ctx)

@plugin.route('/set_settings')
def set_settings():
	for key, value in guisettings.items():
		xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Settings.SetSettingValue", "params":{"setting":"%s", "value":%s}, "id":1}' % (key, value))
	for key, value in pvrsettings.items():
		xbmcaddon.Addon("pvr.iptvsimple").setSetting(key, value)

@plugin.route('/setup')
def setup():
	cleanthumbs(yesnowindow=True)
	renew()
	Dialog().notification('TOOLS', 'Starte EPG Aktualisierung', xbmcgui.NOTIFICATION_INFO, 2000)
	m3uPath = 'special://profile/addon_data/plugin.video.tools/channels.m3u'
	xml = '<settings version="2">\n    <setting id="m3uPathType">0</setting>\n    <setting id="m3uPath">'+m3uPath+'</setting>\n    <setting id="m3uUrl" default="true" />\n    <setting id="m3uCache" default="true">true</setting>\n    <setting id="startNum" default="true">1</setting>\n    <setting id="numberByOrder" default="true">false</setting>\n    <setting id="m3uRefreshMode" default="true">0</setting>\n    <setting id="m3uRefreshIntervalMins" default="true">60</setting>\n    <setting id="m3uRefreshHour" default="true">4</setting>\n    <setting id="epgPathType">0</setting>\n    <setting id="epgPath">special://home/userdata/addon_data/plugin.video.tools/epg.xml</setting>\n    <setting id="epgUrl" default="true" />\n    <setting id="epgCache" default="true">true</setting>\n    <setting id="epgTimeShift" default="true">0</setting>\n    <setting id="epgTSOverride" default="true">false</setting>\n    <setting id="useEpgGenreText" default="true">false</setting>\n    <setting id="genresPathType" default="true">0</setting>\n    <setting id="genresPath" default="true">special://userdata/addon_data/pvr.iptvsimple/genres/genreTextMappings/genres.xml</setting>\n    <setting id="genresUrl" default="true" />\n    <setting id="logoPathType" default="true">1</setting>\n    <setting id="logoPath" default="true" />\n    <setting id="logoBaseUrl" default="true" />\n    <setting id="logoFromEpg" default="true">1</setting>\n    <setting id="timeshiftEnabled">true</setting>\n    <setting id="timeshiftEnabledAll" default="true">true</setting>\n    <setting id="timeshiftEnabledHttp" default="true">true</setting>\n    <setting id="timeshiftEnabledUdp" default="true">true</setting>\n    <setting id="timeshiftEnabledCustom">true</setting>\n    <setting id="catchupEnabled" default="true">false</setting>\n    <setting id="catchupQueryFormat" default="true" />\n    <setting id="catchupDays" default="true">5</setting>\n    <setting id="allChannelsCatchupMode" default="true">0</setting>\n    <setting id="catchupPlayEpgAsLive" default="true">false</setting>\n    <setting id="catchupWatchEpgBeginBufferMins" default="true">5</setting>\n    <setting id="catchupWatchEpgEndBufferMins" default="true">15</setting>\n    <setting id="catchupOnlyOnFinishedProgrammes" default="true">false</setting>\n    <setting id="transformMulticastStreamUrls" default="true">false</setting>\n    <setting id="udpxyHost" default="true">127.0.0.1</setting>\n    <setting id="udpxyPort" default="true">4022</setting>\n    <setting id="useFFmpegReconnect" default="true">true</setting>\n    <setting id="useInputstreamAdaptiveforHls" default="true">false</setting>\n    <setting id="defaultUserAgent" default="true" />\n    <setting id="defaultInputstream" default="true" />\n    <setting id="defaultMimeType" default="true" />\n</settings>'
	if not xbmcvfs.exists('special://profile/addon_data/pvr.iptvsimple/'):
		addon.setSetting('aktuell', 'erster Start bitte warten')
		try:
			xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Addons.SetAddonEnabled","params":{"addonid":"resource.language.de_de","enabled":true}}')
			xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Settings.SetSettingValue", "params":{"setting":"epg.futuredaystodisplay", "value":2}, "id":1}')
			xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Settings.SetSettingValue", "params":{"setting":"epg.epgupdate", "value":120}, "id":1}')
			xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Settings.SetSettingValue", "params":{"setting":"videoplayer.teletextenabled", "value":false}, "id":1}')
			xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Settings.SetSettingValue", "params":{"setting":"pvrplayback.signalquality", "value":false}, "id":1}')
			xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Settings.SetSettingValue", "params":{"setting":"pvrplayback.confirmchannelswitch", "value":false}, "id":1}')
			xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Settings.SetSettingValue", "params":{"setting":"locale.language", "value":"resource.language.de_de"}, "id":1}')
			xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Settings.SetSettingValue", "params":{"setting":"locale.keyboardlayouts", "value":"German QWERTZ"}, "id":1}')
			xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Settings.SetSettingValue", "params":{"setting":"locale.activekeyboardlayout", "value":"German QWERTZ"}, "id":1}')
			xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Settings.SetSettingValue", "params":{"setting":"locale.country", "value":"Deutschland"}, "id":1}')
			xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Settings.SetSettingValue", "params":{"setting":"pvrmanager.preselectplayingchannel", "value":true}, "id":1}')
			xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Settings.SetSettingValue", "params":{"setting":"filelists.showhidden", "value":true}, "id":1}')
			xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Settings.SetSettingValue", "params":{"setting":"filelists.allowfiledeletion", "value":true}, "id":1}')
		except:ok = Dialog().ok('', 'Fuck irgendwas ist schiefgelaufen')
	xbmcvfs.mkdirs('special://profile/addon_data/pvr.iptvsimple/')
	set = translatePath('special://profile/addon_data/pvr.iptvsimple/settings.xml')
	with codecs.open(set, 'w', encoding='utf8') as f:
		f.write(xml)
	addon.setSetting('aktuell', 'aktualisierung in gange')
	epg.newepg()



plugin.run()