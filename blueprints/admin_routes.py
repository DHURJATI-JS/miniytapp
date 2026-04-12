from flask import Blueprint, render_template
from imports import *
adminbp = Blueprint('adminbp', __name__)
@adminbp.route("/admin/main",methods=["POST","GET"])
@admin_only
def admin():
    pending_reports =(
    reports.query
    .filter_by(status='pending')
    .all()
)
    return render_template('admin_main.html',reports=pending_reports)
@adminbp.route('/admin/logout',methods=["POST"])
def loggadminoff():
        if session.get('admin_logged_in'):del session['admin_logged_in'] 
        if session.get("admin_email"):del session['admin_email'] 
        if session.get("admintoken"):del session['admintoken'] 
        flash("Logout successfull",success)
        return redirect(url_for('.adminlogin'))
@adminbp.route('/admin',methods=["POST","GET"])
def adminlogin():
    if session.get('admin_logged_in') or session.get('admin_email') or session.get('admintoken'):
        flash("Already logged in",error)
        return redirect(url_for('.admin'))
    if request.method == 'POST':
        adm_email = request.form.get('email') or ''
        adm_pass = request.form.get('password') or ''
        admin = admin_users.query.filter_by(email=adm_email).first()
        if admin and check_password_hash(admin.password, adm_pass):
            x=str(uuid.uuid4())
            admin.token=x
            currentdb.commit()
            session['admin_logged_in'] = True
            session['admin_email'] = admin.email
            session['admintoken']=x
            flash('login succesfull',success)
            return redirect(url_for('.admin')) 
        flash("Invalid Credentials",error)   
    return render_template("admin-login.html")
@adminbp.route('/reset-admin-password',methods=["POST",'GET'])
def resetadminpass():
    if session.get('admin_logged_in') or session.get('admin_email') or session.get('admintoken'):
        flash("Already logged in",error)
        return redirect(url_for('.admin'))
    if request.method == 'POST':
        email = request.form.get('email')
        admin = admin_users.query.filter_by(email=email).first()
        if admin:
            try:
                temp_password = str(uuid.uuid4())[:8] 
                admin.password = generate_password_hash(temp_password)
                send_email(f"From: admin section {g.appname}!, Admin password: {temp_password}",email)
                currentdb.commit()
                flash("Email sent",success)
                return redirect(url_for('.adminlogin'))
            except Exception as e:
                currentdb.rollback()
                flash("Error sending email", error)
        else:
            flash("Admin email not found.", error)
    return render_template('admin-password.html')
@adminbp.route('/admin/action/<int:report_id>/<string:target>/<string:action>')
@limiter.limit("10 per minute", methods=["POST"]) 
@admin_only
def admin_report_action(report_id, target, action):
    report = currentdb.get(reports,report_id)
    if not report:
        flash("Report not found",error)
        return redirect(url_for('.admin'))
    user_to_act_on = None
    if target == "reporter":user_to_act_on = users.query.get(report.reporter_id)
    elif target == "reported":user_to_act_on = users.query.get(report.reported_user_id)
    if action == "ban":
        if user_to_act_on:
            n=user_to_act_on.name
            m=user_to_act_on.email
            user_to_act_on.permanentdisabled = True 
            channels.query.filter_by(user_id=user_to_act_on.id).update({channels.ischannelenabled: False})
            keys.query.filter_by(user_id=user_to_act_on.id).update({keys.used:True})
            report.status='resolved'
            currentdb.commit()
            send_email(f"""
            Hey there {n}!
            Your activity was judged inapropriate and as a result your account has been banned.
            Thank you
            {g.appname} Team
""",m)            
            flash(f"User {user_to_act_on.name} has been Banned", success)
    elif action == "delete":
        if user_to_act_on:
            n=user_to_act_on.name
            m=user_to_act_on.email
            deluserdata(user_to_act_on)
            currentdb.delete(report)
            currentdb.commit()
            send_email(f"""
            Hey there {n}!
            Your activity was judged inapropriate and as a result your account has been terminated.
            Thank you
            {g.appname} Team
""",m)
            flash("User account and data permanently deleted", success)
    elif action == "done":
        report.status='resolved'
        currentdb.commit()
        send_email(f"""
            Hey there {report.author.name}!
            Your report has been considered and has been processed by our team.
            Thank you
            {g.appname} Team
""",report.author.email)
        flash("Report marked as resolved", "success")
    return redirect(url_for('.admin'))
