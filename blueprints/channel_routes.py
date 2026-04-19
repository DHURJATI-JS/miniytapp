from flask import Blueprint, render_template
from imports import *
channelbp = Blueprint('channelbp', __name__)
@channelbp.route('/channel/<int:id>' , methods=["POST", "GET"])
@limiter.limit("5 per minute",methods=['POST'])
@validatechannel
def viewchannel(id):
    if request.method=="POST" and loggedin():
        name=request.form.get('cname') or ''
        desc=request.form.get('cdesc') or ''
        cprofilephoto=request.files.get('cphoto')
        cprofilebanner=request.files.get('cbanner')
        cenable=request.form.get('cenable')
        e=getsinglechannelobjbyid(id)   
        if e:
            if not e.user_id==session.get('user_id'):
                flash("You cannot edit someone else's channel",error)
                return redirect(url_for(".viewchannel",id=id))
            if len(name)<10 or len(name)>50 or len(desc)>500 or len(desc)<10:
                flash("Invalid input data" ,error)
                return redirect(url_for(".viewchannel",id=id))
            e.channelname=name
            e.channeldesc=desc
            if cprofilebanner:
                if not checkfilesize(cprofilebanner,5):
                    return redirect(url_for('.viewchannel',id=id))
                bn=e.channelbanner
                e.channelbanner=savetopc(cprofilebanner,True,bannerpath)
            if cprofilephoto:
                if not checkfilesize(cprofilephoto,4):
                    return redirect(url_for('.viewchannel',id=id))
                cl=e.channelicon
                e.channelicon=savetopc(cprofilephoto,True)
            if cenable:
                e.ischannelenabled=True
            else:
                e.ischannelenabled=False    
            try:        
                addnotification(session.get('user_id'),"Your channel's settings have been updated","Channel update")
                currentdb.commit()
                if cprofilebanner:removefiles(bn,bannerpath)
                if cprofilephoto:removefiles(cl,folderpath)                
                flash("Your channel's settings have been updated" ,success)
            except Unauthorized:
                    raise                 
            except Exception as e:
                currentdb.rollback()
                flash(f"error: {e}" ,error)
            return redirect(url_for('.viewchannel',id=id))
        else:
            flash("Channel doesn't exists" ,error)    
            return redirect(url_for('index'))
    else:    
        page = request.args.get('page', 1, type=int)
        offset_val=(page - 1) * maxvideoperpage
        obj=getsinglechannelobjbyid(id)
        if obj:
            g.channel=obj
            channelid=obj.id
            hasnext=False
            subscriber=getallsubscribersofachannel(channelid)
            video_count, vd = getallvideosofachannel(channelid, offset_val)
            print(vd)
            if len(vd) > maxvideoperpage:
                vd.pop()
                hasnext=True 
            if not vd:
             video_count = 0    
            if obj.ischannelenabled:
                z=False
                isub=False
                if loggedin() and obj.user_id==session.get('user_id'):
                    z=True
                if z!=True:    
                    isub=checkifsubscribed(session.get('user_id'),channelid) 
                return render_template('channel.html' ,cid=id,page=page,has_next=hasnext,video_count=video_count,su=isub,me=z,vids=vd,subs=subscriber,clogo=getpath(g.channel.channelicon),cbanner=getpath(g.channel.channelbanner,True))
            elif obj.ischannelenabled!=True and loggedin() and obj.user_id==session.get('user_id'):
                
                flash("Your channel isn't enabled and cant be seen by others" , info)
                return render_template('channel.html' ,cid=id,page=page,has_next=hasnext,video_count=video_count,su=False,vids=vd ,me=True,subs=subscriber,clogo=getpath(g.channel.channelicon),cbanner=getpath(g.channel.channelbanner,True))
            else:
                flash('Channel not found' , error)
                return redirect(url_for('index'))
        else:
            flash('Channel not found' , error)
            return redirect(url_for('index'))
