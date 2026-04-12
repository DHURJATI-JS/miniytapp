from flask import Blueprint, render_template
from imports import *
playlistbp = Blueprint('playlistbp', __name__)
@playlistbp.route('/delvidfromplaylist/<int:id>',methods=["POST"]) 
@requireduserlogin
def delvideofromplist(id):
    obj=getplaylistobj(id)
    if not obj:
        flash("Playlist not found")
        return redirect(request.referrer or url_for('.viewplaylists'))
    if not obj.user_id==session.get('user_id'):return redirect(request.referrer or url_for('.viewthatplaylist',id=id))
    vid_id=request.form.get("vid_id") or ''
    if not vid_id:
        flash("Maniuplation detected",error)
        log_event("Manipulation",f"Done by:{getattr(g, 'user', None).id}")
        return redirect(request.referrer or url_for('index')) 
    playlistobj=playlistvideo.query.filter_by(playlist_id=id,video_id=vid_id).first()
    if not playlistobj:
        flash("Video coud'nt be deleted",error)
        return redirect(request.referrer or url_for('.viewthatplaylist',id=id))
    try:
        currentdb.delete(playlistobj)   
        currentdb.commit()
        flash("Video removed from playlist",success)
    except Unauthorized:
                    raise          
    except Exception as e:
        currentdb.rollback()
        flash(f"Error: {e}",error)    
    return redirect(request.referrer or url_for('.viewthatplaylist',id=id))
@playlistbp.route('/user/liked-videos')
@requireduserlogin
def viewlikedvideos():
    userid = session.get('user_id')
    page = request.args.get('page', 1, type=int)
    offset_val=(page - 1) * maxvideoperpage
    has_next=False
    total_liked_count = (
    currentdb.query(func.count(videos.id))
    .join(likes, videos.id == likes.video_id)
    .join(channels, videos.channel_id == channels.id)
    .join(users, channels.user_id == users.id)
    .filter(
        likes.user_id == userid,
        videos.display == True,
        channels.ischannelenabled == True,
        users.permanentdisabled == False
    )
    .scalar() 
)

    vids_query = (
    currentdb.query(
        videos.view_count.label('view_count'),
        videos.like_count.label('like_count'),
        videos
    )
    .join(likes, videos.id == likes.video_id)
    .join(channels, videos.channel_id == channels.id)
    .join(users, channels.user_id == users.id)
    .filter(
        likes.user_id == userid,
        videos.display == True,
        channels.ischannelenabled == True,
        users.permanentdisabled == False
    )
    .options(
        contains_eager(videos.parent_channel) 
        .contains_eager(channels.owner)       
    )
    .group_by(videos.id, channels.id, users.id, likes.created)
    .order_by(likes.created.desc())
    .offset(offset_val)
    .limit(maxvideoperpage + 1)
    .all()
)
    if len(vids_query) > maxvideoperpage:
        vids_query.pop()
        has_next=True 
    return render_template('likedvideos.html', vids=vids_query,has_next=has_next,page=page,lcount=total_liked_count)
@playlistbp.route('/playlists',methods=["POST","GET"])
@limiter.limit("5 per minute",methods=["POST"])
@requireduserlogin
def viewplaylists():
    page = request.args.get('page', 1, type=int)
    offset_val=(page - 1) * maxplaylistsperpage
    userid=session.get('user_id')
    count=currentdb.query(func.count(playlists.id)).filter(playlists.user_id == userid).scalar()
    if request.method=="POST":
        if count>=maxplaylists:
            flash("Playlist threshold reached!",error)
            return redirect(url_for(".viewplaylists"))
        name=request.form.get('name') or ''
        desc=request.form.get('desc') or ''
        if len(name)<10 or len(name)>50 or len(desc)<10 or len(desc)>300:
            flash("Invalid input data",error)
            return redirect(url_for(".viewplaylists"))        
        thumbnail=request.files.get('thumbnail')
        if not checkfilesize(thumbnail,10):return redirect(url_for('.viewplaylists'))
        display=request.form.get('visibility')
        obj=playlists(name=name,description=desc,thumbnail=savetopc(thumbnail,True,bannerpath) if thumbnail else defbanner,display=True if display else False,user_id=session.get('user_id'))
        try:        
            currentdb.add(obj)
            currentdb.commit()
            addnotification(userid,f"Playlist: {name} created!","Playlist Update")
            flash('Playlist added succesfuly',success)
            return redirect(url_for('.viewplaylists'))
        except Unauthorized:
                        raise          
        except Exception as e:
            currentdb.rollback()
            flash(f"Error {e}",error)
            return redirect(url_for('.viewplaylists')) 
    v=None
    has_next=False
    v=getallplaylistobject(userid,offset_val)
    if len(v) > maxplaylistsperpage:
        v.pop()
        has_next=True    
    return render_template('playlists.html',plists=v,bannerpath=url_for('static' ,filename=banners),has_next=has_next,page=page,count=count)
