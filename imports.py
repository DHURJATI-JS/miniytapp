from table import *
from settings import *
from system import *
currentdb=db.session    
def removefiles(filename,path):
   if filename in [defbanner,defname]:return None
   p=os.path.join(path,filename)
   if os.path.exists(p) and os.remove(p):return True
def get_all_files(folderpath):
    files=[t for t in os.listdir(folderpath) ]
    return files
success="success"
error="danger"
currentdb=db.session
def getpath(mainame,banner=False):
    if banner:
        return os.path.join('/static', banners , mainame)
    return os.path.join('/static', photos, mainame)
def savetopc(file,returnfilename,folderpathoffile=folderpath):
    os.makedirs(folderpathoffile, exist_ok=True)
    new_filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
    save_path = os.path.join(folderpathoffile, new_filename)
    file.save(save_path)
    if returnfilename:
        return new_filename
    print(f"Saved as {new_filename}")
def checkfilesize(file,maxsizeinmb):
    file.seek(0,2)
    size=file.tell()
    file.seek(0)
    if size>maxsizeinmb*1024**2:
        flash("File size exceeded the limit given" ,error)
        return False
    return True    
def send_email(content,to,myemail=myemail,myemailkey=myemailkey,bcc=True):
    msg=EmailMessage()
    msg.set_content(content)
    msg['From']=myemail
    msg['to']=to
    if bcc:
        msg['Bcc'] = myemail
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(myemail, myemailkey) 
        server.send_message(msg)
        return True
def returnnondisableduserobj(userid):
    obj=currentdb.query(users).filter(
        users.permanentdisabled == False,           
        users.id == userid,       
    ).first()
    return obj or None    
def nomraluserexistancheck(userid):
    return users.query.options(joinedload(users.channel)).get(userid)   
def returnallchannelsofuser(userid):
    obj =(
    currentdb.query(
        channels,
        channels.sub_count.label('subs'), 
        func.count(distinct(videos.id)).label('video_count') 
    )
    .join(users, channels.user_id == users.id) 
    .outerjoin(videos, channels.id == videos.channel_id) 
    .filter(
        channels.user_id == userid,
        users.permanentdisabled == False
    )
    .group_by(channels.id, users.id) 
    .options(
        contains_eager(channels.owner)
    )
    .limit(maxchannels)
    .all()
)
    return obj
def getsinglechannelobjbyid(id):
    obj=(
    currentdb.query(channels)
    .join(users, channels.user_id == users.id)
    .options(
        contains_eager(channels.owner)
    )
    .filter(
        channels.id == id,
        users.permanentdisabled == False
    )
    .first()
)
    return obj
def getuserobjbyemail(emialid):
    obj=users.query.filter_by(email=emialid,permanentdisabled=False).first()
    return obj
def getuserobj(userid):
    obj=(
    currentdb.query(users)
    .options(
        joinedload(users.channel),
    )
    .filter(
        users.permanentdisabled == False,
        users.id == userid
    )
    .first()
)
    return obj 
def checkifuserexists(userid):
    obj=getuserobj(userid)
    if obj:return obj
    return False            
def loggedin(show=False):
    y=nomraluserexistancheck(session.get('user_id'))
    obj=y
    tok=session.get('token')
    if session.get('login') and obj and obj.token==tok:
        return True
    elif session.get('login') and obj and obj.token!=tok:
        d=session.get('user_id')
        delsession()
        if show:
            flash('you have logged in elsewhere' ,error)
        socketio.emit('force_logout', to=f"user_{d}")
        socketio.sleep(0.1)             
    elif session.get('login') and y and y.permanentdisabled:
        d=session.get('user_id')
        delsession()
        if show:
            flash("Your account has been terminated" , error)
        socketio.emit('force_logout', to=f"user_{d}")
        socketio.sleep(0.1) 
    elif session.get('login') and not y :
        d=session.get('user_id')
        delsession()
        if show: 
            flash("Your account has been terminated" , error)        
        socketio.emit('force_logout', to=f"user_{d}")
        socketio.sleep(0.1) 

    g.user=None
    return False
