from collections import namedtuple
from hashlib import sha256
from time import time
from urllib import urlopen, urlencode
from xml.dom import Node
from xml.dom.minidom import parse

# Data structures
class Artist(object):
  """ This class represents a respons from the artist XML. It has the
  attributes listed below (which will be None if they were not present in the
  response):

  id - artist id
  name - artist name
  albums - number of albums the artist has
  songs - number of songs the artist has
  tags - list of (tagid, tagstring) tuples
  preciserating
  rating
  """
  def __init__(self,
               id=None,
               name=None,
               albums=None,
               tags=None,
               preciserating=None,
               rating=None):
    # initialize the attributes of this object
    for (k,v) in locals().items():
      if k != 'self':
        setattr(self, k, v)

class Album(object):
  """ This class represents a respons from the album XML. It has the
  attributes listed below (which will be None if they were not present in the
  response):

  id - album id
  name - album name
  artist - artist who wrote the album
  artistid - artist id of the artist
  tracks - number of tracks the album has
  disk - the disk number
  tags - list of (tagid, tagstring) tuples
  art - the album art
  preciserating
  rating
  """
  def __init__(self,
               id=None,
               name=None,
               artist=None,
               artistid=None,
               tracks=None,
               disk=None,
               tags=None,
               art=None,
               preciserating=None,
               rating=None):
    # initialize the attributes of this object
    for (k,v) in locals().items():
      if k != 'self':
        setattr(self, k, v)

class Song(object):
  """ This class represents a respons from the song XML. It has the
  attributes listed below (which will be None if they were not present in the
  response):

  id - album id
  artist - artist who wrote the album
  artistid - artist id of the artist
  album - album the song is on
  albumid - the id of the album
  tags - list of (tagid, tagstring) tuples
  track - the track number on the album
  time - the length of the album in seconds
  url - the ampache url for the song
  size - song size in bytes
  art - the album art
  preciserating
  rating
  """
  def __init__(self,
               id=None,
               artist=None,
               artistid=None,
               album=None,
               albumid=None,
               tags=None,
               track=None,
               time=None,
               url=None,
               size=None,
               art=None,
               preciserating=None,
               rating=None):
    # initialize the attributes of this object
    for (k,v) in locals().items():
      if k != 'self':
        setattr(self, k, v)

class Tag(object):
  """ This class represents a respons from the tag XML. It has the
  attributes listed below (which will be None if they were not present in the
  response):

  id - album id
  name - tag name
  albums - number of albums with this tag
  songs - number of songs with this tag
  video - number of videos with this tag
  playlist - number of playlists with this tag
  stream - number of ?? with this tag
  """
  def __init__(self,
               id=None,
               name=None,
               albums=None,
               songs=None,
               video=None,
               playlist=None,
               stream=None):
    # initialize the attributes of this object
    for (k,v) in locals().items():
      if k != 'self':
        setattr(self, k, v)

class Playlist(object):
  """ This class represents a respons from the playlist XML. It has the
  attributes listed below (which will be None if they were not present in the
  response):

  id - album id
  name - playlist name
  owner - user who owns the playlist
  items - number of things in the playlist
  tags - playlist tags
  type - playlist type (e.g. "Public")
  """
  def __init__(self,
               id=None,
               name=None,
               owner=None,
               items=None,
               tags=None,
               type=None):
    # initialize the attributes of this object
    for (k,v) in locals().items():
      if k != 'self':
        setattr(self, k, v)

class Video(object):
  """ This class represents a respons from the video XML. It has the
  attributes listed below (which will be None if they were not present in the
  response):

  id - album id
  title - video title
  mime - video mime type
  resolution - video resolution (e.g. "720x288")
  size - size in bytes
  tags - tags of the video
  url - url of the video
  """
  def __init__(self,
               id=None,
               title=None,
               mime=None,
               resolution=None,
               size=None,
               tags=None,
               url=None):
    # initialize the attributes of this object
    for (k,v) in locals().items():
      if k != 'self':
        setattr(self, k, v)

class AmpacheAPIError(Exception):
  """ Represents errors as specified here:
  http://ampache.org/wiki/dev:xmlapi:error """
  def __init__(self, code, message):
    self.code = code
    self.message = message

  def __str__(self):
    return 'ERROR ' + str(self.code) + ': ' + self.message

### Parsing functions.
def _get_text(element):
  """ Get all of the text from a particular DOM element. """
  rc = []
  for node in element.childNodes:
    if node.nodeType in [Node.TEXT_NODE, Node.CDATA_SECTION_NODE]:
      rc.append(node.data)
  return ''.join(rc)

def _dictify(element):
  """ Turn the node into a dict, where the keys in the dict are the child tag
  names, and the values are their cdata. """
  d = {}
  for node in element.childNodes:
    if node.nodeType not in [Node.TEXT_NODE, Node.CDATA_SECTION_NODE]:
      if node.hasAttribute('id'):
        d[node.tagName + 'id'] = node.getAttribute('id')
      d[node.tagName] = _get_text(node)
  return d

def _get_object(element, tagname):
  """ Get a dictionary representation of an "object", where an object is one
  of: artist, album, song, tag, playlist, video. The dicts returned have a few
  corner cases:
    song['id'] is the id as returned by the API
    song['tags'] is a list of the tag strings returned by the API

  Everything else is just stored as tagname : cdata in the dict.
  """
  objects = []
  for node in element.getElementsByTagName(tagname):
    # Grab the regular elements
    d = _dictify(node)

    # add the id
    d['id'] = node.getAttribute('id')

    # Tags don't have tags, but everything else does.
    if tagname != 'tag':
      tags = []
      for tag in node.getElementsByTagName('tag'):
        tags.append((node.getAttribute('id'), _get_text(tag))
      d['tags'] = tags

    # Remove any errornous 'tag' attribute(s) that were collected.
    if 'tag' in d:
      del d['tag']
    if 'tagid' in d
      del d['tagid']

    objects.append(d)
  return objects

class AmpacheServer(object):
  def __init__(self, server, username, password):
    self.server = server
    self.auth = self.handshake(username, password)['auth']

  def _request(self, **kwargs):
    """ Make the request to the server with the given arguments. If the request
    fails, raise an exception. Otherwise, return a DOM for use in extracting
    the results.
    
    This method adds in the self.auth value to the request if it is not already
    present (i.e. you probably don't ever need to worry about
    authenticating)."""
    
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
        message = _get_text(error)
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
    
    return _dictify(dom.childNodes[0])

  def ping(self):
    _dictify(self._request(action='ping'))

  def url_to_song(self, url):
    return self._request(action='url_to_song', url=url)

  # Data Methods
  def artists(self, filter, exact=False, add=None, update=None):
    return _get_object(self._request(action='artists', filter=filter, 
                      exact=exact, add=add, update=update), 'artist')

  def artist_songs(self, filter):
    return _get_object(self._request(action='artist_songs', filter=filter), 'song')

  def artist_albums(self, filter):
    return _get_object(self._request(action='artist_albums', filter=filter), 'album')

