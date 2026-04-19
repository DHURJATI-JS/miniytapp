from flask import Blueprint, render_template
from imports import *
from ai import *
from algorithm import *
videobp = Blueprint('videobp', __name__)
sumgenerr=" <strong> Summary generation was interupted...</strong>"
generr=" <strong> AI generation was interupted...</strong>"
def execute_imrovement_task(reqid,vid,itime):
    if (time.time() - itime > 60) or reqid in alrimproved or not is_ollama_online():
            emit("chat_chunk", {
                "text": "Something went wrong Kindly <a href='?reload=true'>refresh</a> the page",
                "done": True
            },to=reqid)
            return False
    with system.app_context():
        try:
            for bits in get_ai_improvements(getvideobyid(vid)):
                if reqid not in alrimproved:alrimproved[reqid]=True
                if reqid not in request_count or not is_ollama_online():
                        eventlet.sleep(1)
                        emit("chat_chunk", 
                {"text":generr,"done":True}
                    ,to=reqid)
                        return False
                if not bits['done'] :
                    word = bits['response']
                    socketio.sleep(0.01)
                    socketio.emit("chat_chunk", {
                        "text": str(word)
                    },to=reqid)
                else:
                    socketio.emit("chat_chunk", {
                        "done": True
                    },to=reqid)
                    break
        except Exception as e:
                eventlet.sleep(1)
                emit("chat_chunk", 
                {"text":generr,"done":True}
                ,to=reqid)
                return False      
def exe_ai_sum(vidid, itime, aitoken, user_id,videdit=True):
    user_key = str(user_id)
    # print("porocesing usmaryr ge ratuon")
    def is_valid_task():
        try:
            raw_data = active_tasks.get(user_key)
            if not raw_data:
                # print("nodat fouind")
                return False
            if hasattr(raw_data, 'decode'):
                raw_data = raw_data.decode('utf-8')
            data = json.loads(raw_data)
            return str(data[0]) == str(aitoken) and data[1] is True
        except Exception:
            return False
    def cleanup():
        try:
            if user_key in active_tasks:
                del active_tasks[user_key]
        except Exception:
            pass
    if (time.time() - itime > 60) or not is_ollama_online() or not is_valid_task():
        cleanup()
        eventlet.sleep(1)
        return ""
    content = ""
    start_run = time.time()
    try:
        with system.app_context():
            video_obj = getvideobyid(vidid)
            for bits in get_ai_summary(video_obj,videdit):
                if (time.time() - start_run > 60) or not is_ollama_online() or not is_valid_task():
                    cleanup()
                    eventlet.sleep(1)
                    # print("proccesing ollama")
                    return (content + f"{sumgenerr}") if content else ""
                if not bits['done']:
                    content += bits['response'].replace('"', "'").replace("`", "'")
                else:
                    break
            cleanup()
            return content
    except Exception:
        cleanup()
        eventlet.sleep(1)
        return (content + f"{sumgenerr}") if content else ""
def execute_chat_task(sid,vid,oldprompt,prompt,lastprompt,itime):
    if (time.time() - itime > 60) or not is_ollama_online():
            emit("limit_reached", 
             {"msg":"Something went wrong Kindly <a href='?reload=true'>refresh</a> the page"}
            ,to=sid)
            return False    
    with system.app_context():
        try:
            for bits in ai_chat(oldprompt,getvideobyid(vid),prompt,lastprompt):
                if sid not in request_count or not is_ollama_online() or not request_count.get(sid,0) <maxaiprompts:
                        if acchats.get(sid):del acchats[sid]    
                        eventlet.sleep(1)
                        socketio.emit("chat_chunk", {
                        "text": generr,
                        "done":True
                    },to=sid,)
                        return False        
                if not bits['done'] :
                    word = bits['response']
                    socketio.sleep(0.01)
                    socketio.emit("chat_chunk", {
                        "text": str(word)
                    },to=sid)
                else:
                    socketio.emit("chat_chunk", {
                        "done": True
                    },to=sid)
                    if acchats.get(sid):del acchats[sid]    
                    break
        except Exception as e:
            if acchats.get(sid): del acchats[sid]
            log_event(f"AI Stream Crash: {e}",time.time())
            socketio.emit("chat_chunk", {
                "done": True, 
                        "text": generr
            }, to=sid)
            return False  