@playlistbp.route('/playlists/<int:id>')
def viewthatplaylist(id):
    obj=getplaylistobj(id)
    if not obj:
        flash("Playlist not found",success)
        return redirect(url_for('.viewplaylists') if loggedin() else url_for('index'))
    if not obj.display and not session.get("user_id")==obj.user_id:
        return redirect(url_for('.viewplaylists') if loggedin() else url_for('index')) 
    if not obj.display:
        flash("This playlist is private and can't be seen by anyone",info)
    else:flash("This playlist is accessible to anyone with the link",info)           
    g.playlist=obj
    page = request.args.get('page', 1, type=int)
    offset_val=(page - 1) * maxvideoperpage
    has_next=False

    vids = (
    currentdb.query(
        videos.view_count.label('view_count'),
        videos.like_count.label('like_count'),
        videos
    )
    .join(playlistvideo, videos.id == playlistvideo.video_id)
    .join(channels, videos.channel_id == channels.id)
    .join(users, channels.user_id == users.id)
    .filter(
        playlistvideo.playlist_id == g.playlist.id, 
        videos.display == True,                      
        channels.ischannelenabled == True,           
        users.permanentdisabled == False             
    )
    .group_by(
        videos.id, 
        channels.id, 
        users.id, 
        playlistvideo.playlist_id, 
        playlistvideo.video_id,
        playlistvideo.created 
    ).order_by(
         playlistvideo.created.desc()
    )
    .options(
        contains_eager(videos.parent_channel)
        .contains_eager(channels.owner)
    ).offset(offset_val).limit(maxvideoperpage+1)
    .all()
)
    if len(vids) > maxvideoperpage:
        vids.pop()
        has_next=True 
    return render_template('viewplaylist.html' ,vids=vids,has_next=has_next,page=page,thisid=id,countv=len(obj.videos))    
@playlistbp.route('/delete-playlist/<int:id>',methods=["POST"])
@requireduserlogin
def deleteplaylist(id): 
    obj=getplaylistobj(id)
    userid=session.get('user_id')
    if obj and obj.user_id==userid:
        try:
            f=obj.thumbnail      
            currentdb.delete(obj)
            currentdb.commit()
            removefiles(f,thumbnailspath)
            addnotification(userid,"Playlist deleted ","Playlist update")
            flash('Playlist deleted ',success)
            return redirect(url_for('.viewplaylists')if loggedin() else url_for('index'))
        except Unauthorized:
                    raise          
        except Exception as e:
            currentdb.rollback()
            flash(f"Error: {e}",error)
            return redirect(url_for('.viewthatplaylist',id=id ) if obj else url_for('.viewplaylists'))
@playlistbp.route('/edit-playlist/<int:id>',methods=["POST","GET"])
@limiter.limit("10 per minute",methods=['POST'])
@requireduserlogin
def editplaylist(id):
    userid=session.get('user_id')
    obj=getplaylistobj(id)
    if obj and obj.user_id==userid:
        if request.method=="POST":
            name=request.form.get('name') or ''
            descr=request.form.get('desc') or ''
            if len(name)<10 or len(name)>50 or len(descr)<10 or len(descr)>300:
                flash("Invalid input data",error)
                return redirect(url_for(".viewplaylists"))             
            thumbnail=request.files.get('thumbnail')
            if not checkfilesize(thumbnail,10):return redirect(url_for('.editplaylist',id=id))
            visibile=request.form.get('visibility')
            if visibile:
                obj.display=True
            else:
                obj.display=False
            if name:
                obj.name=name
            if descr:
                obj.description=descr
            if thumbnail:
                f=obj.thumbnail
                obj.thumbnail=savetopc(thumbnail,True,bannerpath) 
            try:     
                currentdb.commit()
                if thumbnail:removefiles(f,bannerpath)
                flash("Playlist updated ",success)
                return redirect(url_for('.editplaylist',id=id))
            except Unauthorized:
                            raise              
            except Exception as e:
                currentdb.rollback()
                flash(f"Error: {e}",error)
                return redirect(url_for('.editplaylist',id=id))
        g.playlist=obj
        return render_template('editplaylist.html')
    else:
        return redirect(url_for('.viewplaylists') if loggedin() else url_for('index'))
@playlistbp.route('/append-to-playlist',methods=["POST"])
@requireduserlogin
def appendtoplaylist():
    playlist_id=request.form.get("playlist_id") or ''
    vid_id=request.form.get("vid_id") or ''
    if not vid_id or not playlist_id:
        flash("Maniuplation detected",error)
        log_event("Manipulation",f"Done by:{getattr(g, 'user', None).id}")
        return redirect(request.referrer or url_for('index'))        
    obj=getplaylistobj(playlist_id)
    if not obj:
        flash("Playlist not found",error)
        return redirect(url_for('videobp.viewvid',id=vid_id))
    if not obj.user_id==session.get('user_id'):    
        return redirect(url_for('videobp.viewvid',id=vid_id))
    count=len(obj.videos)
    if count>=maxvideoinplaylist:
        flash("Video addition limit reached!",error)
        return redirect(url_for('videobp.viewvid',id=vid_id))
    vidobj=getvideobyid(vid_id)
    if not vidobj:
        flash("Video not found",error)
        return redirect(url_for('index'))
    if currentdb.query(playlistvideo).filter(playlistvideo.playlist_id==playlist_id, playlistvideo.video_id==vid_id).first():
        flash("Video cannot be added to the same playlist",error)
        return redirect(request.referrer or url_for('.viewplaylists'))
    cobj=playlistvideo(playlist_id=playlist_id,video_id=vid_id)    
    try:
        currentdb.add(cobj)
        currentdb.commit()
        flash(f"Video added ",success)
        return redirect(request.referrer or url_for('.viewplaylists'))
    except Unauthorized:
                    raise      
    except Exception as e:
        currentdb.rollback()
        flash(f"Error: {e}",error)
        return redirect(request.referrer or url_for('.viewplaylists'))