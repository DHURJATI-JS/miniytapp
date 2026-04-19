from algorithm import *
from blueprints import app_blueprints
from system import *
from groupedvid import *
for x in app_blueprints:
    system.register_blueprint(x)
db.init_app(system)
migrate = Migrate(system, db)
scheduler = APScheduler()

@system.before_request
def debug_blueprint():
    if request.endpoint == 'static' or request.path.startswith('/static'):
        return
    if request.endpoint:
        print(f"--- ACTIVE BLUEPRINT/ROUTE: {request.endpoint} ---")
@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    stack = traceback.extract_stack()
    for frame in reversed(stack):
        if "site-packages" not in frame.filename and "yt app" in frame.filename:
            # print(f" QUERY AT: {os.path.basename(frame.filename)} | LINE: {frame.lineno} | FUNC: {frame.name}")
            print(f"Executing SQL: {statement[:100]}...") # Print the start of the SQL
            break
@event.listens_for(db.session, 'before_flush')
def strict_manual_eject_guard(db_session, flush_context, instances):
    if not has_request_context():
        return
    allowed_bps = ['authbp', 'adminbp']
    allowed_endpoints = ['videobp.delviewhistory', 'videobp.addviews', 'static','videobp.viewvid']
    
    if request.blueprint in allowed_bps or request.endpoint in allowed_endpoints:
        return
    user_id = session.get('user_id')
    user_token = session.get('token')
    conn = db_session.connection()
    query = text("""
        SELECT 1 FROM users 
        WHERE id = :uid AND token = :token AND permanentdisabled = :ds 
        LIMIT 1
    """)
    result = conn.execute(query, {
        "uid": user_id, 
        "token": user_token, 
        "ds": False
    }).fetchone()
    if not result or not getattr(g, 'user', None):
        db_session.expunge_all()
        raise Unauthorized("Undoing changes...")

@system.teardown_request
def teardown_request(exception=None):
    if exception:
        currentdb.rollback()
    currentdb.remove()
@system.before_request
def block_banned_ips():
    if request.path.startswith('/static') or request.endpoint == 'static':
            return 
    user_ip = request.remote_addr
    if is_ip_banned(user_ip):
        if request.path != url_for('bannedip') and not request.path.startswith('/static'):
            return redirect(url_for('bannedip'))
@limiter.request_filter
def is_admin():
    if request.endpoint == 'static' or request.path.startswith('/static'):
        return
    if has_request_context() :
            return (session.get('admin_logged_in') == True)or not productionmode
    return False
@system.before_request
def load_global_data():
    if request.path.startswith('/static') or request.endpoint == 'static':
        return     
    processlogin(True)
@system.before_request
def limit_file_types():
    if request.endpoint == 'static' or request.path.startswith('/static'):
        return
    if request.method == 'POST' and request.files:
        allowed = system.config['ALLOWED_IMAGE_EXTENSIONS'].union(system.config['ALLOWED_VIDEO_EXTENSIONS'])
        for z in request.files:
            file = request.files[z]
            if file and file.filename:
                ext = file.filename.rsplit('.', 1)[-1].lower()
                if ext not in allowed:
                    flash("Invalid file type uploaded",error)
                    return redirect(request.referrer or url_for('index'))
@system.before_request
def checkifloggedinelsewhere():
    if request.path.startswith('/static') or request.endpoint == 'static':
        return 
    g.appname=appname
    g.bcategory=category
    g.myemail=myemail
    if request.endpoint=='videobp.viewvid' or request.endpoint=='videobp.editvid':
        if is_ollama_online():
            g.ai=True
        else:
            g.ai=False
@system.context_processor
def injectn():
    if request.endpoint == 'static' or request.path.startswith('/static'):
        return {}
    g.tpath=os.path.join('static',thumbnailfolder)
    g.vpath=os.path.join('static',videofolder)
    g.logopath=os.path.join('static',photos)
    g.ailimit=maxaiprompts
    if session.get("login"):
        userid=session.get('user_id')
        notifs = (
    notifications.query
    .filter_by(user_id=userid)
    .options(
        undefer(notifications.title),
        undefer(notifications.content),
        undefer(notifications.created),
        load_only(notifications.title, notifications.content, notifications.created)
    )
    .order_by(notifications.created.desc())
    .limit(maxnotifications)
    .all()
)       
        return dict(notifs=notifs)
    return dict(notifs=[])
@system.after_request
def add_security_headers(response):
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    session.modified = True
    return response