@channelbp.route('/create-channel',methods=["POST","GET"])
@limiter.limit("3 per minute",methods=['POST'])
@requireduserlogin
def createchannel():
    userid=session.get('user_id')
    count=db.session.query(func.count(channels.id)).filter(channels.user_id == userid).scalar()
    if count>=maxchannels:
            flash("Channel creation limited reached!",error)
            return redirect(url_for('viewprofile',userid=userid))
    if request.method=="POST":
        if count>= maxchannels:
            flash("Channel creation limited reached!",error)
            return redirect(url_for('viewprofile',userid=userid))            
        channelname=request.form.get('channelname') or ''
        channeldesc=request.form.get('description') or ''
        visibilty=request.form.get('cdata')
        icon=request.files.get('icon')
        bannr=request.files.get('banner')
        if len(channelname)<10 or len(channelname)>50 or len(channeldesc)>500 or len(channeldesc)<10:
                flash("Invalid input data" ,error)
                return redirect(url_for(".createchannel"))        
        if icon and not checkfilesize(icon,4):
            return redirect(url_for('.createchannel'))
        if bannr and not checkfilesize(bannr,5):
            return redirect(url_for('.createchannel'))
        if not icon:
            icon=defname
        else:icon=savetopc(icon,True)    
        if not bannr:    
            bannr=defbanner
        else:bannr=savetopc(bannr,True,bannerpath)    
        if not visibilty:
            visibilty=False
        else:visibilty=True    
        newchannel=channels(created=datetime.now(),channeldesc=channeldesc,channelname=channelname,user_id=userid,channelicon=icon,channelbanner=bannr,ischannelenabled=visibilty)
        try:
            currentdb.add(newchannel)
            currentdb.commit()
            flash('channel added ',success)
            return redirect(url_for('viewprofile',userid=session.get('user_id')))
        except Unauthorized:
                    raise          
        except Exception as e:
            currentdb.rollback()
            flash(f"Error: {e}",error)
            return redirect(url_for('.createchannel'))
    return render_template('createchannel.html')
@channelbp.route('/subscribe_channel/<int:id>',methods=['POST'])
@requireduserlogin
@validatechannel
def subchannel(id):
    proceed=False
    userid=session.get('user_id')
    target_channel=getsinglechannelobjbyid(id)
    if not target_channel or not target_channel.ischannelenabled:
        flash("channel not found",error)
        return redirect(url_for('index'))        
    channelid=id
    targetchannelowenrid=target_channel.user_id
    targetchannelname=target_channel.channelname
    if loggedin() and userid!=targetchannelowenrid and not checkifsubscribed(userid,channelid):
        proceed = True
    if proceed:
        obj=subscribers(user_id=userid,channel_id=channelid)
        try:       
            currentdb.add(obj)
            currentdb.commit()
            addnotification(targetchannelowenrid,f"Someone subscribed to {targetchannelname}","Subscribe channel")
            addnotification(userid,f"Subscribed to: {targetchannelname}","Subscribe channel")
            flash(f"Subscribed to: {targetchannelname}",success)
        except Unauthorized:
                    raise              
        except Exception as e:
            currentdb.rollback()
            flash(f"Error: {e}" ,error) 
    syncsubs(target_channel)                                      
    return redirect(request.referrer or url_for('.viewchannel' ,id=id) if target_channel else request.referrer or url_for('index'))
@channelbp.route('/un_subscribe_channel/<int:id>',methods=['POST'])
@requireduserlogin
@validatechannel
def unsubchannel(id):
    proceed=False
    userid=session.get('user_id')
    target_channel=getsinglechannelobjbyid(id)
    if not target_channel or not target_channel.ischannelenabled:
        flash("channel not found",error)
        return redirect(url_for('index'))
    channelid=target_channel.id
    targetchannelowenrid=target_channel.user_id
    targetchannelname=target_channel.channelname
    if loggedin() and userid!=targetchannelowenrid and checkifsubscribed(userid,channelid) :
        proceed = True
    if proceed:
        obj=getsubscribedobj(userid,channelid)
        if obj:
            try:             
                currentdb.delete(obj)
                currentdb.commit()
                addnotification(userid,f"unsubscribed from: {targetchannelname}","Unsubscribe channel")
                flash(f"unsubscribed from {targetchannelname}",success)
            except Unauthorized:
                    raise                  
            except Exception as e:
                currentdb.rollback()
                flash(f"Error: {e}" ,error)
    syncsubs(target_channel)                                      
    return redirect(request.referrer or url_for('.viewchannel' ,id=id) if target_channel else request.referrer or url_for('index'))
@channelbp.route('/deletechannel/<int:id>',methods=["POST"])
@requireduserlogin
def deletechannel(id):
    tchannel=getsinglechannelobjbyid(id)
    userid=session.get('user_id')
    if not tchannel:
        flash("Channel not found",error)
        return redirect(url_for('viewprofile',userid=userid) if loggedin() else url_for('index'))
    if not tchannel.user_id==userid:
        return redirect(url_for('viewprofile',userid=userid) if loggedin() else url_for('index'))
    try:
        removefiles(tchannel.channelbanner,bannerpath)
        removefiles(tchannel.channelicon,folderpath)
        currentdb.delete(tchannel)
        currentdb.commit()
        flash("Channel deleted ",success)
        return redirect(url_for('viewprofile',userid=userid))
    except Unauthorized:
            raise      
    except Exception as e:
        currentdb.rollback()
        flash(f"Error: {e}",error)
        return redirect(url_for('viewprofile',userid=userid))
