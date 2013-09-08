# coding=utf-8
import os
import re
import urllib2

from operator import itemgetter
from xml.dom.minidom import parse
from werkzeug.urls import url_fix
from tornado.util import ObjectDict


API_KEY = 'Get it in dictionaryapi.com'

g = ObjectDict()

class WordDict(ObjectDict):
    def __init__(self, word):
        self.data = word
        self.entry = []
        self.suggestion = []

    def collect(self, entry):
        self.entry.append(entry)

    def suggest(self, suggestion):
        self.suggestion.append(suggestion)


class EntryDict(ObjectDict):
    def __init__(self, entry):
        self.definition = []

    def parse(self, entry):
        elements = ['ew', 'hw', 'fl', 'cx', 'def']
        for element in elements:
            if element == 'hw':
                if entry.getElementsByTagName('hw'):
                    self['hw'] = getText(entry.getElementsByTagName('hw')[0].childNodes)
                    g.entry.hindex = entry.getElementsByTagName('hw')[0].getAttribute('hindex')
            elif element == 'def':
                if entry.getElementsByTagName('def'):
                    handleDefinition(entry.getElementsByTagName('def')[0])
            elif entry.getElementsByTagName(element):
                self[element] = getText(entry.getElementsByTagName(element)[0].childNodes)
        for node in entry.childNodes:
            if node.nodeType == node.ELEMENT_NODE:
                if node.tagName == 'sound':
                    wav = node.getElementsByTagName('wav')[0].firstChild.data
                    self['audio'] = wav.split('.')[0]
                    if wav.startswith('bix'):
                        self['wav'] = 'http://media.merriam-webster.com/soundc11/bix/' + wav
                    elif wav.startswith('gg'):
                        self['wav'] = 'http://media.merriam-webster.com/soundc11/gg/' + wav
                    elif wav[0].isdigit():
                        self['wav'] = 'http://media.merriam-webster.com/soundc11/number/' + wav
                    else:
                        self['wav'] = 'http://media.merriam-webster.com/soundc11/' + wav[0] + '/' + wav


    def define(self, definition):
        self.definition.append(definition)


class DefinitionDict(ObjectDict):
    pass


def getText(nodelist):
    text = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            if node.data.startswith(':'):
                text.append(node.data[1:])
            elif node.data.startswith(' :'):
                text.append(node.data[2:])
            else:
                text.append(node.data)
        elif node.nodeType == node.ELEMENT_NODE:
            if node.tagName == 'sx':
                text.append('<a href="' + node.firstChild.data + '">' + '<span class="' + node.tagName + '">' + getText(node.childNodes) + '</span></a>')
            elif node.tagName in ['sx', 'vi', 'it']:
                text.append('<span class="' + node.tagName + '">' + getText(node.childNodes) + '</span>')
            else:
                text.append(getText(node.childNodes))
    return ''.join(text)


def handleWord(word):
    g.word = WordDict(word)
    url = 'http://dictionaryapi.com/api/v1/references/collegiate/xml/%s?key=%s' % (word, API_KEY)
    xml = urllib2.urlopen(url_fix(url))
    try:
        dom = parse(xml)
    except:
        return g.word
    if dom.getElementsByTagName('entry'):
        handleEntries(dom.getElementsByTagName('entry'))
    else:
        handleSuggestion(dom.getElementsByTagName('suggestion'))
    return g.word


def handleEntries(entries):
    for entry in entries:
        if entry.hasAttribute('id'):
            handleEntry(entry)


def handleEntry(entry):
    g.entry = EntryDict(entry)
    g.entry.parse(entry)
    g.word.collect(g.entry)


def handleDefinition(definition):
    d = DefinitionDict()
    for node in definition.childNodes:
        if node.nodeType == node.ELEMENT_NODE:
            if node.tagName == 'vt':
                d.vt = getText(node.childNodes)
            elif node.tagName == 'sn':
                d.sn = getText(node.childNodes)
                if d.sn[0].isdigit():
                    d.primary = d.sn.split()[0]
                d.secondary = ''.join(re.compile('[a-z]').findall(d.sn))
                d.tertiary = ''.join(re.compile('\((.*?)\)').findall(d.sn))
            elif node.tagName == 'sd':
                d.sd = getText(node.childNodes)
            elif node.tagName == 'ssl':
                d.ssl = getText(node.childNodes)
            elif node.tagName == 'dt':
                d.dt = getText(node.childNodes)
                g.entry.define(d)
                d = DefinitionDict()


def handleSuggestion(suggestions):
    for suggestion in suggestions:
        g.word.suggest(getText(suggestion.childNodes))