def processio(p):
        loggedin(True)
        delsession()
        session.modified = True   
        socketio.emit('force_logout', to=f"user_{p}") 
        socketio.sleep(0.1)  
        disconnect()                    
@socketio.on("connect")
def connio():
    p=session.get('user_id') or 0
    if not p:
        processio(p)
        return False 
    request_count[request.sid]=0    
    join_room(f"user_{p}")
@socketio.on("get_improvements")
def gimprove(data):
    reqid = request.sid
    p=session.get('user_id') or 0
    if not p:
        processio(p)
        return False 
    key = global_rate_limit_key()
    limit_item = parse(f"{maxaiprompts}/minute") 
    if  not session.get('admin_logged_in') and not limiter.limiter.hit(limit_item, key):
        emit("chat_chunk", {
                "text": "You are moving too fast!  Slow down the pace",
                "done": True
            },to=reqid)
        return False   
    url_parts = request.referrer.split('/')
    page_id = url_parts[-1]
    vobj=getvideobyid(int(page_id))    
    if  (not data['token']==vobj.token )or not vobj:
        emit("chat_chunk", {
                "text": "Something went wrong Kindly <a href='?reload=true'>refresh</a> the page",
                "done": True
            },to=reqid)
        return False        
    executor.submit(execute_imrovement_task, reqid, int(data['vid_id']),time.time() )
@socketio.on("prompt")
def processdata(data):
    prompt=data['prompt']
    reqid = request.sid
    p=session.get('user_id') or 0
    if not p:
        processio(p)
        return False    
    key = global_rate_limit_key()
    limit_item = parse(f"{maxaiprompts}/minute") 
    if  not session.get('admin_logged_in') and not limiter.limiter.hit(limit_item, key):
        emit("chat_chunk", {
                "text": "You are moving too fast!  Slow down the pace",
                "done":True
            },to=reqid)
        return False
    url_parts = request.referrer.split('/')
    page_id = url_parts[-1]    
    vobj=getvideobyid(int(page_id))    
    if  not data['token']==vobj.token or not vobj:
        emit("limit_reached", 
             {"msg":"Something went wrong Kindly <a href='?reload=true'>refresh</a> the page"}
            ,to=reqid)
        return False
    isactive=acchats.get(reqid)
    sid = reqid
    count = request_count.get(sid, 0)
    request_count[sid]=count + 1
    if count >= maxaiprompts:
        emit("limit_reached", {"msg": "Prompt limit reached"}, to=sid)
        return False
    if isactive: 
        request_count[sid]=maxaiprompts+1
        return False
    if len(prompt)>maxipromptlength:
        emit("chat_chunk", {
                "text": "Too long prompt!",
                "done":True
            },to=reqid)
        return False
    oldprompt=data['analyzeddata'] 
    lastprompt=data['lastprompt']
    acchats[reqid]=True
    # print("here nknfdnfndjf")
    executor.submit(execute_chat_task, reqid, int(data['vidid']),oldprompt,prompt,lastprompt,time.time() )
@socketio.on('disconnect')
def handle_disconnect():
    user_id = session.get('user_id')
    if request_count.get(request.sid):del request_count[request.sid]
    if acchats.get(request.sid):del acchats[request.sid]
    if alrimproved.get(request.sid):del alrimproved[request.sid]
    if user_id:
        leave_room(f"user_{user_id}")            
@videobp.route('/video-check/<int:id>/<token>',methods=['POST'])
@limiter.limit('10 per minute')
def checkifvidexists(id,token):
    x=currentdb.query(videos).join(channels).join(users).filter(
        videos.id == id,
        videos.display == True,
        users.permanentdisabled == False,
        channels.ischannelenabled == True,
        videos.token == token
    ).first() is not None
    if x:
        return jsonify({"success":True}),200   
    else:
        return jsonify({"error":False}),500