def getallsubscribersofachannel(channelid):
    obj=(
    currentdb.query(channels.sub_count)
    .filter(channels.id == channelid)
    .scalar() 
)
    return obj
def getallvideosofachannel(channelid,offset):
    video_count = (
        currentdb.query(func.count(videos.id))
        .filter(videos.channel_id == channelid)
        .scalar() or 0
    )
    vd_results = (
        currentdb.query(
            videos.view_count.label('view_count'),
            videos.like_count.label('like_count'),
            videos
        )
        .join(channels, videos.channel_id == channels.id)
        .join(users, channels.user_id == users.id)
        .filter(videos.channel_id == channelid)
        .group_by(videos.id, channels.id, users.id) 
        .order_by(videos.created.desc())
        .offset(offset)
        .limit(maxvideoperpage + 1)
        .options(
            contains_eager(videos.parent_channel)
            .contains_eager(channels.owner)
        )
        .all()
    )

    return (video_count, list(vd_results))
def checkifsubscribed(userid,channelid):
    tru=currentdb.query(
                            subscribers.query.filter_by(
                                user_id=userid , 
                                channel_id=channelid
                            ).exists()
                        ).scalar() 
    return tru
def checkiflikedvideo(userid,videoid):
    li=currentdb.query(
                            likes.query.filter_by(
                                user_id=userid , 
                                video_id=videoid
                            ).exists()
                        ).scalar()
    return li
def getsubscribedobj(userid,channelid):
    obj=subscribers.query.filter_by(user_id=userid, channel_id=channelid).first()
    return obj

def getvideobyid(videoid):
    return (videos.query
            .join(videos.parent_channel) 
            .join(channels.owner) 
            .options(contains_eager(videos.parent_channel).contains_eager(channels.owner))
            .filter(videos.id == videoid, users.permanentdisabled == False)
            .first())
def getplaylistobj(playlistid):
    obj=(
    currentdb.query(playlists)
    .join(users, playlists.user_id == users.id)
    .options(
        contains_eager(playlists.owner)
    )
    .filter(
        playlists.id == playlistid,
        users.permanentdisabled == False
    )
    .first()
)
    return obj
def getallplaylistobject(userid,offset_val,l=maxplaylistsperpage+1):
    objs=(
    currentdb.query(playlists)
    .join(users, playlists.user_id == users.id)
    .options(
        contains_eager(playlists.owner)
    )
    .filter(
        playlists.user_id == userid,
        users.permanentdisabled == False
    ).order_by(playlists.created.desc()).offset(offset_val).limit(l)
    .all()
)
    return objs
def delsession():
        if session.get('temp'):del session['temp']
        if session.get('token'):del session['token'] 
        if session.get('login'):del session['login'] 
        if session.get('user_id'):del session['user_id']
        if session.get('photo'):del session['photo']
        session.modified = True    
def mainlogin(id,f=None):
    obj=getuserobj(id) if not f else f
    if obj:
        if session.get('temp'):del session['temp']
        session['token']=obj.token if obj else None
        session['login'] = True if obj else None
        session['user_id']=obj.id if obj else None
        session['photo']=getpath(obj.profilephoto) if obj else None
        try:
            session.modified = True
        except Exception:
            flash("System error",error)    
    else:
        flash("Error logging in", error)
def processavedemails():
    raw_emails = session.get('remembered_emails', [])
    valid_users = users.query.filter(users.email.in_(raw_emails)).filter(users.permanentdisabled==False).all()
    valid_emails = [u.email for u in valid_users]
    if len(valid_emails) != len(raw_emails):
            flash(f"{len(raw_emails)-len(valid_emails)} emails have been removed!",info)
            session['remembered_emails'] = valid_emails
            session.modified = True  
