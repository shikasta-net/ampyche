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
  """ Represents errors as specified here:
  http://ampache.org/wiki/dev:xmlapi:error """
  def __init__(self, code, message):
    self.code = code
    self.message = message

  def __str__(self):
    return 'ERROR ' + str(self.code) + ': ' + self.message

### Parsing functions.
def get_text(element):
  """ Get all of the text from a particular DOM element. """
  rc = []
  for node in element.childNodes:
    if node.nodeType in [Node.TEXT_NODE, Node.CDATA_SECTION_NODE]:
      rc.append(node.data)
  return ''.join(rc)

def dictify(element):
  d = {}
  for node in element.childNodes:
    if node.nodeType not in [Node.TEXT_NODE, Node.CDATA_SECTION_NODE]:
      d[node.tagName] = get_text(node)
  return d

def get_object(element, tagname):
  objects = []
  for node in element.getElementsByTagName(tagname):
    d = dictify(node)
    id = node.getAttribute('id')
    d['id'] = id

    # tags don't have tags, but everything else does
    if tagname != 'tag':
      d['tags'] = [ get_text(tag) for tag in node.getElementsByTagName('tag') ]
      if 'tag' in d:
        del d['tag']
      print d
    objects.append(d)
  return objects

class AmpacheServer(object):
  def __init__(self, server, username, password):
    self.server = server
    self.auth = self.handshake(username, password)['auth']

  def _request(self, **kwargs):
    """ Make the request to the server with the given arguments. If the request
    fails, raise an exception. Otherwise, return a DOM for use in extracting
    the results. """
    
    # filter out None values
    tmp = {}
    for (k,v) in kwargs.items():
      if v:
        tmp[k] = v
    kwargs = tmp

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
    
    return dictify(dom.childNodes[0])

  def ping(self):
    dictify(self._request(action='ping'))

  def url_to_song(self, url):
    return self._request(action='url_to_song', url=url)

  # Data Methods
  def artists(self, filter, exact=False, add=None, update=None):
    return get_object(self._request(action='artists', filter=filter, 
                      exact=exact, add=add, update=update), 'artist')

  def artist_songs(self, filter):
    return get_object(self._request(action='artist_songs', filter=filter), 'song')

  def artist_albums(self, filter):
    return get_object(self._request(action='artist_albums', filter=filter), 'album')