@videobp.route(f'/{str(uuid.uuid4())}/<string:err>')
@limiter.exempt
def viderr(err):
    flash(f"{err} coud'nt be processed",error)
    return redirect(url_for('index'))
@videobp.route('/view_video/<int:id>')
@validatevideo

def viewvid(id):
    thivid = (
    currentdb.query(
        videos.view_count.label('view_count'),
        videos.like_count.label('like_count'),
        videos
    )
    .join(channels, videos.channel_id == channels.id)
    .join(users, channels.user_id == users.id) 
    
    
    .filter(videos.id == id) 
    .group_by(videos.id, channels.id, users.id) 
    .options(
        contains_eager(videos.parent_channel)
        .contains_eager(channels.owner),
        
        selectinload(videos.comments).joinedload(comments.owner),
        selectinload(videos.comments)
            .selectinload(comments.replieswithincomment)
            .joinedload(replieswithincomment.owner)
    )
    .first()
)
    v_count, l_count, obj = thivid
    userid=session.get('user_id')
    user_has_commented = any(c.user_id == userid for c in obj.comments)
    g.channel=channels.query.filter_by(user_id=userid).first()    
    if obj.display and obj.parent_channel.ischannelenabled:
        plist=(
    currentdb.query(playlists)
    .join(users, playlists.user_id == users.id) 
    .join(playlistvideo, playlists.id == playlistvideo.playlist_id) 
    .options(
        contains_eager(playlists.owner)
    )
    .filter(
        playlists.user_id == userid,
        playlistvideo.video_id == id,
        users.permanentdisabled == False
    )
    .all()
)
 
        aisummary=obj.aisummary
        if aisummary and aisummary.endswith(sumgenerr):
             aisummary=aisummary.removesuffix(sumgenerr)+"..."
        recommended_videos=generateuserprefferedcategoryvids(session.get('user_id'),None,vidid=id,scategory=obj.category.lower())
        if getattr(g, 'user', None) and obj.parent_channel.user_id==userid:
            return render_template("watchvid.html",
                                   aisummary=aisummary,user_has_commented=user_has_commented,
                                   recommended_videos=recommended_videos,maxinnercomments=maxiinercommentspervideo,
                                   maxcomments=maxcommentspervideo,alr_add=plist,v_count=v_count,l_count=l_count ,
                                   user_playlists=getallplaylistobject(userid,0,None) ,liked=False,ifsub=False ,
                                   vid=obj,me=True,subs=getallsubscribersofachannel(obj.parent_channel.id))
        isusb=checkifsubscribed(userid,obj.parent_channel.id)
        li=checkiflikedvideo(userid,obj.id)
        if not getattr(g, 'user', None):
            flash("Login to comment or report content") 
        return render_template("watchvid.html",aisummary=aisummary,user_has_commented=user_has_commented,
                               recommended_videos=recommended_videos,maxinnercomments=maxiinercommentspervideo,
                               maxcomments=maxcommentspervideo,alr_add=plist,l_count=l_count,v_count=v_count,
                               user_playlists=getallplaylistobject(userid,0,None),liked=li,ifsub=isusb ,
                               vid=obj,me=False,subs=getallsubscribersofachannel(obj.parent_channel.id))
    else:
        flash("Video not found")
        return redirect(url_for('index'))