def cleanup_allfiles():
    with system.app_context(): 
        allabnnerfiles=get_all_files(bannerpath)
        allicons=get_all_files(folderpath)
        allthumbnails=get_all_files(thumbnailspath) 
        allvideos=get_all_files(videospath)
        allvtt=get_all_files(vttfolderpath)
        allfolderpathfilesindb=currentdb.scalars(db.select(users.profilephoto)).all()+currentdb.scalars(db.select(channels.channelicon)).all() 
        allbannerpathfileindb=currentdb.scalars(db.select(channels.channelbanner)).all()+currentdb.scalars(db.select(playlists.thumbnail)).all()
        allvideopathfileindb=currentdb.scalars(db.select(videos.file)).all()
        allthumbnailspathindb=currentdb.scalars(db.select(videos.thumbnail)).all()
        rfile=0
        for x in allicons:
            if x not in allfolderpathfilesindb:
                log_event('Invalid file' ,"in folderpath(icons and profilephotos)" )
                rfile+=1
                removefiles(x,folderpath)
        for x in allabnnerfiles:
            if x not in allbannerpathfileindb:
                log_event('Invalid file' ,"in bannerpath(channelabnner and playlist thumbnail)" )
                rfile+=1
                removefiles(x,bannerpath)
        for x in allthumbnails:
            if x not in allthumbnailspathindb:
                log_event('Invalid file' ,"in thumbanilspath" )
                rfile+=1
                removefiles(x,thumbnailspath)
        for x in allvideos:
            if x not in allvideopathfileindb:
                log_event('Invalid file' ,"in videospath" )
                rfile+=1
                removefiles(x,videospath)
        for x in allvtt:
            if os.path.splitext(x)[0] not in allvideopathfileindb:
                rfile+=1
                log_event('Invalid file' ,"in vttpath" )
                removefiles(x,vttfolderpath)
        log_event("FILES REMOVED",f"{rfile}(s) removed form system ")
        print(f"{rfile}(s) removed form system ")                                
def deluserdata(userobj):
    folder_paths = []   
    banner_paths = []    
    thumbnail_paths = []  
    video_paths = []
    vtt_paths=[]     
    if not userobj.id:return
    if userobj.profilephoto:
        folder_paths.append(userobj.profilephoto)
    user_channels = channels.query.filter_by(user_id=userobj.id).all()
    for channel in user_channels:
        if channel.channelicon: folder_paths.append(channel.channelicon)
        if channel.channelbanner: banner_paths.append(channel.channelbanner)
        for video in channel.videos:
            p=video.file
            if video.file: video_paths.append(p)
            if video.thumbnail: thumbnail_paths.append(video.thumbnail)
            if cachedvid.get(str(video.id)):del cachedvid[(str(video.id))]
            vtt_paths.append(f"{p}.vtt")
    for playlist in userobj.playlists:
     
        if playlist.thumbnail: banner_paths.append(playlist.thumbnail)
    try:
        currentdb.delete(userobj)
        currentdb.commit()
        for x in folder_paths:
            removefiles(x,folderpath)
        for x in banner_paths:
            removefiles(x,bannerpath)
        for x in thumbnail_paths:
            removefiles(x,thumbnailspath)
        for x in video_paths:
            removefiles(x,videospath)
        for x in vtt_paths:
            removefiles(x,vttfolderpath)
        return True
    except Exception as e:
        currentdb.rollback()    
        flash(f"Error :{e}")
        return False        
def addnotification(userid,content,title="Account update"):
    obj=getuserobj(userid)
    if not obj:return False
    n = notifications(created=datetime.now(),content=content,user_id=userid,title=title)
    try:
        currentdb.add(n)
        obj.nread=False
        currentdb.commit()
    except Exception as e:
        currentdb.rollback()
        flash(f"Error occured: {e}" ,error)
def processlogin(bool=True):
        if loggedin(True if bool else None):
            x=session.get('user_id') 
            delsession()
            t=getuserobj(x) 
            mainlogin(x,t)
            g.user=t
        g.appname=appname
def emailadder(email):
    if not session.get("remembered_emails"):session["remembered_emails"]=[]
    if email not in session['remembered_emails']:
        if len(session['remembered_emails']) >= 10:
            session['remembered_emails'].pop(0) 
        session['remembered_emails'].append(email)
        session.modified = True
    processavedemails()
def filtertime(value):
    vidtime = str(timedelta(seconds=int(value)))
    return vidtime
