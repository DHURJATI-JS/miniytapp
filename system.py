
import eventlet
eventlet.monkey_patch()
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import *
from sqlalchemy.ext.mutable import MutableList, MutableDict
from flask_migrate import Migrate
from flask import Flask,render_template,redirect,request,url_for,flash,session,g,jsonify,has_request_context
import math
import ast
import gc
import traceback
import pickle
from werkzeug.security import generate_password_hash,check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime,timedelta
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSONB
from datetime import timedelta
from flask_wtf.csrf import CSRFProtect, CSRFError
from types import SimpleNamespace
from sqlalchemy.orm import joinedload,contains_eager,subqueryload,validates,selectinload,aliased,lazyload
from sqlalchemy.ext.hybrid import hybrid_property
from flask_apscheduler import APScheduler
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from jinja2.exceptions import UndefinedError
from moviepy import VideoFileClip
from functools import wraps
import subprocess
from nplusone.ext.flask_sqlalchemy import NPlusOne
import smtplib
from werkzeug.exceptions import Unauthorized
from sqlalchemy import event
from email.message import EmailMessage
import os
import uuid
import ollama
import nh3
import threading
from markupsafe import Markup
import base64
from flask_talisman import Talisman
from flask_limiter import RateLimitExceeded
from flask_socketio import *
import time
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_session import Session
from limits import parse
import redis
import secrets
from sqlalchemy.orm import undefer,load_only
import flask_socketio
import threading
import json
from walrus import Database
import psutil
import GPUtil
from sqlalchemy.exc import SQLAlchemyError 
from werkzeug.exceptions import HTTPException
from werkzeug.exceptions import HTTPException
from flask_executor import Executor
import logging
from collections import Counter
from operator import attrgetter
from werkzeug.datastructures import MultiDict
from email_validator import validate_email, EmailNotValidError
WhisperModellocation = os.path.join(os.path.dirname(os.path.abspath(__file__)),"models","whisper-turbo")
innerdomain="localhost"
ollamaserver=f'http://{innerdomain}:11434'
storage=f'redis://{innerdomain}:6379/'
localdomain='http://127.0.0.1:5000' #use 127... to avoid socektio errors
database="postgresql://postgres:kali@localhost:5432/db"
productiondomain="https://undenunciatory-untreacherous-rick.ngrok-free.dev"
productionmode=False
domainname=productiondomain if productionmode else  localdomain
allowed_origins=[domainname , localdomain]
system=Flask(__name__)
system.secret_key = str(uuid.uuid4())
system.config['SESSION_REFRESH_EACH_REQUEST'] = True
system.config['SESSION_TYPE'] = 'redis'
system.config['SESSION_REDIS'] = redis.from_url(storage+"0")
system.config['EXECUTOR_MAX_WORKERS'] = 1
system.config['RATELIMIT_STORAGE_URI']= storage
system.config['WTF_CSRF_TIME_LIMIT'] = 600
system.config['SESSION_PERMANENT'] = True
system.config['SQLALCHEMY_DATABASE_URI'] = database
system.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
system.config['ALLOWED_IMAGE_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp','svg'}
system.config['ALLOWED_VIDEO_EXTENSIONS'] = {'mp4', 'mov', 'avi', 'mkv', 'webm'}
system.config['NPLUSONE_RAISE'] = False 
system.wsgi_app = ProxyFix(system.wsgi_app, x_for=1, x_proto=1, x_host=1)
system.config['MAX_CONTENT_LENGTH']=500*1024*1024
system.permanent_session_lifetime = timedelta(days=7)
Session(system)
CSRFProtect(system)
if productionmode:
    system.secret_key = str(uuid.uuid4())
else:
    system.secret_key="xyz"
executor=Executor(system) 
socketio = SocketIO(system, cors_allowed_origins='*',async_mode='eventlet',max_http_buffer_size=1 * 1024 * 1024,
    ping_timeout=51, 

    ping_interval=5,manage_session=False,
    message_queue=storage)