@videobp.route('/add-views/<int:videoid>' ,methods=["POST"])
@limiter.limit('10 per minute')
def addviews(videoid):
    if not session.get('temptoken'):
        session['temptoken']=str(uuid.uuid4())
    session.permanent=True
    onedaygap=datetime.now() - timedelta(days=1)
    halfdaygap=datetime.now() - timedelta(hours=12)
    obj=getvideobyid(videoid)
    userid=session.get('user_id')
    if not obj:
        return jsonify({"error":"not found"}),404
    c=obj.category
    data=request.get_json()
    p=math.floor(float(data.get('increment', 0)) * 10) / 10 
    if getattr(g, 'user', None) and obj.parent_channel.owner.id==userid:
        x=getuserobj(userid)
        if x and x.collect_data and data:
            try:
                if c not in x.userclicks:
                    x.userclicks.append(c)
                if x.viewduration.get(c):
                    x.viewduration[c]+=p
                else:
                    x.viewduration[c]=p
                currentdb.commit()                                     
                viewexists = currentdb.query(views).filter(
                                    views.token == str(userid),
                                    views.video_id == obj.id,
                                    views.created >= onedaygap
                                ).first() 
                if not viewexists:
                    viewobj=views(video_id=videoid,token=str(userid))
                    currentdb.add(viewobj)
                    currentdb.commit()
                    syncviews(obj)      
                    return jsonify({"success":True}),200
                else:
                    viewexists.show=True if x.collect_data else False
                    currentdb.commit()
                    # print("View eixts of this video owner")
                    syncviews(obj)      
                    return jsonify({"error":False}),500   
            except Exception as e:
                currentdb.rollback()
                return jsonify({"error":False}),500     
    else:
        try:
            if getattr(g, 'user', None):
                x=getuserobj(userid)
                if x and x.collect_data and data:
                    if c not in x.userclicks:
                        x.userclicks.append(c)
                    if x.viewduration.get(c):
                        x.viewduration[c]+=p
                    else:
                        x.viewduration[c]=p
                    currentdb.commit()
            tok=str(userid) if getattr(g, 'user', None) and userid else str(session.get('temptoken'))
            viewexists = currentdb.query(views).filter(
                                views.token == tok,
                                views.video_id == obj.id,
                                views.created >= halfdaygap
                            ).first() 
            if not viewexists:        
                viewobj=views(video_id=videoid,token=tok)
                currentdb.add(viewobj)
                currentdb.commit()
                syncviews(obj)      
                return jsonify({"success":True}),200

            else:
                viewexists.show=True
                currentdb.commit()
                # print("View eixts for this non owner user")
                syncviews(obj)      
                return jsonify({"error":False}),500
 
        except Exception as e:
                currentdb.rollback()
                return jsonify({"error":False}),500  
@videobp.route('/like_video/<int:id>' ,methods=["POST"])
@requireduserlogin
@validatevideononowner
def like(id):
    obj=None
    obj=getvideobyid(id)   
    userid=session.get('user_id')
    if getattr(g, 'user', None) and not obj.parent_channel.user_id==userid:
        li=checkiflikedvideo(userid,id)
        if not li:  
            new_obj=likes(user_id=userid,video_id=id)
            try:               
                currentdb.add(new_obj)
                currentdb.commit()
                addnotification(userid,f"Video: {obj.name} liked","Video liked")
                flash('Video liked',success)
            except Unauthorized:
                            raise                  
            except Exception as e:
                currentdb.rollback()
                flash(f"Error: {e}",error)   
    synclikes(obj)            
    return redirect(url_for('.viewvid' ,id=id) if obj else url_for('index'))
@videobp.route('/unlike_video/<int:id>' ,methods=["POST"])
@requireduserlogin
@validatevideononowner
def unlike(id):
    obj=getvideobyid(id)   
    userid=session.get('user_id')   
    if getattr(g, 'user', None) and not obj.parent_channel.user_id==userid:
        li=checkiflikedvideo(userid,id)
        if li:  
            d=likes.query.filter_by(user_id=userid, video_id=id).first()
            try:
                currentdb.delete(d)
                currentdb.commit()
                flash('Video unliked',success)
            except Unauthorized:
                    raise      
            except Exception as e:
                currentdb.rollback()
                flash(f"Error: {e}",error)
    synclikes(obj)            
    return redirect(url_for('.viewvid' ,id=id) if obj else url_for('index'))    