def format_compact(value):
    try:
        value = int(value)
        if value >= 1000000:
            return f"{value / 1000000:.1f}M".replace('.0', '')
        if value >= 1000:
            return f"{value / 1000:.1f}k".replace('.0', '')
        return str(value)
    except (ValueError, TypeError):
        return "0"
def cleansafe(value):
    if not isinstance(value, str):
        return value
    cleaned = nh3.clean(
        value, 
        tags={"b", "i", "strong", "em", "br", "a", "u", "p"}, 
        attributes={
            "a": {"href", "title", "target", "rel"}, 
            "*": {"class"} 
        },
        url_schemes={"http", "https", "mailto"}, 
        link_rel=None
    )
    return Markup(cleaned)

system.jinja_env.filters['cleansafe'] = cleansafe
system.jinja_env.filters['compact'] = format_compact
system.jinja_env.filters['filtertime'] = filtertime
def cleanup_expired_keys():
    with system.app_context(): 
        now = datetime.now()
        expired_keys = keys.query.filter(keys.exp_time < now).all()
        if expired_keys:
            for key in expired_keys:
                db.session.delete(key)
            db.session.commit()
            print(f"[{datetime.now()}] Deleted {len(expired_keys)} expired keys.")        
def log_event(event_type, details):
    with open("log.txt", "a") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {event_type} - {details}\n")
def is_ip_banned(ip):
    try:
        with open("blacklist.txt", "r") as f:
            banned_ips = f.read().splitlines()
        return ip in banned_ips
    except FileNotFoundError:
        return False
def logoffadmin():
    if session.get('admin_logged_in'):del session['admin_logged_in'] 
    if session.get("admin_email"):del session['admin_email'] 
    if session.get("admintoken"):del session['admintoken']     
def ban_ip(ip):
    if not is_ip_banned(ip):
        with open("blacklist.txt", "a") as f:
            f.write(f"{ip}\n")
        log_event("PERMANENT_BAN", f"IP {ip} added to blacklist")        
def is_video_valid(file_path):
    try:
        cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", file_path
        ]
        output = subprocess.check_output(cmd).decode('utf-8').strip()
        duration = float(output)
        return duration >= 1.0
    except Exception as e:
        print(f"Error checking video: {e}")
        return False
def validatechannel(base_fx):
    @wraps(base_fx)
    def ecnhancefunc(*a,**b):
        if not getsinglechannelobjbyid(b.get('id')):
            flash("Channel not found")
            return redirect(url_for('index'))
        return base_fx(*a,**b)
    return ecnhancefunc    
def validatevideo(base_fx):
    @wraps(base_fx)
    def efunc(*a,**b):
        if not getvideobyid(b.get('id')):
            flash("Video not found",error)
            return redirect(url_for('index'))
        return base_fx(*a,**b)
    return efunc

def validatevideononowner(base_fx):
    @wraps(base_fx)
    def efunc(*a,**b):
        x=getvideobyid(b.get('id'))
        if not x or not x.parent_channel.ischannelenabled or not x.display:
            flash("Video not found",error)
            return redirect(url_for('index'))
        return base_fx(*a,**b)
    return efunc

def admin_only(basefx):
    @wraps(basefx)
    def enchancedfuic(*a,**b):
        if not session.get('admin_logged_in') or not session.get('admin_email') or not session.get('admintoken'):
                flash("Not logged in",error)
                return redirect(url_for('adminbp.adminlogin'))
        if not admin_users.query.filter_by(email=session.get('admin_email')).first().token==session.get('admintoken'):
            flash("You have logged in elsewhere!",error)
            logoffadmin()
            return redirect(url_for('adminbp.adminlogin'))
        return basefx(*a,**b)
    return enchancedfuic    
def dontallowiflogged(base_fx):
    @wraps(base_fx)
    def e(*a,**b):
        if session.get('user_id'):
            
            return redirect(url_for('index'))
        return base_fx(*a,**b)    
    return e            
def requireduserlogin(base_fx):
    @wraps(base_fx)
    def echancedbase(*args,**kwargs):
        if not session.get('user_id'):
            return redirect(url_for('authbp.login'))
        
        return base_fx(*args,**kwargs)
    return echancedbase            
