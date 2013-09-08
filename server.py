# coding=utf-8

import tornado.ioloop

from webster import handleWord
from tornado.template import Loader
from tornado.web import RequestHandler, StaticFileHandler, Application


class MainHandler(RequestHandler):
    def get(self):
        self.render('index.html')

class WordHandler(RequestHandler):
    def get(self, word):
        dictionary = handleWord(word.lower())
        self.render('word.html', word=word, dictionary=dictionary)

if __name__ == "__main__":
    application = Application([
        (r"/", MainHandler),
        (r"/(.*)", WordHandler),
    ])
    application.listen(4741)
    tornado.ioloop.IOLoop.instance().start()
