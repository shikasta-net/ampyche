from collections import namedtuple
from hashlib import sha256
from os.path import join
from time import time
from urllib import urlopen, urlencode
from xml.dom import Node
from xml.dom.minidom import parse

### Data structures
class BaseObject(object):
  """ Base class for all of the API response containers. """
  def __str__(self):
    s = [self.__class__.__name__ + '(']
    for (k,v) in dict(self):
      s.append(k)
      s.append('=')
      s.append(repr(v))
    return ''.join(s)

class Artist(BaseObject):
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
               songs=None,
               tags=None,
               preciserating=None,
               rating=None):
    # initialize the attributes of this object
    for (k,v) in locals().items():
      if k != 'self':
        setattr(self, k, v)

class Album(BaseObject):
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

class Song(BaseObject):
  """ This class represents a respons from the song XML. It has the
  attributes listed below (which will be None if they were not present in the
  response):

  id - album id
  title - title of the song
  mime - the mime type of the song
  genre - the genre of the song
  genreid - the id of the genre
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
               title=None,
               mime=None,
               genre=None,
               genreid=None,
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

class Tag(BaseObject):
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

class Playlist(BaseObject):
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

class Video(BaseObject):
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
      # We also want to keep track of things like artist ids, as well as the
      # actual artist name.
      if node.hasAttribute('id'):
        d[node.tagName + 'id'] = node.getAttribute('id')
      d[node.tagName] = _get_text(node)
  return d

def _get_objects(element, tagname):
  """ Return a list of the Album, Artist, Song, Tag, Playlist or Video objects
  contained in the DOM. Can raise AmpacheAPIError if asked for an invalid tag
  name. """

  # Resolve the right container constructor for this tag. This will be used
  # later, but we do it here to catch tag name errors early.
  try:
    constructor = globals()[tagname.title()]
  except KeyError:
    raise AmpacheAPIError(9001, "Bad tag name: " + tagname)

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
        tags.append((node.getAttribute('id'), _get_text(tag)))
      d['tags'] = tags

    # Remove any errornous 'tag' attribute(s) that were collected.
    if 'tag' in d:
      del d['tag']
    if 'tagid' in d:
      del d['tagid']

    objects.append(constructor(**d))
  return objects

class AmpacheServer(object):
  def __init__(self, server, username, password):
    self.server = join(server, 'server/xml.server.php?')
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
    """ Set up this AmpacheServer to auth with the particular username or
    password. This is called by the constructor, so unless you're doing
    something fancy, you probably don't ever need to call this. """

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
    """ Keep the ampache connection alive. """
    return _dictify(self._request(action='ping'))

  def url_to_song(self, url):
    """ Get the song data back from a particular URL. Returns a single song
    object. """
    dom = self._request(action='url_to_song', url=url)
    [song] = _get_objects(dom, 'song')
    return song

  # Data Methods
  def artists(self, filter, exact=False, add=None, update=None):
    dom = self._request(action='artists', filter=filter, 
                        exact=exact, add=add, update=update)
    return _get_objects(dom, 'artist')

  def artist_songs(self, filter):
    dom = self._request(action='artist_songs', filter=filter)
    return _get_objects(dom, 'song')

  def artist_albums(self, filter):
    dom = self._request(action='artist_albums', filter=filter)
    return _get_objects(dom, 'album')

  # Control Methods
  def localplay(self, command):
    """ Control the localplay mode. """
    assert command in ['next', 'prev', 'stop', 'play']
    self._request(action='localplay', command=command)

  def democratic(self, method, oid=None):
    """ XXX: democratic() is not well supported, perhaps fix this? """
    assert oid or method not in ['vote', 'devote']
    self._request(action='democratic', method=method, oid=oid)

