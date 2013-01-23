from xbmcswift2 import Plugin
from xbmcswift2 import xbmc
from resources.lib.katsomo import katsomo, NetworkError

__STRINGS__ = {
	'programs' : 30001,
	'newest' : 30002,
	'news' : 30003,
	'sports' : 30004,
	'kids' : 30005
}

plugin = Plugin()

katsomo = katsomo(plugin.addon.getSetting('username'), plugin.addon.getSetting('password'),plugin.addon.getAddonInfo('profile')+'cookies.txt')


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
		
@plugin.cached(60*12)
def getProgramDirs():
	return katsomo.getProgramDirs()

@plugin.cached(60*12)
def getPrograms(progid):
	return katsomo.getPrograms(progid)

@plugin.route('/')
def index():
    items = [
    	{'label': _('programs'), 'path': plugin.url_for('show_programs')},
    	{'label': _('news'), 'path' : plugin.url_for('show_program_count', progid='33001')},
    	{'label': _('sports'), 'path' : plugin.url_for('show_program_count', progid='33002')},
    	{'label': _('kids'), 'path' : plugin.url_for('show_program_count', progid='33003')}
    ]
    return items

@plugin.route('/ohjelmat/')
def show_programs():
	programDirs = getProgramDirs()
	items = [{
		'path'  : plugin.url_for('show_program_count',progid=(programDir['id'])),
		'label' : programDir['label']
	} for programDir in programDirs]
	return items

@plugin.route('/ohjelmat/<progid>/')
def show_program_count(progid):
	programs = getPrograms(progid)
	items = [{
		'label' : program['title'],
		'path' : plugin.url_for('play_program', playid=(program['playid'])),
		'is_playable' : True,
		'thumbnail' : program['img']
	} for program in programs]
	return items

@plugin.route('/play/<playid>')
def play_program(playid):
	return plugin.set_resolved_url(katsomo.getVideoLink(playid))


if __name__ == '__main__':
    plugin.run()
