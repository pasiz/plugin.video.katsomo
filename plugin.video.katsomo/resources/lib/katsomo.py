import cookielib
import urllib2,urllib,urlparse,re
import CommonFunctions
from datetime import datetime
import time

common = CommonFunctions

class katsomo():

	URL = { 
		'login' : 'http://m.katsomo.fi/katsomo/login',
		'programdir' : 'http://m.katsomo.fi/katsomo/programs',
		'programs' : 'http://m.katsomo.fi/katsomo/?treeId=',
		'videolink' : 'http://m.katsomo.fi/?progId='
	}

	def __init__(self, username="", password="", cookie_file=""):
		self.cj = cookielib.LWPCookieJar(cookie_file)
		if username == "":
			self.noLogin = True
		else:
			self.noLogin = False
			self.username = username
			self.password = password
			try:
				self.cj.revert(ignore_discard = True)
			except IOError:
				pass
		self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
		self.user_agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 5_0 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko) Version/5.1 Mobile/9A334 Safari/7534.48.3'
		
	def getPage(self, url,postvars={}, header_data = {}):
		req = urllib2.Request(url, urllib.urlencode(postvars), header_data)			
		req.add_header('user-agent', self.user_agent)
		#req.add_header('cookie
		return self.opener.open(req).read()
	
	def getLoginStatus(self):
		if self.noLogin:
			return False
		ret = common.parseDOM(self.getPage(self.URL['login']), "div", attrs = { "class": "login" })
		#ret = common.parseDOM(ret, "a", ret = "href")
		if not "/katsomo/logout" in ret:
			return doLogin()
		else:
			return True
			
	def doLogin(self):
		postvars = { 
			'u' : self.username,
			'p' : self.password
		}
		header_data = {
			'User-Agent' : USER_AGENT,
			'Referer' : 'http://m.katsomo.fi/katsomo/login'
		}
		
		#ret = common.parseDOM(ret, "a", ret = "href")
		if "/katsomo/logout" in common.parseDOM(self.getPage(self.URL['login'], postvars, header_data), "div", attrs = { "class": "login" }):
			try:
				self.cj.save( ignore_discard=True )
			except IOError:
				pass
			return True
		else:
			self.cj.clear()
			return False
	
	def getProgramDirs(self):	
		ret = common.parseDOM(self.getPage(self.URL['programdir']), "div", {'id': 'programs-by-name'})
		ret = common.parseDOM(ret, "ul", {'class': 'all-programs-list'})
		retIDs = common.parseDOM(ret, "li", ret="data-id")
		retNames = common.parseDOM(ret, "li")
		programdirs=[]
		for i in range(0, len(retIDs)):
			name = retNames[i]
			id = retIDs[i]
			if 'star' in name:
				name = common.stripTags(name) + " *"
			else:
				name = common.stripTags(name)
			programdirs.append({'label': name, 'id': id })
		return programdirs
		
	def getPrograms(self, prog_id): 
		ret = common.parseDOM(self.getPage(self.URL['programs'] + prog_id), "div", {'class': 'program'})
		
		programs = []
		for r in ret:
			link = common.parseDOM(r, "a", ret = "href")[0]
			title = common.parseDOM(r, "p", {'class': 'program-name'})[0]
			if 'class="star"' in title and not self.getLoginStatus(): continue
			elif 'class="star"' in title and self.getLoginStatus() and self.scrapVideoLink(link) == None: continue	
			
			title += ' ' + common.parseDOM(r, "p", {'class': 'program-abstract'})[0]
			img = 'http://m.katsomo.fi' + common.parseDOM(r, "img", ret = "src")[0]
	
			timestamp = common.parseDOM(r, "p", {'class': 'timestamp'})[0]
			ts = None
			if 'TULOSSA' in timestamp:
				continue;

			try:
				ts = datetime.strptime(timestamp.replace('- ', ''), '%d.%m.%Y %H.%M')
			except TypeError:
				ts = datetime(*(time.strptime(timestamp.replace('- ', ''), '%d.%m.%Y %H.%M')[0:6]))	
			timestamp = '{:%d.%m.%Y}'.format(ts)
			playid = urlparse.urlparse(link)[4].split('=')[1]
			programs.append( {'playid' : playid, 'title':title, 'img' : img } )
	
		return programs
		
	def getVideoLink(self, link_id):
		ret = common.parseDOM(self.getPage(self.URL['videolink'] + link_id), "source", {'type': 'video/mp4'}, ret = "src")
		if len(ret)>0:
			return ret[0]
		else:
			return None