@system.route('/community')
def viewcommunity():
    
    page = request.args.get('page', 1, type=int)
    query = request.args.get('q', '')
    cat_filter = request.args.get('cat', '')
    ai = request.args.get('sort', '')
    offset_val = (page - 1) * maxchannelsperpage
    userid=session.get("user_id")
    all_channels = (
    currentdb.query(
        channels.sub_count.label('sub_count'), 
        channels,
        func.count(distinct(videos.id)).label('video_count') 
    )
    .join(users, channels.user_id == users.id)
    .outerjoin(videos, channels.id == videos.channel_id) 
    .filter(
     channels.user_id != userid,
        channels.ischannelenabled == True,
        users.permanentdisabled == False
    )
    .group_by(channels.id, users.id)
)
    dis=False
    has_next=False    
    if cat_filter or query:
        if cat_filter:
            all_channels = all_channels.filter(videos.category == cat_filter)
        if query:
            all_channels = all_channels.filter(channels.channelname.ilike(f"%{query}%"))
        results= (
        all_channels.options(contains_eager(channels.owner),
                             selectinload(channels.videos))
        .order_by(
        desc('sub_count'),      
        desc('video_count'),
        channels.created.desc(),
)
        .offset(offset_val)
        .limit(maxchannelsperpage + 1)
        .all()
    )
        if not results:
            flash("No channels found",error)
    elif ai and getattr(g, 'user', None) and g.user.viewduration and g.user.userclicks:
        ai='ai'
        flash("Personalized sorting",info)
        results = generateuserprefferedcategoryvids(session.get('user_id'),offset_val,True)
        if not results:
            flash("No channels found",error)
            dis=True
    elif ai and getattr(g, 'user', None) and not g.user.viewduration and not g.user.userclicks:return redirect(url_for('viewcommunity'))
    elif ai and not getattr(g, 'user', None):return redirect(url_for('viewcommunity'))
    else:
        results = (
        all_channels.options(contains_eager(channels.owner),selectinload(channels.videos))
.order_by(
        desc('sub_count'),      
        desc('video_count') ,
        channels.created.desc(),
    )        .offset(offset_val)
        .limit(maxchannelsperpage + 1)
        .all()
    )
        if not results:
            flash("No channels found",error)
            dis=True
    if len(results) > maxchannelsperpage:
        results.pop()
        has_next=True  
    print(len(results),page,has_next)        
    return render_template('community.html', channels=results, query=query, active_cat=cat_filter,category_list=category,page=page,per_page=maxchannelsperpage,has_next=has_next,dis=dis,sort=ai)
@system.route('/nread>',methods=["POST"])
def nread():
    if getattr(g, 'user', None):
        g.user.nread=True
        try:
            currentdb.commit()
        except Exception as e:
            currentdb.rollback()
            flash(f"Error: {e}",error)    
        return {"status": True}, 200
    return {"status": False}, 403
@system.route('/fetch-channel/' , methods=["POST"])
def fetchchannel():
    data = request.get_json()
    if not data or 'ids' not in data:
        return jsonify({"status": False}),403
    print(data)
    num=[int(channel_id.strip()) for channel_id in data['ids'].split() if channel_id.strip()]
    cou = channels.query.join(users).filter(
    channels.id.in_(num),
    channels.ischannelenabled == True,
    users.permanentdisabled == False  
).count()
    if cou==len(num):
        return jsonify({"status": True}),200
    return jsonify({"status": False}),403
def gennvids(offset_val):
    base_videos =(
    currentdb.query(
        videos.view_count,
        videos.like_count, 
        videos
    )
    .join(videos.parent_channel)
    .join(channels.owner)
    
    
    .filter(
        videos.display == True,            
        channels.ischannelenabled == True,         
        users.permanentdisabled == False    
    )
    .group_by(videos.id, channels.id, users.id) 
    .order_by(
        videos.like_count.desc(), 
        videos.view_count.desc(), 
        videos.created.desc()
    )
    .limit(maxvideoperpage+1)
    .offset(offset_val)
    
    .options(
        contains_eager(videos.parent_channel)
        .contains_eager(channels.owner)
    )
    .all()
)
    return base_videos
