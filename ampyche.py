from collections import namedtuple
from hashlib import sha256
from time import time
from urllib import urlopen, urlencode
from xml.dom import Node
from xml.dom.minidom import parse


# Data structures
Artist = namedtuple('Artist', ['id', 'name', 'albums', 'songs', 
                               'tags', 'preciserating', 'rating'])
Album = namedtuple('Album', ['id', 'name', 'artist', 'year', 'tracks', 'disk', 
                             'tags', 'art', 'preciserating', 'rating'])
Song = namedtuple('Song', ['id', 'title', 'artist', 'album', 'tags', 'track', 'time',
                           'url', 'size', 'art', 'preciserating', 'rating'])
Tag = namedtuple('Tag', ['id', 'name', 'albums', 'artists', 'songs', 
                         'video', 'playlist', 'stream'])
Playlist = namedtuple('Playlist', ['id', 'name', 'owner', 'items', 'tags', 'type'])
Video = namedtuple('Video', ['id', 'title', 'mime', 'resolution', 'size', 'tags', 'url'])

class AmpacheAPIError(Exception):
  def __init__(self, code, message):
    self.code = code
    self.message = message

  def __str__(self):
    return 'ERROR ' + str(self.code) + ': ' + self.message

def get_text(element):
  """ Get all of the text from a particular DOM element. """
  rc = []
  for node in element.childNodes:
    if node.nodeType == Node.TEXT_NODE or Node.CDATA_SECTION_NODE:
      rc.append(node.data)
  return ''.join(rc)

class AmpacheServer(object):
  def __init__(self, server, username, password):
    self.server = server
    self.auth = self.handshake(username, password)['auth']

  def _request(self, **kwargs):
    """ Make the request to the server with the given arguments. If the request
    fails, raise an exception. Otherwise, return a DOM for use in extracting
    the results. """
    
    # add our auth if it's not already in the request
    if 'auth' not in kwargs:
      kwargs['auth'] = self.auth

    print urlopen(self.server + urlencode(kwargs.items())).read()
    dom = parse(urlopen(self.server + urlencode(kwargs.items())))

    errors = dom.getElementsByTagName('error')
    if len(errors) >= 1:
      # really, we expect only one error
      assert len(errors) == 1
      for error in errors:
        code = error.getAttribute('code')
        message = get_text(error)
        raise AmpacheAPIError(code, message)
    return dom

  # Non-Data Methods
  def handshake(self, username, password):
    ts = str(int(time()))
    passphrase = sha256(ts + sha256(password).hexdigest()).hexdigest()
    
    dom = self._request(
      action = 'handshake',
      auth = passphrase,
      timestamp = ts,
      version = 350001,
      user = username,
    )

    d = {}
    for node in dom.childNodes[0].childNodes:
      if node.nodeType != Node.TEXT_NODE:
        d[node.tagName] = get_text(node)
    return d

  def ping(self):
    return self._request(action='ping')

  def url_to_song(self, url):
    return self._request(action='url_to_song', url=url)

  # Data Methods
