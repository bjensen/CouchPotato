
from moviemanager.model import Movie, Feed
from moviemanager.model.meta import Session as Db
import Queue
import datetime
import logging
import threading
import time

log = logging.getLogger(__name__)

NzbCronQueue = Queue.Queue()
class NzbCron(threading.Thread):
    
    ''' Cronjob for searching for NZBs '''

    lastChecked = 0
    interval = 60 #minutes
    provider = None
    sabNzbd = None

    def run(self):
        log.info('NzbCron thread is running.')
        time.sleep(10)

        self.lastChecked = time.time()
        self.intervalSec = (self.interval * 60)

        while True:
            now = time.time()

            self.searchNzbs()

            self.lastChecked = now

            log.info('Sleeping NzbCron for %d seconds' % self.intervalSec)
            time.sleep(self.intervalSec)

    def searchNzbs(self):
        log.info('Searching for NZB.')

        #get al wanted movies
        movies = Db.query(Movie).filter_by(status = u'want')

        for movie in movies:
            self._searchNzb(movie)

            log.info('Sleeping search for 2 sec')
            time.sleep(2)

    def _searchNzb(self, movie):

        results = self.provider.find(movie.name, movie.quality)

        #remove old cached feeds
        [Db.delete(x) for x in movie.Feeds]
        Db.commit()

        #add results to feed cache
        for result in results:
            new = Feed()
            new.movieId = movie.id
            new.name = result.name
            new.dateAdded = datetime.datetime.strptime(result.date, '%a, %d %b %Y %H:%M:%S +0000')
            new.link = self.provider.downloadLink(result.id)
            new.contentId = result.id
            new.score = self.provider.calcScore(result, movie)
            new.size = result.size

            Db.add(new)

        #send highest to SABnzbd & mark as snatched
        if len(movie.Feeds) > 0:
            nzb = movie.Feeds.pop(0)
            success = self.sabNzbd.send(nzb.link)
            if success:
                movie.status = u'snatched'
                Db.commit()
                    
        Db.commit()

def startNzbCron():
    cron = NzbCron()
    cron.start()

    return cron