@videobp.route('/upload/<int:id>' ,methods=['POST' ,"GET"])
@limiter.limit("8 per hour",methods=["POST"])
@requireduserlogin
@createtaskai
def upload(id,aitoken=None):
    tchannel=getsinglechannelobjbyid(id)
    userid=session.get('user_id')
    count=(currentdb.query(func.count(videos.id))
               .filter(videos.channel_id == tchannel.id)
               .scalar())
    if count>=maxvideoupload:
            flash("Video creation limited reached!",error)
            return redirect(request.referrer or url_for('channelbp.viewchannel',id=id))
    if getattr(g, 'user', None) and tchannel and tchannel.ischannelenabled:
        if userid==tchannel.user_id:
            if request.method=="POST":
                if count>=maxvideoupload:
                    flash("Video creation limited reached!",error)
                    return redirect(request.referrer or url_for('channelbp.viewchannel',id=id))     
                name=request.form.get('name')
                descr=request.form.get('desc')
                public=request.form.get('privacy')
                ca=request.form.get('category').lower()
                file=request.files.get('video')
                file1=request.files.get('thumbnail')
                if len(name)<10 or len(name)>40 or len(descr)>300 or len(descr)<30 or ca not in category:
                    flash("Invalid input data" ,error)
                    return redirect(url_for(".upload",id=id))   
                d=False
                if int(public)==1:
                    d=True
                if checkfilesize(file,500)!=True:
                    return redirect(url_for('.upload',id=id)) 
                if checkfilesize(file1,10)!=True:
                    return redirect(url_for('.upload',id=id)) 
                xx=savetopc(file,True,videospath)
                if not is_video_valid(os.path.join(videospath,xx)):
                    flash("Upload a longer duartion video",error)
                    return redirect(url_for(".upload",id=id))
                xx1=savetopc(file1,True,thumbnailspath)
                duration=get_video_duration(os.path.join(videospath,xx))
                newobj=videos(token=secrets.token_urlsafe(32),duration=duration,name=name,description=descr,created=datetime.now(),channel_id=tchannel.id,category=ca,display=d,file=xx,thumbnail=xx1)
                try:                     
                    currentdb.add(newobj)
                    currentdb.commit()
                    newobj.aisummary=executor.submit(exe_ai_sum ,newobj.id,time.time(),aitoken,userid,True).result()
                    currentdb.commit()
                    if int(public)==1:
                        subs=currentdb.query(subscribers.user_id).join(
                            users, subscribers.user_id == users.id
                        ).filter(
                            subscribers.channel_id == tchannel.id
                        ).all()  
                        notification_data = [
                            {
                                "title": "New video",
                                "content": f"{tchannel.channelname} has uploaded: {name}!",
                                "user_id": sub_id[0],
                                "created": datetime.utcnow()
                            }
                            for sub_id in subs 
                        ] 
                        if notification_data:
                            currentdb.execute(insert(notifications), notification_data)
                            currentdb.commit()
                    l=newobj.aisummary
                    addnotification(id,f"Video: {name} uploaded!","Video upload")  
                    flash("Video uploaded" ,success) if l and not l.endswith(sumgenerr) else flash("Something went wrong during summary generation" ,error)        
                    return redirect(url_for('channelbp.viewchannel' , id=id))
                except Unauthorized:
                        raise           
                except Exception as e:
                    currentdb.rollback()
                    flash(f"Error: {e}" ,error)
                return redirect(url_for('.upload' , id=id)) 
            g.channel=tchannel
            flash(f"Uploading to channel:  <a href='{url_for('channelbp.viewchannel',id=g.channel.id)}' class='text-primary fw-bold'>{g.channel.channelname}<i class='fas text-primary  fa-external-link-alt'></i></a>" , info)
            return render_template("upload.html" ,categories=category)
        else:
            return redirect(url_for('viewprofile' ,userid=userid) if getuserobj(userid) else url_for('index'))    
    else:
        flash("Not logged in " , error) if not getattr(g, 'user', None) else flash("Channel not found " , error)
        return redirect(url_for('channelbp.viewchannel' ,id=id) if getuserobj(userid) else url_for('index'))