socketdomain="wss://"+domainname.removeprefix("https://").removeprefix("http://")
csp = {
    'default-src': "'self'",
    'connect-src': [
        "'self'", 
        socketdomain, 
        domainname, 
        ollamaserver,
    ],
    'script-src': [
        "'self'", 
        "'unsafe-inline'", 
        "'unsafe-eval'"  
    ],
    'default-src': "'self'",
    'media-src': ["'self'", "blob:", "data:", "*"], 
    'style-src': ["'self'", "'unsafe-inline'"],
    'font-src': ["'self'", "data:", "*"], 
    'img-src': ["'self'", "data:", "blob:" , "*"],
    'form-action': "'self'"
}
Talisman(
    system,
    content_security_policy=csp,
    force_https=False,           
    session_cookie_secure=False,  
    session_cookie_http_only=False,
    frame_options='DENY',
    x_xss_protection=True
)
maxrecommenedvideo=50
defaultadminpassword="admin"
maxaiprompts=10
maxvideoperpage=12
maxchannelsperpage=30
randomizer=True
maxplaylistsperpage=10
maxreportsperpage=500
maxchannels=10
maxvideoupload=50
maxcommentspervideo=40
maxiinercommentspervideo=40
maxvideoinplaylist=30
maxplaylists=20
maxnotifications=20
maxipromptlength=100
processpower=60
client = ollama.Client(host=ollamaserver,timeout=10.0)
if processpower<maxvideoperpage or processpower<maxchannelsperpage or processpower<maxrecommenedvideo:
    raise("Increase processing power!")
appname="YT"
#dont remove anything
category = [
    "Humour",
    "Music", "Gaming", "Programming", "Artificial Intelligence", 
    "Content Creation", "Cybersecurity", "Health & Wellness", 
    "Personal Finance", "Digital Art", "Travel", "Sustainability",
    "Data Science", "Web Development", "Mobile App Dev", "Cloud Computing",
    "DevOps", "Game Development", "Blockchain & Web3", "UI/UX Design",
    "Embedded Systems", "Robotics", "Open Source",
    "Motion Graphics", "Photography", "Video Editing", "3D Modeling",
    "Animation", "VFX", "Music Production", "Filmmaking", 
    "Creative Writing", "Podcasting", "Graphic Design",
    "Entrepreneurship", "Digital Marketing", "Project Management", 
    "Leadership", "Public Speaking", "E-commerce", "Investing", 
    "Product Management", "Remote Work",
    "Cooking & Culinary", "Fitness", "Mental Health", "DIY & Crafting", 
    "Education", "History", "Science & Space", "Photography", 
    "Automotive", "Sports", "Self-Improvement"
]
mostsearched = [f"Search for {line.strip()}..." for line in open("recommend.txt") if line.strip()]
def updaterec():
    mostsearched[:] = [f"Search for {line.strip()}..." for line in open("recommend.txt") if line.strip()]

category[:]=[x.lower() for x in category ]
myemail="dhurjatisharma2010@gmail.com"
myemailkey="nifn azve dngv sibi"
def get_video_duration(file_path):
    clip = VideoFileClip(file_path)
    duration = clip.duration  
    clip.close() 
    return duration
def purge_executor_queue():
    global executor
    try:
        executor.shutdown(wait=False, cancel_futures=True) 
        print("Queue purged! Restarting executor...")
        executor.init_app(system) 
    except Exception as e:
        print(f"Error purging queue: {e}")

cdata = Database.from_url(storage)
try:
    if cdata.ping():
        print("✅ REDIS CONNECTED.")
except Exception as e:
    print(f"❌ REDIS ERROR: Could not connect. {e}")
active_tasks=cdata.Hash('active_tasks') 
request_count={}
acchats={}
alrimproved={}
cachedvid=cdata.Hash('cachedvid')
clear_all_data = lambda: [
    active_tasks.clear(),   
    cachedvid.clear(),      
    request_count.clear(),  
    acchats.clear(),        
    alrimproved.clear()     
]
def createtaskai(basefx):
    @wraps(basefx)
    def _e(*a, **b):
        uid = session.get("user_id")
        if has_request_context() and request.method=="POST":
            l = str(uuid.uuid4())
            active_tasks[uid] = json.dumps((l, True, time.time()))
            b['aitoken'] = l
        return basefx(*a, **b)
    return _e    
def auto_purge_scheduler():
    while True:
        time.sleep(60) 
        print("Running scheduled 60s purge...")
        for entry in active_tasks:
            try:
                user_id_bytes, data_bytes = entry
                
                user_id = user_id_bytes.decode('utf-8')
                data_str = data_bytes.decode('utf-8')
                
                data_list = json.loads(data_str)
                
                if len(data_list) > 1 and (data_list[1] is False or (time.time()-data_list[2]>60)):
                    print(f"Delelting :{user_id}")
                    del active_tasks[user_id]
                    
            except (ValueError, json.JSONDecodeError, IndexError, UnicodeDecodeError):
                continue
        purge_executor_queue()

last_check_time = 0
cached_result = True     

