from cookielib import LWPCookieJar, Cookie
from urllib2 import HTTPError, URLError
import urllib2,urllib,urlparse,re
import CommonFunctions as common
from datetime import datetime
import time

class NetworkError(Exception):
	pass

class katsomo():

	URL = { 
		'login' : 'http://m.katsomo.fi/katsomo/login',
		'programdir' : 'http://m.katsomo.fi/katsomo/programs',
		'programs' : 'http://m.katsomo.fi/katsomo/?treeId=',
		'videolink' : 'http://m.katsomo.fi/?progId='
	}

	def __init__(self, username="", password="", cookie_file=""):
		if not cookie_file == "":
			self.cj = LWPCookieJar(cookie_file)
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
		self.cj.set_cookie(self.makeCookie('hq','1'))
		self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
		self.user_agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 5_0 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko) Version/5.1 Mobile/9A334 Safari/7534.48.3'
	
	def makeCookie(self, name, value):
		return Cookie(
		    version=0, 
		    name=name, 
		    value=value,
		    port=None, 
		    port_specified=False,
		    domain="katsomo.fi", 
		    domain_specified=True, 
		    domain_initial_dot=False,
		    path="/", 
		    path_specified=True,
		    secure=False,
		    expires=None,
		    discard=False,
		    comment=None,
		    comment_url=None,
		    rest=None
		)
		
	def getPage(self, url,postvars={}, header_data = {}):
		req = urllib2.Request(url, urllib.urlencode(postvars), header_data)			
		req.add_header('user-agent', self.user_agent)
		try:
			resp = self.opener.open(req).read()
		except HTTPError, error:
			raise NetworkError('HTTPError: %s' % error)
		except URLError, error:
			raise NetworkError('URLError: %s' % error)
		return self.opener.open(req).read()
	
	def getLoginStatus(self):
		if self.noLogin:
			return False
		ret = common.parseDOM(self.getPage(self.URL['login']), "div", attrs = { "class": "login" })
		if not "/katsomo/logout" in ret:
			return self.doLogin()
		else:
			return True
			
	def doLogin(self):
		postvars = { 
			'u' : self.username,
			'p' : self.password
		}
		header_data = {
			'User-Agent' : self.user_agent,
			'Referer' : 'http://m.katsomo.fi/katsomo/login'
		}
		if "/katsomo/logout" in common.parseDOM(self.getPage(self.URL['login'], postvars, header_data), "div", attrs = { "class": "login" }):
			try:
				self.cj.save( ignore_discard=True )
			except IOError:
				pass
			return True
		else:
			self.cj.clear()
			return False
	
	def getCategories(self):
		ret = common.parseDOM(self.getPage(self.URL['programdir']), "li", {'class': 'initial'})
		return ret
	
	def getProgramDirs(self, category=''):	
		if category=='':
			ret = common.parseDOM(self.getPage(self.URL['programdir']), "div", {'id': 'programs-by-name'})
			ret = common.parseDOM(ret, "ul", {'class': 'all-programs-list'})
		else:
			ret = common.parseDOM(self.getPage(self.URL['programdir']), "div", {'id': 'programs-by-type'})
			ret = common.parseDOM(ret, "ul", {'class': 'all-programs-list'})
			out = []
			found = False
			ret = ret[0].split('\r')
			for result in ret:
				if found:
					if not '<li class="initial"' in result:
						out.append(result)
					else:
						found = False
				if '<li class="initial">' + category + '</li>' in result:
					found = True
			ret = out
		
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
		page = self.getPage(self.URL['programs'] + prog_id)
		serieplot = common.parseDOM(page, "div", {'class' : 'program-details' })
		serieplot = common.parseDOM(serieplot, "p")[0]
		ret = common.parseDOM(page, "div", {'class': 'program'})
		programs = []
		for r in ret:
			link = common.parseDOM(r, "a", ret = "href")[0]
			title = common.parseDOM(r, "p", {'class': 'program-name'})[0]
			plot = common.parseDOM(r, "p", {'class': 'program-abstract'})[0]
			if 'class="star"' in title and not self.getLoginStatus(): continue
			elif 'class="star"' in title and self.getLoginStatus() and self.scrapVideoLink(link) == None: continue	
			title += ' ' + common.parseDOM(r, "p", {'class': 'program-abstract'})[0]
			img = 'http://m.katsomo.fi' + common.parseDOM(r, "img", ret = "src")[0]
			timestamp = common.parseDOM(r, "p", {'class': 'timestamp'})[0]
			ts = None
			if 'TULOSSA' in timestamp:
				continue
			try:
				ts = datetime.strptime(timestamp.replace('- ',''), '%d.%m.%Y %H.%M')
			except TypeError:
				ts = datetime(*(time.strptime(timestamp.replace('- ',''), '%d.%m.%Y %H.%M')[0:6]))	
			timestamp = ts.strftime('%d.%m.%Y')
			#timestamp = str('{:%d.%m.%Y}'.format(ts))
			playid = urlparse.urlparse(link)[4].split('=')[1]
			programs.append( {'playid' : playid, 'title':title, 'img' : img, 'timestamp' : timestamp, 'plot' : serieplot + plot, 'plotoutline' : plot } )
		return programs
		
	def getVideoLink(self, link_id):
		ret = common.parseDOM(self.getPage(self.URL['videolink'] + link_id), "source", {'type': 'video/mp4'}, ret = "src")
		if len(ret)>0:
			return ret[0]
		else:
			return None
