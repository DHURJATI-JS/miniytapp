from flask import Blueprint, render_template
from imports import *
authbp = Blueprint('authbp', __name__)
@authbp.route('/reset-password/' ,methods=["POST","GET"])
@limiter.limit("5 per minute",methods=['POST'])
@dontallowiflogged
def respassword():           
    if request.method=="POST":
        email= request.form.get("email").lower().strip() if request.form.get('email') else ""
        print(email)
        useobj=getuserobjbyemail(email)
        if useobj and not useobj.permanentdisabled:
            useid=useobj.id
            now=datetime.now()
            exists_req = currentdb.query(keys).join(keys.owner).filter(
                users.email == email,        
                keys.exp_time > now,        
                keys.used == False          
            ).first()
            if not exists_req:
                code=str(uuid.uuid4())
                token=str(uuid.uuid4())
                time=datetime.now()+timedelta(hours=1)
                exp_time=time.strftime("%I:%M %p")
                st=str(uuid.uuid4())
                objm=keys(code=code,exp_time=time,token=token,user_id=useid,session_token=st)
                try:
                    if not checkifuserexists(useid):
                            flash("user not found",error)
                            currentdb.rollback()
                            return redirect(url_for('authbp.login'))                    
                    currentdb.add(objm)
                    currentdb.commit()
                    session['temp']=st
                    if send_email(f"""
    Hi,

    You requested a password reset. Please click the link below to set a new password:
    {url_for('.nextrespass', token=token, _external=True)}

    Code: {code}    

    This code is valid for 1 hour and will expire at {exp_time}.

    If you did not request this, please ignore this email.
""",email):
                        flash("A code has been sent to your email" ,success)
                    else:
                        flash("Email coudnt be sent" ,error)
                        if objm:
                            currentdb.delete(objm)
                            currentdb.commit()
                        return redirect(url_for('.login'))    
                    addnotification(useid,"Someones is trying to reset your password","PASSWORD RESET")
                    return redirect(url_for('.nextrespass',token=token))
                except Exception as e:
                    currentdb.rollback()
                    flash(f"Error: {e}" ,error)
                    return redirect(url_for('.respassword'))

            else:
                flash("Already a request has been made for this account, wait for 1 hour" ,error)
                return redirect(url_for('.login'))        
        else:
            flash("Invalid email id" ,error)
            return redirect(url_for('.respassword'))
    else:
        processavedemails()
        return render_template("resetpassword.html")
@authbp.route('/reset-password/main/<token>' , methods=["POST","GET"])
@limiter.limit("5 per minute",methods=['POST'])
@dontallowiflogged
def nextrespass(token):
    now = datetime.now()
    valid = currentdb.query(keys).filter(
            keys.token == token,
            keys.exp_time > now,       
            keys.used == False
        ).first()
    if valid :
        vobj=valid
        if request.method=="POST" and vobj:
            sessiond=request.form.get('session')
            if sessiond==vobj.session_token:
                code=request.form.get('code').strip() if request.form.get('code') else ''
                password=request.form.get('password')
                obj=currentdb.query(keys).filter(
                keys.used == False,
                keys.session_token==sessiond,
                keys.token == token,
                keys.exp_time > datetime.now(),
                keys.code==code           
                ).first()
                if not obj:
                    flash('Invalid code')
                    vobj.used=True
                    vobj.session_token=None
                    try:
                        currentdb.commit()
                    except Exception as e:
                        currentdb.rollback()
                        flash(f"Error: {e}" ,error)
                    return redirect(url_for('.respassword'))  
                obj.used=True
                obj.session_token=None
                try:
                    currentdb.commit()
                except Exception as e:
                    currentdb.rollback()
                    flash(f"Error {e}, Contact admin to reset the password" ,error)
                    return redirect(url_for('.respassword',token=token))
                if obj:
                    uid=obj.user_id
                    tochange=getuserobj(uid)
                    if tochange:
                        if len(password)<10 or len(password)>100:
                            flash("Invalid password length",error)
                            return redirect(url_for(".respassword"))
                        tochange.password=generate_password_hash(password)
                        tochange.token=""
                        try:
                            currentdb.commit()
                            socketio.emit('force_logout', to=f"user_{uid}")
                            socketio.sleep(0.1)
                            emailadder(tochange.email)
                            addnotification(uid,"Password changed successfully")
                            flash("Password changed successfully" ,success)
                            if not send_email(f"""
                Hi,

                You requested a password reset. 
                The process has been compeleted successfully and the code cannot be used further.                
                

                If you did not request this, please contact the admin.
                """,tochange.email):flash("Email coudn't be sent" ,error)
                            if session.get('temp'):
                                del session['temp']
                            return redirect(url_for('.login'))
                        except Exception as e:
                            currentdb.rollback()
                            flash(f"Error {e}" ,error)
                            return redirect(url_for('.login'))
                    else:
                        flash("user not found",error)
                        return redirect(url_for('.login')) 
            else:
                flash("Session error" ,error)
                return redirect(url_for('.respassword'))                                               
        elif request.method=="GET":   
            st=str(uuid.uuid4())
            vobj.session_token=st
            session['temp']=st
            try:
                currentdb.commit()
            except Exception as e:
                currentdb.rollback()
                flash(f"Error: {e}" ,error)                                  
            return render_template('resetmainpass.html', token=token,session_uuid=st)
        else:
            flash("Session error",error)
            return redirect(url_for('.respassword'))  
    else:
        flash("Invalid token",error)  
        return redirect(url_for('.respassword'))
