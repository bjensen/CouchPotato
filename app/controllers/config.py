from app.config.cplog import CPLog
from app.config.db import QualityTemplate, Session as Db
from app.controllers import BaseController, redirect
from app.lib.qualities import Qualities
from app.lib.xbmc import XBMC
from app.lib.nmj import NMJ
from app.lib.plex import PLEX
from app.lib.prowl import PROWL
from app.lib.growl import GROWL
from app.lib.notifo import Notifo
import cherrypy
import json
import sys

log = CPLog(__name__)

class ConfigController(BaseController):

    @cherrypy.expose
    @cherrypy.tools.mako(filename = "config/index.html")
    def index(self):
        '''
        Config form
        '''
        config = cherrypy.config.get('config')

        renamer = self.cron.get('renamer')
        replacements = {
             'cd': ' cd1',
             'cdNr': ' 1',
             'ext': 'mkv',
             'namethe': 'Big Lebowski, The',
             'thename': 'The Big Lebowski',
             'year': 1998,
             'first': 'B',
             'original': 'The.Big.Lebowski.1998.1080p.BluRay.x264.DTS-GROUP',
             'group':'GROUP',
             'audio':'DTS',
             'video':'x264',
             'quality': '1080p',
             'sourcemedia': 'BluRay',
             'resolution' : '1920x1080'
        }

        trailerFormats = self.cron.get('trailer').formats
        foldernameResult = renamer.doReplace(config.get('Renamer', 'foldernaming'), replacements)
        filenameResult = renamer.doReplace(config.get('Renamer', 'filenaming'), replacements)

        return self.render({'trailerFormats':trailerFormats, 'foldernameResult':foldernameResult, 'filenameResult':filenameResult, 'config':config})

    @cherrypy.expose
    def save(self, **data):
        '''
        Save all config settings
        '''
        config = cherrypy.config.get('config')

        # catch checkboxes
        bools = filter(lambda s: not data.get(s),
            [
              'global.launchbrowser', 'global.updater',
              'XBMC.enabled', 'XBMC.onSnatch',
              'NMJ.enabled',
              'PLEX.enabled',
              'PROWL.enabled', 'PROWL.onSnatch',
              'GROWL.enabled', 'GROWL.onSnatch',
              'Notifo.enabled', 'Notifo.onSnatch',
              'Meta.enabled',
              'MovieETA.enabled',
              'Renamer.enabled', 'Renamer.trailerQuality', 'Renamer.cleanup',
              'Torrents.enabled',
              'NZB.enabled',
              'NZBMatrix.enabled', 'NZBMatrix.english', 'NZBMatrix.ssl',
              'NZBsRUS.enabled',
              'newzbin.enabled',
              'NZBsorg.enabled',
              'newznab.enabled',
              'Subtitles.enabled', 'Subtitles.addLanguage',
              'MovieRSS.enabled',
            ]
        )
        data.update(data.fromkeys(bools, False))

        # Do quality order
        order = data.get('Quality.order').split(',')
        for id in order:
            qo = Db.query(QualityTemplate).filter_by(id = int(id)).one()
            qo.order = order.index(id)
            Db.flush()
        del data['Quality.order']

        # Save templates
        if data.get('Quality.templates'):
            templates = json.loads(data.get('Quality.templates'))
            Qualities().saveTemplates(templates)
        del data['Quality.templates']

        # Save post data
        for name in data:
            section = name.split('.')[0]
            var = name.split('.')[1]
            config.set(section, var, data[name])

        # Change cron interval
        self.cron.get('yarr').setInterval(config.get('Intervals', 'search'))

        config.save()

        self.flash.add('config', 'Settings successfully saved.')
        return redirect(cherrypy.request.headers.get('referer'))

    def testXBMC(self, **data):

        xbmc = XBMC()
        xbmc.test(data.get('XBMC.host'), data.get('XBMC.username'), data.get('XBMC.password'))

        return ''

    @cherrypy.expose
    def testNMJ(self, **data):

        nmj = NMJ()
        nmj.test(data.get('NMJ.host'), data.get('NMJ.database'), data.get('NMJ.mount'))

        return ''

    @cherrypy.expose
    def autoNMJ(self, **data):

        nmj = NMJ()
        cherrypy.response.headers['Content-Type'] = 'text/javascript'
        return nmj.auto(data.get('NMJ.host'))

    @cherrypy.expose
    def testPLEX(self, **data):

        plex = PLEX()
        plex.test(data.get('PLEX.host'))

        return ''

    @cherrypy.expose
    def testGROWL(self, **data):

        growl = GROWL()
        growl.test(data.get('GROWL.host'), data.get('GROWL.password'))

        return ''

    @cherrypy.expose
    def testPROWL(self, **data):

        prowl = PROWL()
        prowl.test(data.get('PROWL.keys'), data.get('PROWL.priority'))
        return ''

    @cherrypy.expose
    def testNotifo(self, **data):

        notifo = Notifo()
        notifo.test(data.get('Notifo.username'), data.get('Notifo.key'))

        return ''

    @cherrypy.expose
    def exit(self):

        cherrypy.engine.exit()
        sys.exit()

    @cherrypy.expose
    def restart(self):

        cherrypy.engine.restart()

    @cherrypy.expose
    def update(self):

        updater = cherrypy.config.get('updater')
        result = updater.run()

        return 'Update successful, restarting...' if result else 'Update failed.'

    @cherrypy.expose
    def checkForUpdate(self):

        updater = cherrypy.config.get('updater')
        updater.checkForUpdate()

        return redirect(cherrypy.request.headers.get('referer'))

    @cherrypy.expose
    @cherrypy.tools.mako(filename = "config/userscript.js")
    def userscript(self, **data):
        '''
        imdb UserScript, for easy movie adding
        '''
        cherrypy.response.headers['Content-Type'] = 'text/javascript'
        return self.render({'host':data.get('host')})