@videobp.route('/edit_video/<int:id>' ,methods=["POST","GET"])
@limiter.limit("8 per hour",methods=["POST"])
@requireduserlogin
@validatevideo
@createtaskai
def editvid(id,aitoken=None):
    if not request.method=="POST":
        baseobj = (
    currentdb.query(
        videos.view_count.label('view_count'),
        videos.like_count.label('like_count'),
        videos
    )
    .join(videos.parent_channel)
    .join(channels.owner)
    .filter(
        videos.id == id,            
    )
    .group_by(videos.id, channels.id, users.id) 
    .options(
        contains_eager(videos.parent_channel)
        .contains_eager(channels.owner)
    )
    .first()
)
        v_count, l_count,obj=baseobj    
    else:obj= getvideobyid(id)
    userid=session.get('user_id')   
    if getattr(g, 'user', None) and obj.parent_channel.user_id==userid:
        if request.method=="POST":
            ai=request.form.get('ai_summary')
            if ai:
                obj.aisummary=executor.submit(exe_ai_sum ,obj.id,time.time(),aitoken,userid,False).result()
                obj.token=secrets.token_urlsafe(32)
                try:
                    currentdb.commit()
                    l=obj.aisummary
                    flash("Summary updated " ,success) if l and not l.endswith(sumgenerr) else flash("Something went wrong during summary generation" ,error)
                except Unauthorized:
                     raise
                except Exception:
                    currentdb.rollback()
                    flash(f"Error: {e}" ,error)
                return redirect(url_for('.editvid',id=id))                     
            name=request.form.get("name")
            descr=request.form.get("desc")
            tfile=request.files.get("tfile")
            vfile=request.files.get("vfile")
            privacy=request.form.get("privacy")
            ca=request.form.get("category").lower()
            if len(name)<10 or len(name)>40 or len(descr)>300 or len(descr)<30 or ca not in category:
                    flash("Invalid input data" ,error)
                    return redirect(url_for(".editvid",id=id))
            if vfile and not checkfilesize(vfile,500):
                    return redirect(url_for('.editvid',id=id)) 
            if tfile and not checkfilesize(tfile,10):
                    return redirect(url_for('.editvid',id=id))
            gensum=False
            if not name==obj.name or not descr==obj.description or not ca==obj.category or vfile or tfile:gensum=True
            obj.name=name
            obj.description=descr
            obj.category=ca
            if int(privacy)==1:
                obj.display=True
            else:
                obj.display=False
            if tfile:
                tname=obj.thumbnail
                obj.thumbnail=savetopc(tfile,True,thumbnailspath)
            if vfile:    
                vfi=obj.file
                newvfi=savetopc(vfile,True,videospath)
                #anaylaze the vidoe with previosu conextt to see wheteh the vieoe euplaoded i actaully worthy or not 
                #for now dleete views and likes
                models_to_clean = [views, likes]
                for model in models_to_clean:
                    currentdb.execute(
                        delete(model).where(model.video_id == id)
                    )
                currentdb.commit()
                if not is_video_valid(os.path.join(videospath,newvfi)):
                    flash("Upload a longer duration video",error)
                    currentdb.rollback()
                    return redirect(url_for(".editvid",id=id))
                obj.file=newvfi
                obj.duration=get_video_duration(os.path.join(videospath,newvfi))
            try:          
                if tfile:removefiles(tname,thumbnailspath)
                if vfile:removefiles(vfi,videospath)
                currentdb.commit()
                if gensum:
                    obj.aisummary=executor.submit(exe_ai_sum ,obj.id,time.time(),aitoken,userid,False if not vfile else True).result()
                    obj.token=secrets.token_urlsafe(32)
                currentdb.commit()
                l=obj.aisummary
                if gensum:
                    flash("Video updated",success) if l and not l.endswith(sumgenerr) else flash("Something went wrong during summary generation" ,error)
                else:
                    flash("Video updated",success)
            except Unauthorized:
                    raise      
            except Exception as e:
                currentdb.rollback()
                flash(f"Error: {e}" ,error)
            return redirect(url_for('.editvid',id=id))        
        if not obj.parent_channel.ischannelenabled and not obj.display:
            flash("Your channel and the video are set to private and can't be seen by anyone",info)
        elif not obj.parent_channel.ischannelenabled:
            flash("This channel is private and video(s) can't be seen by anyone",info)
        elif not obj.display:
            flash("This video is private and can't be seen by anyone",info)
        flash("Summary is automatically updated when changes are detected",info)
        return render_template('editvid.html' , vid=obj,categories=category,views=v_count,likes=l_count)
    else:
        flash("video not found",error) if getattr(g, 'user', None) else flash("Not logged in" ,error)
        return redirect(url_for('index'))
