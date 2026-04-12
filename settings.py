import os
defname='def.svg'
defbanner='defbanner.jpg'
photos='profilephotos'
success="success"
error="danger"
info='info'
banners='bannerimage'
videofolder='videos'
thumbnailfolder='thumbnails'
base = os.path.dirname(os.path.abspath(__file__))
defaultimage=os.path.join(base,'static',photos,defname)
bannerpath=os.path.join(base,'static',banners)
folderpath=os.path.join(base,'static',photos)
videospath=os.path.join(base,'static',videofolder)
thumbnailspath=os.path.join(base,'static',thumbnailfolder)
vttfolderpath = os.path.join(base, 'static','captions')