@system.route('/' ,methods=["POST" ,"GET"])
def index():
    page = request.args.get('page', request.form.get('page', 1, type=int), type=int)
    offset_val = (page - 1) * maxvideoperpage
    vids=None     
    onlyquery=False
    grpdata=None    
    g.tpath=os.path.join('static',thumbnailfolder)
    if request.method=="POST":
        video_title = request.form.get('query').strip() if request.form.get('query')  else None
        channel_ids = request.form.get('channel_ids').strip() if request.form.get('channel_ids') else  None
        sort_by = request.form.get('sort_by')
        ordered = request.form.get('order')
        vcategory = request.form.get('category').lower().strip()
        onlywatchedvideos=request.form.get('watchedvidesonly')
        onlyquery=request.form.get('onlyquery',False)
        num=[int(channel_id.strip()) for channel_id in channel_ids.split() if channel_id.strip() ]if channel_ids else []
        cou = (
    currentdb.query(channels)
    .join(users, channels.user_id == users.id)
    .filter(
        channels.id.in_(num),
        channels.ischannelenabled == True,
        users.permanentdisabled == False  
    )
    .count()
)
        if cou!=len(num):
            flash("Invalid id(s)" , error)
            return redirect(url_for('index'))    
        query = currentdb.query(videos).join(
    channels, videos.channel_id == channels.id
).join(
    users, channels.user_id == users.id
)
        query = query.filter(users.permanentdisabled == False,channels.ischannelenabled == True)
        conditions = []
        if num and not onlyquery:
            conditions.append(videos.channel_id.in_(num))
        numd=" ".join([str(x) for x in num])
        g.dataobj = SimpleNamespace(
                video_title=video_title or None,
                channel_ids=numd or None,
                sort=sort_by or None,
                order=ordered or None,
                category=vcategory or None,
                onlywatchedvideos=onlywatchedvideos or None
            ) 
        
        userid=session.get('user_id') or session.get('temptoken')
        query = (
    currentdb.query(
        videos.view_count, 
        videos.like_count, 
        videos             
    )
    .join(channels, videos.channel_id == channels.id)
    .join(users, channels.user_id == users.id)
    .filter(
        users.permanentdisabled == False,
        channels.ischannelenabled == True,
        videos.display == True
    )
)
        if g.dataobj and g.dataobj.onlywatchedvideos and not onlyquery:
            query = query.join(views, videos.id == views.video_id).filter(views.token == str(userid),views.show==True)
        if conditions and not onlyquery:
            query = query.filter(or_(*conditions))
        if video_title:
            query = query.filter(videos.name.ilike(f"%{video_title}%"))
        if vcategory and vcategory != "all" and not onlyquery:
            query = query.filter(videos.category.ilike(f"%{vcategory}%"))
        if sort_by in ['likes', 'views'] and not onlyquery:
            query = query.options(contains_eager(videos.parent_channel).contains_eager(channels.owner))
            sort_target = videos.like_count if sort_by == 'likes' else videos.view_count
        else:
            if not hasattr(videos, str(sort_by)):
                return redirect(url_for('index')) 
            query = query.outerjoin(likes, videos.id == likes.video_id)
            query = query.outerjoin(views, videos.id == views.video_id)
            query = query.group_by(videos.id, channels.id, users.id)
            sort_target = getattr(videos, sort_by) 

        direction = desc if ordered == 'desc' else asc
        vids = (
    query.options(
        contains_eager(videos.parent_channel)
                .contains_eager(channels.owner)
            )
            .order_by(direction(sort_target) if not onlyquery else videos.like_count.desc(),videos.view_count.desc())
        .limit(maxvideoperpage + 1)
    .offset(offset_val)
             .all()
        )
        has_next = False
        if len(vids) > maxvideoperpage:
            has_next = True
            vids.pop()    
        if onlyquery:
            grpdata=grpvids(vids)

        flash("Filtering using criteria...",info) if not onlyquery else None
    else:
        if getattr(g, 'user', None):
            vids=None
            vids=generateuserprefferedcategoryvids(session.get('user_id'),offset_val)
            if not vids:
                vids= gennvids(offset_val)
            if not g.user.collect_data:
                flash("Enable data collection to improve feed",info)
            has_next = False
            if len(vids) > maxvideoperpage:
                has_next = True
                vids.pop()
        else:            
            vids=gennvids(offset_val)
            has_next = False
            if len(vids) > maxvideoperpage:
                has_next = True
                vids.pop()       
    return render_template('index.html',onlyquery=onlyquery,grpdata=grpdata,mostsearched=mostsearched,vids=vids,page=page,per_page=maxvideoperpage,has_next=has_next)
@system.route('/profile/<int:userid>')
def viewprofile(userid):
    userobj=getuserobj(userid)
    if not userobj:
        flash("User not found",error)
        return redirect(url_for('index'))
    return render_template('profile.html',user=userobj,channels=returnallchannelsofuser(userid))