@adminbp.route('/admin/studio/action', methods=['POST'])
@limiter.limit("10 per minute", methods=["POST"]) 
@admin_only
def admin_studio_action():
    target_val = request.form.get('target_id')
    target_type = request.form.get('target_type') 
    action = request.form.get('action_type')      
    target_user = None
    try:
        if target_type == 'user':
            target_user = currentdb.get(users,target_val)
        elif target_type == 'video':
            vid = currentdb.get(videos,target_val)
            target_user=currentdb.get(users,vid.parent_channel.owner.id)
            if vid:
                if action in ['toggle_video']:
                    c=vid.display
                    vid.display = not vid.display 
                    currentdb.commit()
                    n=target_user.name
                    m=target_user.email
                    if c:
                        send_email(f"""
                        Hey there {n}!
                        Your activity was judged inapropriate and as a result your video named{vid.name} ({target_val}) has been disabled.
                        Thank you
                        {g.appname} Team
                        """,m)
                    else:send_email(f"""
                        Hey there {n}!
                        Your video named{vid.name} ({target_val}) has been restored. Kindly cooporate in the future to avoid such incidents.
                        Thank you
                        {g.appname} Team
                        """,m)    
                    flash(f"Video {target_val} disabled."if c else f"Video {target_val} enabled.", success)
                    return redirect(url_for('.admin'))
                elif action =='wipe':
                    n=target_user.name
                    m=target_user.email
                    k=vid.thumbnail
                    l=vid.file
                    d=vid.id
                    currentdb.delete(vid)
                    currentdb.commit()
                    removefiles(k,thumbnailspath)
                    removefiles(l,videospath)
                    removefiles(f"{l}.vtt",vttfolderpath)
                    if cachedvid.get(str(d)):del cachedvid[(str(d))]
                    send_email(f"""
                    Hey there {n}!
                    Your video was judged inapropriate and as a result your video has been deleted.
                    Thank you
                    {g.appname} Team
                    """,m)
                    flash(f"video #{target_val} deleted", success)
                    return redirect(url_for('.admin'))
        elif target_type == 'channel':
            chnl = currentdb.get(channels,target_val)
            target_user=currentdb.get(users,chnl.owner.id)
            if chnl:
                if action in ['toggle_channel']:
                    c=chnl.ischannelenabled
                    chnl.ischannelenabled = not chnl.ischannelenabled
                    currentdb.commit()
                    n=target_user.name
                    m=target_user.email
                    if c:
                        send_email(f"""
                        Hey there {n}!
                        Your activity was judged inapropriate and as a result your channel named{chnl.channelname} ({target_val}) has been disabled.
                        Thank you
                        {g.appname} Team
                        """,m)
                    else:send_email(f"""
                        Hey there {n}!
                        Your channel named{chnl.channelname} ({target_val}) has been restored. Kindly cooporate in the future to avoid such incidents.
                        Thank you
                        {g.appname} Team
                        """,m)    
                    flash(f"Channel {target_val} disabled."if c else f"Channel {target_val} enabled.", success)
                    return redirect(url_for('.admin'))
                elif action =='wipe':
                    i=target_user.id
                    n=target_user.name
                    m=target_user.email
                    k=chnl.channelbanner
                    l=chnl.channelicon
                    currentdb.delete(chnl)
                    currentdb.commit()
                    removefiles(k,bannerpath)
                    removefiles(l,folderpath) 
                    send_email(f"""
                    Hey there {n}!
                    Your chnanel was judged inapropriate and as a result your channel has been deleted.
                    Thank you
                    {g.appname} Team
                    """,m)
                    flash(f"channel #{i} deleted", success)
                    return redirect(url_for('.admin'))    
    except Exception as e:
        currentdb.rollback()
        flash(f"Error: {e}",error)
        return redirect(url_for('.admin'))
    if target_user:
        try:
            if action == 'wipe':
                i=target_user.id
                n=target_user.name
                m=target_user.email
                if not deluserdata(target_user):
                    flash("Error while deleting user",error)
                    return redirect(url_for(".admin"))
                send_email(f"""
                Hey there {n}!
                Your activity was judged inapropriate and as a result your account has been terminated.
                Thank you
                {g.appname} Team
                """,m)
                flash(f"User #{i} and all associated data wiped.", success)
                return redirect(url_for('.admin'))
            elif action == 'ban':
                c=target_user.permanentdisabled
                target_user.permanentdisabled = not target_user.permanentdisabled 
                if not c:
                    channels.query.filter_by(user_id=target_user.id).update({channels.ischannelenabled: False})
                    keys.query.filter_by(user_id=target_user.id).update({keys.used:True})
                currentdb.commit()
                n=target_user.name
                m=target_user.email
                if not c:
                    send_email(f"""
                    Hey there {n}!
                    Your activity was judged inapropriate and as a result your account has been banned.
                    Thank you
                    {g.appname} Team
                    """,m)
                else:send_email(f"""
                    Hey there {n}!
                    Your account {m} has been enabled! Please cooporate next time to avoid such incidents..
                    Thank you
                    {g.appname} Team
                    """,m)                
                i=target_user.id
                flash(f"User #{i} has been banned." if not c else f"User #{i} has been unbanned.", success)
                return redirect(url_for('.admin'))
        except Exception as e:
            currentdb.rollback()
            flash(f"Error: {e}",error)
        return redirect(url_for('.admin'))
    else:
        flash("Target ID not found in database.", error)
        return redirect(url_for('.admin'))