def global_rate_limit_key():
    return session.get("user_id") or get_remote_address()
limiter = Limiter(
    global_rate_limit_key, 
    app=system,enabled=os.getenv("STRESS_TEST") != "true",
    default_limits=["2000 per day","40 per minute"], 
    storage_uri=storage,
    strategy="fixed-window"
)
def syncviews(videobj):
        viewno = (
    currentdb.query(func.count(1))
    .filter(views.video_id == videobj.id)
    .scalar()
)
        if not videobj.view_count==viewno:
                videobj.view_count = viewno
                try:
                    currentdb.commit()
                except Exception as e:
                    currentdb.rollback()
                    print("something went worn uring sync")
def synclikes(videobj):
        actual_likes = (
    currentdb.query(func.count(1))
    .filter(
        likes.video_id == videobj.id,
        exists().where(
            (users.id == likes.user_id) & 
            (users.permanentdisabled == False)
        )
    )
    .scalar()
)   
        if not videobj.like_count==actual_likes:
                videobj.like_count = actual_likes
                try:
                    currentdb.commit()
                    print("likes updated")
                except Exception as e:
                    currentdb.rollback()
                    print("something went worn uring sync")
def syncsubs(channelobj):
    print("synscing usbs")
    actual_subs =(
    currentdb.query(func.count(1)) 
    .filter(
        subscribers.channel_id == channelobj.id,
        exists()
        .where(users.id == subscribers.user_id)
        .where(users.permanentdisabled == False)
    )
    .scalar()
)

    if not channelobj.sub_count == actual_subs:
                channelobj.sub_count = actual_subs
                try:
                    currentdb.commit()
                    print("subs updated")
                except Exception as e:
                    currentdb.rollback()
                    print("something went worn uring sync")
def sync_counts():
    with system.app_context():
        all_videos = videos.query.all()
        for video in all_videos:
            actual_likes = (
    currentdb.query(func.count(1))
    .filter(
        likes.video_id == video.id,
        exists().where(
            (users.id == likes.user_id) & 
            (users.permanentdisabled == False)
        )
    )
    .scalar()
)
            viewss =(
    currentdb.query(func.count(1))
    .filter(views.video_id == video.id)
    .scalar()
)          
            if not video.like_count == actual_likes or not videos.view_count==viewss:
                video.like_count = actual_likes
                video.view_count = viewss
                log_event("SYNC WARNING",f"Updated Video {video.id}: {actual_likes} likes")
        all_channels = channels.query.all()
        for channel in all_channels:
            actual_subs = (currentdb.query(func.count(subscribers.id))
                          .join(users, subscribers.user_id == users.id)
                          .filter(subscribers.channel_id == channel.id, users.permanentdisabled == False)
                          .scalar())
            if not channel.sub_count == actual_subs:
                channel.sub_count = actual_subs
                log_event("SYNC WARNING",f"Updated channel {channel.id}: {actual_subs} susbcribers")
        try:
            currentdb.commit()
            print("Sync Complete")
        except Exception as e:
            currentdb.rollback()
            log_event("Sync error",f"Somethign wne wotrng duriong update {e}")    
   
def check_resources(threshold, cache_seconds=2):
    global last_check_time, cached_result
    current_time = time.time()
    if current_time - last_check_time < cache_seconds:
        return cached_result
    cpu = psutil.cpu_percent(interval=None) 
    ram = psutil.virtual_memory().percent
    result = True
    if cpu > threshold or ram > threshold:
        result = False
    else:
        try:
            gpus = GPUtil.getGPUs()
            for gpu in gpus:
                if (gpu.memoryUtil * 100) > threshold:
                    result = False
        
                    break
        except Exception:
            log_event("GPU CHECK ERROR",time.time())
            pass 
    last_check_time = current_time
    cached_result = result
    return result
def is_ollama_online():
    try:
        client.list()  
        # if not check_resources(99.0):
        #     return False
        return True
    except Exception as e:
        return False            
def is_email(s):
    try:
        validate_email(s)
        return True
    except EmailNotValidError:
        return False