@authbp.route('/cancel-token/<token>',methods=['POST'])
@dontallowiflogged
def cancel_reset(token):
    now=datetime.now()
    key_object = currentdb.query(keys).filter(
        keys.token == token,           
        keys.exp_time > now,       
        keys.used == False           
    ).first()
    if key_object and key_object.session_token==request.form.get('session'):
        try:
            email=key_object.owner.email
            key_object.used=True
            currentdb.commit()
            addnotification(users.query.filter_by(email=email).first().id,"Password reset cancelled","PASSWORD RESET")
            if not send_email(f"""
            Hi,

            You requested a password reset cancellation. 
            The process has been compeleted successfully and the code cannot be used further.                
            

            If you did not request this, please ignore this email.
            """,email):flash("Email coudn't be sent" ,error)
            flash("Token cancelled" ,success)
            return redirect(url_for('login'))
        except Exception as e:
            currentdb.rollback()
            flash(f"Error : {e}" ,error)
            return redirect(redirect(url_for('.nextrespass',token=token)))            
    else:
        flash("Invalid token" if not key_object else 'Session error',error)
        return redirect(url_for('.respassword'))        
@authbp.route('/login', methods=['POST', 'GET'])
@limiter.limit("10 per minute",methods=['POST'])
@dontallowiflogged
def login():
    if request.method=="POST":
        try:
            email=request.form.get('email').lower().strip() or ''
            password=request.form.get('password') or ''
            remember=request.form.get('remember')
            prevurl=request.form.get('prevurl') 
            userobj = getuserobjbyemail(email)
            if userobj and check_password_hash(userobj.password,password):
                newtoken=str(uuid.uuid4())
                userobj.token=newtoken
                keys.query.filter_by(user_id=userobj.id, used=False).update({keys.used: True})
                currentdb.commit()
                emailadder(email)
                if remember:
                    tpass=str(uuid.uuid4())
                    if send_email(f"""
        Hi,

        You requested an account fallback. Please click the link below to login with your temporary password
        You may want to change the password later!
        {url_for('.login', _external=True)}?email={email}

        Password: {tpass}    

        If you did not request this, please contact the admin
    """,email):
                        flash("A new password has been sent to your email" ,success)
                        socketio.emit('force_logout', to=f"user_{userobj.id}")
                        socketio.sleep(0.1)
                        userobj.password=generate_password_hash(tpass)
                        currentdb.commit()
                        return redirect(url_for('.login'))
                    else:
                        flash("Email coud'nt be sent.Contact the admin" ,error)
                        return redirect(url_for('.login'))
                if not checkifuserexists(userobj.id):
                            flash("user not found",error)
                            currentdb.rollback()
                            return redirect(url_for('.login'))                      
                mainlogin(userobj.id)
                socketio.emit('force_logout', to=f"user_{session.get('user_id')}")
                socketio.sleep(0.1)
                flash('login successful' , success)                
                return redirect(f'{prevurl}' or url_for('index'))        
            else:
                flash('invalid credentials', error)
                return redirect(url_for('.login'))
        except Exception as e:
                currentdb.rollback()
                flash(f'Something went wrong: {e}' ,error)
                return redirect(url_for('.login'))    
    processavedemails()         
    return render_template('login.html',)