@videobp.route('/delete_video/<int:id>',methods=["POST"])
@requireduserlogin
@validatevideo
def delvid(id):
    obj=getvideobyid(id)
    userid=session.get('user_id')    
    previd=obj.parent_channel.id
    if getattr(g, 'user', None) and obj.parent_channel.user_id==userid:
        try:
            tname=obj.thumbnail
            vfi=obj.file      
            currentdb.delete(obj)
            removefiles(tname,thumbnailspath)
            removefiles(vfi,videospath)
            removefiles(f"{vfi}.vtt",vttfolderpath)
            addnotification(userid,f"Video: {obj.name}  deleted","Video removal")
            currentdb.commit()
            if cachedvid.get(str(obj.id)):del cachedvid[(str(obj.id))]
            flash("Video  deleted" ,success)
        except Unauthorized:
                    raise      
        except Exception as e:
            currentdb.rollback()
            flash("Video failed to delete" ,success)
        return redirect(url_for('channelbp.viewchannel',id=previd))
    else:
        flash("Video not found" ,error)    
        return redirect(url_for('index'))
@videobp.route('/add_comment/<int:id>' ,methods=["POST"])
@limiter.limit("10 per minute")
@requireduserlogin
@validatevideononowner
def addcomment(id):
    obj=getvideobyid(id)
    l=obj.parent_channel.user_id
    count=currentdb.query(func.count(comments.id)).filter(comments.video_id == id).scalar()
    if count>=maxcommentspervideo:
        flash("Comment limit reached!",error)
        return redirect(url_for('.viewvid',id=obj.id))
    userid=session.get('user_id')
    if getattr(g, 'user', None) and obj:
            if not getuserobj(userid).permanentdisabled:
                content=request.form.get('comment')
                if len(content)>300 or len(content)<10:
                    flash("Invalid comment length",error)
                    return redirect(request.referrer or url_for('.viewvid',id=id) if obj and getattr(g, 'user', None) else url_for('index')) 
                new_obj=comments(user_id=userid,video_id=id,content=content,created=datetime.now())
                try:                    
                    currentdb.add(new_obj)
                    currentdb.commit()
                    if l==userid:
                        addnotification(userid,f"You commented on your own video: {obj.name} " ,"Add comment")
                    else:
                        addnotification(l,f"New comment on video: {obj.name} " ,"Add comment")
                        addnotification(userid,f"You commented on video: {obj.name} " ,"Add comment")
                    flash('Comment added ',success)
                except Unauthorized:
                    raise          
                except Exception as e:
                    currentdb.rollback()
                    flash(f"Error: {e}",error)
            else:
                flash("You are banned!" ,error)          
    else:
        flash("Not logged in", error)
    return redirect(request.referrer or url_for('.viewvid',id=id) if obj and getattr(g, 'user', None) else url_for('index')) 
@videobp.route('/delete_comment/<int:id>',methods=['POST'])
@requireduserlogin
def delcomment(id):
    obj=None
    obj=comments.query.filter_by(id=id).first()
    x=obj.parent_video.id
    y=getvideobyid(x)
    if not y or not y.parent_channel.ischannelenabled or not y.display:
            flash("Video not found",error)
            return redirect(url_for('index'))
    userid=session.get('user_id')
    if getattr(g, 'user', None) and obj:
        if obj.owner.id==userid:
            try:               
                currentdb.delete(obj)
                currentdb.commit()
                flash('Comment deleted ',success)
            except Unauthorized:
                    raise          
            except Exception as e:
                currentdb.rollback()
                flash(f"Error: {e}",error)
    else:
        flash("Not logged in" if obj else "Video not found", error)
    return redirect(request.referrer or url_for('.viewvid',id=x) if obj and getattr(g, 'user', None) else url_for('index'))