@system.route('/decleration')
def declaration():
    return render_template('declaration.html')
@system.errorhandler(404)
@limiter.limit("10 per minute")
def page_not_found(e):
    log_event("URL WARNING", f"IP: {request.remote_addr} WRONG ADDRESS ,USER_ID: {session.get('user_id') or None}")
    return render_template('404.html'), 404  
@system.errorhandler(RateLimitExceeded)
def ratelimit_handler(e):
    if limiter.current_limit:
        retry_after = int(limiter.current_limit.reset_at - time.time())
    print(retry_after)    
    log_event("SPAM WARNING", f"IP: {request.remote_addr} acting suspicously ,USER_ID: {session.get('user_id') or None}")
    return render_template('cooldown.html',reason=e.description, retry_after=retry_after), 429 
@system.errorhandler(CSRFError)
@limiter.limit("5 per minute")
def handle_csrf_error(e):
    
    log_event("IDLE WARNING", f"IP: {request.remote_addr} CSRF TOKEN EXPIRED ,USER_ID: {session.get('user_id') or None}")
    flash("Your session was timed out for security. Please try again.", info)
    return redirect(request.referrer or url_for('index'))
@system.route('/bannedip')
def bannedip():
    userip=request.remote_addr
    if is_ip_banned(userip):
        if session.get('login'):delsession()
        return render_template('bannedip.html',myemail=myemail),403
    else:
        flash("You are'nt banned",error)
        return redirect(request.referrer or url_for('index'))  
@system.errorhandler(413)
def request_entity_too_large(error):
    currentdb.rollback()
    flash("File size exceeded the limit given",error)    
    log_event("FILE SIZE" ,f"{request.remote_addr} sent a big file at the server")
    return redirect(request.referrer or url_for('index'))
@system.errorhandler(405)
def method_not_allowed(e):
    flash('This action is not allowed.', error)
    return redirect( request.referrer or url_for('index')), 405
@system.errorhandler(Exception)
def internal_error(e):
    currentdb.rollback() 
    if isinstance(e, UndefinedError):
        raise e
    if isinstance(e, HTTPException):
        return e
    log_event("Fatal Error",f"Error {e}")
    return render_template("500.html"),500
@system.errorhandler(UndefinedError)
def handle_jinja_error(e):
    log_event("Jinja varaible error",f"Error {e}")
    flash("Something went wrong", error)
    return redirect(request.referrer or url_for('index'))
@system.errorhandler(Unauthorized) 
def handle_unauthorized(e):
    currentdb.rollback()
    delsession()
    flash("Undoing changes....", error)
    return redirect(url_for('authbp.login',_external=True), code=303)
@system.route('/cancel-task', methods=['POST'])
def cancel():
    user_id = session.get('user_id', 'NONE')
    if user_id in active_tasks:
        del active_tasks[user_id]   
    return "Done"
if __name__=="__main__":
    with system.app_context():
        scheduler.add_job(id='Clean', func=cleanup_expired_keys, trigger='interval', seconds=3600, max_instances=1, coalesce=True)
        scheduler.add_job(id='cleanfiles', func=cleanup_allfiles, trigger='interval', seconds=3600, max_instances=1, coalesce=True)
        scheduler.add_job(id="syncowrkforai", func=sync_counts, trigger="interval", minutes=10, max_instances=1, coalesce=True)
        scheduler.add_job(id="clearveything", func=clear_all_data, trigger="interval", minutes=1440,  max_instances=1,coalesce=True)
        scheduler.add_job(id="updaterecommendation" ,func=updaterec,trigger="interval", minutes=30,  max_instances=1,coalesce=True)
        scheduler.init_app(system)
        threading.Thread(target=auto_purge_scheduler, daemon=True).start()        
        scheduler.start()
        acchats.clear()
        
        # db.drop_all()
        # db.create_all() 
        x=admin_users.query.filter_by(email=myemail).first()
        if not x:
            new_admin = admin_users(
                email=myemail,
                password=generate_password_hash(defaultadminpassword),
                token=str(uuid.uuid4())
            )
            try:
                currentdb.add(new_admin)
                currentdb.commit()
            except Exception as e:
                currentdb.rollback()
                print(f"Error :{e}")    
    system.run(host='0.0.0.0', port=5000,debug=not productionmode)
    socketio.run(system, port=5000,debug=not productionmode)