@authbp.route('/forget-account/<string:email>')
@limiter.limit("11 per minute")
@dontallowiflogged
def forget_account(email):
    processavedemails()
    if not session.get('remembered_emails') or not email in session.get("remembered_emails"):
        flash("List not found",error)
        return redirect(request.referrer or url_for('.login'))    
    if email in session.get('remembered_emails'):
        session.get('remembered_emails').remove(email)
        flash("User removed from history",success)
        return redirect(request.referrer or url_for(".login"))
@authbp.route('/register', methods=['POST', 'GET'])
@limiter.limit("30 per minute")
@dontallowiflogged
def register():
    if request.method=="POST":
        name=request.form.get('name') or''
        name=name.strip()
        email=request.form.get('email').lower().strip() or ''
        channelname=request.form.get('cname') or''
        channeldesc=request.form.get("cdesc") or ''
        prevurl=request.form.get('prevurl') 
        if not channeldesc:
            channeldesc=f"This channel is created by {name} on {datetime.now().date()}.**** Auto generated ****"
        if not channelname:
            channelname=name
        password=request.form.get('password') or ''
        if len(name)<10 or len(name)>50 or len(email)<3 or len(email)>100 or len(password)<10 or len(password)>100:
            flash("Invalid input data" if not len(password)>100 else "Enter shorter password",error)
            return redirect(url_for('.register'))
        if channeldesc and len(channeldesc)<10 or len(channeldesc)>500:
            flash("Invalid input data" ,error)
            return redirect(url_for('.register'))            
        file=request.files.get('file')
        if not checkfilesize(file,4):
            return redirect(url_for('.register'))        
        autologin=request.form.get('autologin')
        is_exists = currentdb.query(select(users).where(users.email == email).exists()).scalar()
        if is_exists:
            flash(f"A user with that email already exists <a href='{url_for('.login')}?email={email}' class='text-primary fw-bold'>Click here to login<i class='fas text-primary  fa-external-link-alt'></i></a>" , error)
            return redirect(url_for('.register'))
        xv=savetopc(file,True) if file is not None and file.filename!="" else defname
        new_user=users(name=name,password=generate_password_hash(password),email=email,created=datetime.now(),profilephoto=xv)
        try:
            currentdb.add(new_user)
            currentdb.commit()
            newchannel=channels(created=datetime.now(),channeldesc=channeldesc,channelname=channelname,user_id=new_user.id,channelicon=defname,channelbanner=defbanner)
            currentdb.add(newchannel)
            newob=playlists(user_id=new_user.id,name="Watch Later",description="Auto generated,\nStore videos to watch later",thumbnail=defbanner,display=False)
            currentdb.add(newob)
            currentdb.commit()
            emailadder(email)
            addnotification(new_user.id,f"Welcome to Yt hub {new_user.name}!","Greetings!")            
            if autologin:
                newtoken=str(uuid.uuid4())
                new_user.token=newtoken
                currentdb.commit()
                mainlogin(new_user.id)
                g.user=new_user
                flash("User added and logged in" ,success)
                return redirect(f'{prevurl}' or url_for('index'))
            else:
                flash("User added successfully" ,success)
                return redirect(url_for('.login'))
        except Exception as e:
            currentdb.rollback()
            flash (f"Something went wrong: {e}" , error)
            return redirect(url_for('.register'))
    return render_template('register.html')
@authbp.route('/logout', methods=["POST"])
def logout():
    if loggedin():
        p=session.get('user_id')
        flash("Logout successfull",success)
        delsession()
        session.modified = True 
        eventlet.sleep(0.1)
        socketio.emit('force_logout', to=f"user_{p}")
        delsession()
        return redirect(url_for('.login'))        
    else:    
        flash('No user has logged in' ,error)
        return redirect(url_for('.login'))