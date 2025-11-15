import xbmcaddon, xbmc, xbmcgui, xbmcvfs, sys,os, time, datetime, plugin, scripts
servicing = False
PY2 = sys.version_info[0] == 2
transPath = xbmc.translatePath if PY2 else xbmcvfs.translatePath
if os.path.exists(transPath('special://profile/new')):
	addons= ["plugin.video.dazn","plugin.video.joyn","plugin.video.magenta-sport","plugin.video.rtlgroup.de","plugin.video.vavooto","plugin.video.waipu.tv","plugin.video.xship","plugin.video.xstream","plugin.video.zappntv","slyguy.disney.plus","pvr.iptvsimple"]
	for addon in addons:
		xbmc.executebuiltin('InstallAddon(%s)' % (addon))
		xbmc.executebuiltin('SendClick(11)')
	xbmc.executebuiltin("UpdateAddonRepos")
	xbmc.executebuiltin('UpdateLocalAddons')
	scripts.premium()
	os.remove(transPath('special://profile/new'))
	
def Service():
	global servicing
	if servicing:
		return
	if xbmc.Player().isPlaying():
		return
	servicing = True
	#plugin.setup()
	time.sleep(2)
	servicing = False

if __name__ == '__main__':
	monitor = xbmc.Monitor()
	
	while not monitor.abortRequested():
		if monitor.waitForAbort(10):
			break
		waitTime = 86400 * int(xbmcaddon.Addon().getSetting('service.interval'))
		if "Fehler" in str(xbmcaddon.Addon().getSetting('aktuell')):
			waitTime = 3600
		ts = xbmcaddon.Addon().getSetting('last.update') or "0.0"
		lastTime = datetime.datetime.fromtimestamp(float(ts))
		now = datetime.datetime.now()
		nextTime = lastTime + datetime.timedelta(seconds=waitTime)
		td = nextTime - now
		timeLeft = td.seconds + (td.days * 24 * 3600)
		if timeLeft <= 0:
			Service()
		now = time.time()
		xbmcaddon.Addon().setSetting('last.update', str(now))