from flask import Blueprint, render_template
from imports import *
reportbp = Blueprint('reportbp', __name__)
@reportbp.route('/report/<int:id>',methods=['POST','GET'])
@limiter.limit("10 per minute",methods=['POST'])
@requireduserlogin
def report(id):
    userid=session.get('user_id')
    myobj=getuserobj(userid)
    obj=getuserobj(id)
    if not obj:
        flash("User not found",error)
        return redirect(url_for('index'))
    if obj.id==userid:
        flash("Well honest people exist!",success)
        return redirect(url_for('viewprofile', userid=userid))
    if request.method=="POST":
        try:
            if request.method=="POST":
                reason=request.form.get('reason') or ''
                details=request.form.get('details') or ''
                if len(details)<10 or len(details)>500:
                    flash("Invalid input data",error)
                    return redirect(url_for(".report",id=id)) 
                new_report = reports(
                        reporter_id=userid,
                        reported_user_id=obj.id,
                        reason=reason,
                        details=details,
                        status='pending' 
                    )
                currentdb.add(new_report)
                send_email(f"""Hi there {myobj.name}! 
                           The report is under review and we will get back shortly!

                           Thank you
                           {g.appname}
                           """,myobj.email)
                addnotification(userid,f"Reported user:{obj.name}","Report user")
                flash("Reported succesfully",success)
                currentdb.commit()
        except Exception as e:
            currentdb.rollback()
            flash(f"Error: {e}",error)
        return redirect(request.referrer or url_for( '.report',id=id))    
    flash("False reporting may lead to account termination!",error)
    return render_template('report.html',target_user=obj)
@reportbp.route('/view-reports')
@requireduserlogin
def viewreports():
    userid=session.get('user_id')
    obj=getuserobj(userid)
    if obj:
        all_reports=(
    currentdb.query(reports)
    .filter(reports.reporter_id == userid)
    .order_by(reports.created_at.desc())
    .limit(maxreportsperpage)
    .all()
)
        return render_template('view-report.html',reports=all_reports,maxreportsperpage=maxreportsperpage)
    else:
        flash('User not found',error)
        return redirect(url_for('index'))
@reportbp.route('/remove-report/<int:id>',methods=["POST"])
@requireduserlogin
def remove_report(id):
    userid=session.get('user_id')
    obj=currentdb.get(reports,id)
    if not obj.reporter_id==userid:
        flash("You cannot delete someone else's report",error)
        return redirect(url_for('.viewreports' if loggedin() else 'index')) 
    try:        
        currentdb.delete(obj)
        currentdb.commit()
        flash("Report deleted",success)
    except Exception as e:
        currentdb.rollback()
        flash(f'Error: {e}',error)
    return redirect(url_for('.viewreports'))