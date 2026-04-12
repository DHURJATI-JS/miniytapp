from flask import Blueprint, render_template
from imports import *
accsettings = Blueprint('accsettings', __name__)
@accsettings.route('/settings',methods=["POST",'GET'])
@limiter.limit("10 per minute",methods=['POST'])
@requireduserlogin
def settings():
    userid=session.get('user_id')
    if request.method=="POST":
        userbj=getuserobj(userid)
        if userbj:
            currentpass=request.form.get('current_password') or ""
            newpass=request.form.get('new_password')
            newname=request.form.get('name') or ''
            newname=newname.strip()
            newemail=request.form.get('email').lower().strip() or '' 
            cdata=None
            cdata=request.form.get('cdata')
            pphoto=None
            pphoto=request.files.get('profile_photo')
            if len(newname)<10 or len(newname)>50 or len(newemail)<3 or len(newemail)>100 :
                flash("Invalid input data",error)
                return redirect(url_for('.settings')) 
            if check_password_hash(userbj.password,currentpass):
                if newpass:
                    if len(newpass)<10 or len(newpass)>100:
                        flash("Invalid input data",error)
                        return redirect(url_for('.settings'))                         
                    userbj.password=generate_password_hash(newpass)
                if newname:
                    userbj.name=newname
                if newemail:
                    userbj.email=newemail
                if pphoto:
                    if not checkfilesize(pphoto,4):return redirect(url_for('.settings'))
                    f=userbj.profilephoto
                    userbj.profilephoto=savetopc(pphoto,True,folderpath)
                if cdata:
                    userbj.collect_data=True
                else:
                    userbj.collect_data=False                            
                try:
                    currentdb.commit()
                    if pphoto:removefiles(f,folderpath)
                    emailadder(newemail)
                    addnotification(userid,"Account updated ","Account update")
                    flash("Account updated",success)    
                    return redirect(request.referrer or url_for('index'))
                except Unauthorized:
                    raise 
                except Exception as e:
                    currentdb.rollback()
                    flash(f"Error: {e}",error)
                    return redirect(url_for('.settings'))    
            else:
                flash("Invalid password",error)
                return redirect(url_for('.settings')) 
        else:       
            flash('User not found' if not userbj else "Invalid password",error)
            return redirect(url_for('index'))
    else:
        stats=getuserobj(userid).viewduration or {}
        categories=list(stats.keys()) if stats else None
        watchcount=list(stats.values()) if stats else None
        print(watchcount,categories)
        return render_template('settings.html',categories=categories or {},watch_counts=watchcount or {})
@accsettings.route('/clearhistory',methods=["POST"])
@requireduserlogin
def clearhistory(): 
    userobj=None
    userid=session.get('user_id')
    userobj=getuserobj(userid)
    if not userobj:
        flash("User not found",error)
        return redirect(url_for('index'))
    if not check_password_hash(userobj.password,request.form.get("password") or ""):
        flash("Invalid password",error)
        return redirect(url_for('.settings'))
    userobj.viewduration.clear()
    userobj.userclicks.clear()
    try:
        currentdb.commit()
        addnotification(userid,"History cleared successfully","Cleared history")
        flash("History cleared successfully",success)
        return redirect(url_for('.settings'))
    except Unauthorized:
        raise 
    except Exception as e:
        currentdb.rollback()
        flash(f"Error: {e}",error)
        return redirect(url_for('.settings'))
@accsettings.route('/delete-account',methods=["POST"])
@requireduserlogin
def delacc():
    userobj=None
    userid=session.get('user_id')
    userobj=getuserobj(userid)
    cp=request.form.get('current_password') or ""
    if not userobj or not check_password_hash(userobj.password,cp):
        flash("User not found" if not userobj else "Invalid password",error)
        return redirect(url_for('index') if not userobj else url_for('.settings'))
    try:
        ee=userobj.email
        n=userobj.name
        nh=session.get('user_id')
        deluserdata(userobj)
        delsession()
        send_email(f"""
        Hi there {n}!
    
        We are sorry to see you go, in case if you ever feel like comming back you are welcome to do so!
        Thank you
        {g.appname} Team
        ***This is a computer geenrated message 
        """,ee)
        flash("Account deleted successfully",success)
        socketio.emit('force_logout', to=f"user_{nh}")
        return redirect(url_for('index'))
    except Unauthorized:
        raise 
    except Exception as e:
        currentdb.rollback()
        flash(f"Error: {e}",error)
        return redirect(url_for('.settings'))