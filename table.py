from system import *
from settings import *
db = SQLAlchemy()
class users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(5000), nullable=False)
    channel = db.relationship('channels', backref='owner', cascade="all, delete-orphan", uselist=False, lazy=True)
    likes = db.relationship('likes', backref='owner', cascade="all, delete-orphan")
    comments = db.relationship('comments', backref='owner', cascade="all, delete-orphan")
    subscribed = db.relationship('subscribers', backref='owner', cascade="all, delete-orphan")
    notification = db.relationship('notifications', backref='owner', cascade="all, delete-orphan")
    rcomments = db.relationship('replieswithincomment', backref='owner', cascade="all, delete-orphan")
    playlists = db.relationship('playlists', backref='owner', cascade="all, delete-orphan", lazy=True)
    reports_sent = db.relationship('reports', foreign_keys='reports.reporter_id', backref='author', lazy=True)
    reports_received = db.relationship('reports', foreign_keys='reports.reported_user_id', backref='target', lazy=True)    
    created = db.Column(db.DateTime, index=True)
    profilephoto = db.Column(db.String(400), default=defname)
    token = db.Column(db.String(500))
    nread = db.Column(db.Boolean, default=False)
    viewduration = db.Column(MutableDict.as_mutable(JSONB), default={})
    permanentdisabled = db.Column(db.Boolean, default=False)
    userclicks = db.Column(MutableList.as_mutable(JSONB), default=[])
    tokenreset = db.relationship('keys', backref='owner', cascade="all, delete-orphan")
    collect_data = db.Column(db.Boolean, default=True)

class channels(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    channelname = db.Column(db.String(50), nullable=False)
    videos = db.relationship('videos', backref='parent_channel', cascade="all, delete-orphan", lazy="select")
    subscribers = db.relationship('subscribers', backref='parent_channel', cascade="all, delete-orphan", lazy="select")
    ischannelenabled = db.Column(db.Boolean, default=False)
    channelicon = db.Column(db.String(500), default=defname)
    channelbanner = db.Column(db.String(500), default=defbanner)
    channeldesc = db.Column(db.String(500))
    created = db.Column(db.DateTime, index=True)  
    sub_count = db.Column(db.Integer, default=0, nullable=False)

class videos(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    playlists = db.relationship('playlistvideo', backref='parent_video', cascade="all, delete-orphan")
    comments = db.relationship('comments', backref='parent_video', order_by="desc(comments.created)", cascade="all, delete-orphan", lazy=True)        
    channel_id = db.Column(db.Integer, db.ForeignKey('channels.id', ondelete='CASCADE'), nullable=False, index=True)
    views = db.relationship('views', backref='parent_video', cascade="all, delete-orphan" , lazy="select")
    likes = db.relationship('likes', backref='parent_video', cascade="all, delete-orphan" , lazy="select")
    aisummary = db.Column(db.String(10000), nullable=True)
    created = db.Column(db.DateTime, index=True)
    display = db.Column(db.Boolean, nullable=False)
    file = db.Column(db.String(500), nullable=False)
    thumbnail = db.Column(db.String(500), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    token = db.Column(db.String(500), nullable=False)
    like_count = db.Column(db.Integer, default=0, nullable=False)
    view_count = db.Column(db.Integer, default=0, nullable=False)

class playlistvideo(db.Model):
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlists.id', ondelete="CASCADE"), primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id', ondelete="CASCADE"), primary_key=True)
    created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    __table_args__ = (db.UniqueConstraint('playlist_id', 'video_id', name='unqiuevideoperplaylist'),)         

class playlists(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=False)
    thumbnail = db.Column(db.String(500), nullable=False)
    display = db.Column(db.Boolean, nullable=False, default=False)
    created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    videos = db.relationship(
        'playlistvideo', 
        primaryjoin="playlists.id == playlistvideo.playlist_id", 
        backref='parent_playlist', 
        cascade="all, delete-orphan",
        lazy='select'
    )

class comments(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id', ondelete='CASCADE'), nullable=False, index=True)
    replieswithincomment = db.relationship('replieswithincomment', backref='parent_comment', order_by="desc(replieswithincomment.created)", cascade="all, delete-orphan")
    content = db.Column(db.String(300), nullable=False)
    created = db.Column(db.DateTime, index=True)

class replieswithincomment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(300), nullable=False)
    created = db.Column(db.DateTime, index=True)     
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

class likes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id', ondelete='CASCADE'), nullable=False, index=True) 
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    __table_args__ = (
        UniqueConstraint('user_id', 'video_id', name='unique_like'),)  

class subscribers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    channel_id = db.Column(db.Integer, db.ForeignKey('channels.id', ondelete='CASCADE'), nullable=False, index=True)
    created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    __table_args__ = (
        UniqueConstraint('user_id', 'channel_id', name='unique_subscription'),)   

class views(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id', ondelete='CASCADE'), nullable=False, index=True) 
    created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    token = db.Column(db.String(500), nullable=False)   
    show = db.Column(db.Boolean, default=True)

class notifications(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, default=datetime.utcnow, index=True)    
    title = db.Column(db.String(50), nullable=False)
    content = db.Column(db.String(300), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

class keys(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(500), nullable=False)
    exp_time = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    token = db.Column(db.String(500), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    session_token = db.Column(db.String(500), nullable=True)
    created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

class reports(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True, index=True)
    reported_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True, index=True)
    reason = db.Column(db.String(500), nullable=False)
    details = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending') 
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

class admin_users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100000), nullable=False)    
    token = db.Column(db.String(500), nullable=False)