@videobp.route('/add_innercomment/<int:id>',methods=["POST"]) 
@limiter.limit("10 per minute")
@requireduserlogin
def addinnercomment(id):
    userid=session.get('user_id')
    obj=comments.query.filter_by(id=id).first()
    if not obj:
            flash("Comment not found",error)
            return redirect(request.referrer or url_for('index'))        
    x=obj.parent_video.id
    y=getvideobyid(x)
    if not y or not y.parent_channel.ischannelenabled or not y.display:
            flash("Video not found",error)
            return redirect(url_for('index'))
    count=currentdb.query(func.count(replieswithincomment.id)).filter(replieswithincomment.comment_id == id).scalar()
    if count>=maxiinercommentspervideo:
        flash("Comment limit reached!",error)
        return redirect(url_for('.viewvid',id=x))
    if getattr(g, 'user', None) and obj:
        if not getuserobj(userid).permanentdisabled:
            content=request.form.get('content')
            if len(content)>300 or len(content)<10:
                flash("Invalid comment length",error)
                return redirect(request.referrer or url_for('.viewvid',id=id) if obj and getattr(g, 'user', None) else url_for('index'))             
            newobj=replieswithincomment(content=content,created=datetime.now(),comment_id=id,user_id=userid)
            try:         
                currentdb.add(newobj)
                currentdb.commit()
                if obj.owner.id==userid:
                    addnotification(userid,f"You replied on your comment, on video: {obj.parent_video.name} " ,"Comment reply")
                else:
                    addnotification(obj.owner.id,f"Reply on your comment on video: {obj.parent_video.name} " ,"Comment reply")
                toreply=[ x.user_id  for x in obj.replieswithincomment if x.user_id!=userid]
                for x in toreply:
                    addnotification(x,f"Reply on your comment of video named:{obj.parent_video.name}","Comment reply")
                flash("Replied to comment " ,success)  
            except Unauthorized:
                    raise          
            except Exception as e:
                currentdb.rollback()
                flash(f"Error: {e}" ,error)    
        else:
            flash("You are banned!" ,error)
    else:
        flash("Not logged in" if obj else "Comment not found", error)
    return redirect(request.referrer or url_for('.viewvid',id=x) if obj and getattr(g, 'user', None) else url_for('index')) 
@videobp.route('/remove_innercomment/<int:id>',methods=["POST"])
@requireduserlogin 
def removeinnercomment(id):
    userid=session.get('user_id')
    obj=replieswithincomment.query.filter_by(id=id).first()
    x=obj.parent_comment.parent_video.id
    y=getvideobyid(x)
    if not y or not y.parent_channel.ischannelenabled or not y.display:
            flash("Video not found",error)
            return redirect(url_for('index'))
    if getattr(g, 'user', None) and obj and obj.parent_comment:
        if obj.owner.id==userid:
            try:          
                currentdb.delete(obj)
                currentdb.commit()
                flash("Reply deleted " ,success) 
            except Unauthorized:
                    raise             
            except Exception as e:
                currentdb.rollback()
                flash(f"Error: {e}" ,error)
    else:flash("Not logged in" if obj else "Comment not found", error)
    return redirect(request.referrer or url_for('.viewvid',id=x) if obj and getattr(g, 'user', None) else url_for('index'))     
@videobp.route(f'/{str(uuid.uuid4())}',methods=['post'])
@limiter.limit("3 per minute")
def delviewhistory():
    data=request.form.get("useriddel")
    l=getattr(g, 'user', None)
    try:
        if l:data=int(data)
        if not l and data==session.get('temptoken'):
            currentdb.query(views).\
                filter(views.token == str(session.get('temptoken'))).\
                update(
                    {views.show: False}, 
                    synchronize_session='fetch'
            )
            currentdb.commit()
            flash("Watch history cleared",success)
        elif l and data==session.get('user_id'):
            currentdb.query(views).\
            filter(views.token == str(session.get('user_id'))).\
            update(
                {views.show: False}, 
                synchronize_session='fetch'
            )
            currentdb.commit()
            flash("Watch history cleared",success)
        else:
            flash("User not found")
    except Unauthorized:
        raise      
    except Exception as e:
        currentdb.rollback() 
        flash(f"Error: {e}",error)
    return redirect(request.referrer or url_for('index'))    