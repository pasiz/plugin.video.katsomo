from xbmcswift2 import Plugin
from xbmcswift2 import xbmc
from resources.lib.katsomo import katsomo, NetworkError
import SimpleDownloader as downloader

downloader = downloader.SimpleDownloader()
plugin = Plugin()

__STRINGS__ = {
	'programs' 		: 30001,
	'newest' 		: 30002,
	'news' 			: 30003,
	'sports' 		: 30004,
	'kids' 			: 30005,
	'categories'	: 30006,
	'download'		: 30007
}

katsomo = katsomo(plugin.addon.getSetting('username'), plugin.addon.getSetting('password'),plugin.addon.getAddonInfo('profile')+'cookies.txt')
if plugin.addon.getSetting('cache_lifetime') != '':
	cache_lifetime = int(float(plugin.addon.getSetting('cache_lifetime')))
else:
	cache_lifetime = 1

def clearCaches():
	if katsomo.clearCache:
		cache_data = plugin.get_storage('.functions')
		cache_data.clear()
		cache_data.sync()
		katsomo.clearCache = False
		plugin.log.info('cache cleared')

def _(language):
	if language in __STRINGS__:
		try:
			return plugin.get_string(__STRINGS__[language])
		except:
			return language
			plugin.log.warning('String is missing: %s' % language)
	else:
		plugin.log.warning('String is missing: %s' % language)
		return language
		
@plugin.cached(TTL=cache_lifetime)
def getProgramDirs(category=''):
	return katsomo.getProgramDirs(category)

@plugin.cached(TTL=cache_lifetime)
def getCategories():
	return katsomo.getCategories()

@plugin.cached(TTL=cache_lifetime)
def getPrograms(progid):
	return katsomo.getPrograms(progid)

@plugin.route('/')
def index():
	clearCaches()
	categories = getCategories()
	items = [{'label': _('programs'), 'path' : plugin.url_for('show_programs')}]
	items += [{
		'path' : plugin.url_for('show_programs_content', content=(category)),
		'label' : category
	} for category in categories]
	return items

@plugin.route('/ohjelmat/', name='show_programs')
@plugin.route('/ohjelmat/<content>/', name='show_programs_content')
def show_programs(content=''):
	clearCaches()
	programDirs = getProgramDirs(content)
	items = [{
		'path'  : plugin.url_for('show_program_count',progid=(programDir['id'])),
		'label' : programDir['label']
	} for programDir in programDirs]
	return items

@plugin.route('/ohjelma/<progid>/')
def show_program_count(progid):
	clearCaches()
	programs = getPrograms(progid)
	items = [{
		'label' : program.get('title'),
		'path' : plugin.url_for('play_program', playid=program.get('playid')),
		'is_playable' : True,
		'thumbnail' : program.get('img'),
		'info': {
			'plot' : program.get('plot'),
			'plotoutline' : program.get('plotoutline'),
			'aired' : program.get('timestamp'),
		},
		'context_menu' : [
			(_('download'),'XBMC.RunPlugin(%s)' % plugin.url_for('download_program', playid=program.get('playid'), title=program.get('title'))),
		],
	} for program in programs]
	return items

@plugin.route('/download/<playid>/<title>')
def download_program(playid, title):
	params = {
		'url' : katsomo.getVideoLink(playid),
		'download_path' : plugin.addon.getSetting('download_folder'),
		'Title' : title,
	}
	downloader.download(title+'.mp4', params)

@plugin.route('/play/<playid>')
def play_program(playid):
	return plugin.set_resolved_url(katsomo.getVideoLink(playid))


if __name__ == '__main__':
    plugin.run()
