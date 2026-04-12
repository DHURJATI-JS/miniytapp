from imports import *
from collections import Counter
now=datetime.now()
def generateuserprefferedcategoryvids(userid,offset,community_sorting=False,scategory=False,vidid=False):
    guserobj=g.user
    user_clicks,watch_time=(None,None)
    if guserobj:
        user_clicks = g.user.userclicks or []
        watch_time = g.user.viewduration or {}
    if not scategory and (not user_clicks or not watch_time) :
        return False
    total_count = (
        currentdb.query(func.count(videos.id))
        .filter(
            videos.display == True,
            channels.ischannelenabled == True,
            users.permanentdisabled == False
        ).scalar()
    )
    basevidquery =(
    currentdb.query(
        videos.view_count.label('view_count'),
        videos.like_count.label('like_count'),
        videos
    )
    .join(channels, videos.channel_id == channels.id)
    .join(users, channels.user_id == users.id) 
    .filter(
        videos.display == True,
        channels.ischannelenabled == True,
        users.permanentdisabled == False
    )
    .group_by(videos.id, channels.id, users.id) 
    .options(
        contains_eager(videos.parent_channel),
        contains_eager(videos.parent_channel).contains_eager(channels.owner)
    )
)
    if not scategory:
        random_start = max(0, total_count - processpower)
        allvids = (
    basevidquery
  .order_by(
        desc('like_count'), 
        desc('view_count'), 
        videos.created.desc()
    )    .offset(random_start)
    .limit(processpower)
    .all()
)
    elif not guserobj and scategory:
        allvids = (
            basevidquery
            .filter(videos.id != vidid)
            .order_by(
                case((func.lower(videos.category) == scategory.lower(), 1), else_=0).desc(),
                desc('like_count'), 
                desc('view_count'), 
                videos.created.desc()
            )
            .limit(maxrecommenedvideo)
            .all()
        )
        return allvids
    else:
        random_start = max(0, total_count - processpower)
        allvids = (
    basevidquery
    .filter(videos.id!=vidid)
    .order_by(
        desc('like_count'), 
        desc('view_count'), 
        videos.created.desc()
    )
    .offset(random_start)
    .limit(processpower)
    .all()
)       
    recency = user_clicks[::-1][:3]
    click_count = Counter(user_clicks)
    top_clicks = [x for x,_ in click_count.most_common(3)]
    top_watch = [x for x,_ in sorted(watch_time.items(), key=lambda x: x[1], reverse=True)[:2]]
    scoreboard = {}
    for category in watch_time:
        score = 0
        score += click_count[category] * 2
        score += watch_time[category] * 0.5
        if category in recency:
            score *= 1.5
        if category in top_clicks:
            score *= 1.2
        if category in top_watch:
            score *= 1.3
        scoreboard[category] = round(score, 2)
    if community_sorting:
        total_ccount =(
    currentdb.query(func.count(distinct(channels.id))) 
    .join(users, channels.user_id == users.id)
    .join(videos, videos.channel_id == channels.id) 
    .filter(
        channels.ischannelenabled == True,
        users.permanentdisabled == False,
        videos.display == True
    )
    .scalar() or 0
)
        rst = max(0, total_ccount - processpower)
        all_channels =(
    currentdb.query(
        channels.sub_count.label('sub_count'), 
        channels,
        func.count(distinct(videos.id)).label('video_count')
    )
    .join(users, channels.user_id == users.id)
    .outerjoin(videos, channels.id == videos.channel_id) 
    .filter(
        channels.ischannelenabled == True,
        users.permanentdisabled == False,
        channels.user_id != session.get('user_id')
    )
    .group_by(channels.id, users.id) 
    .options(
         contains_eager(channels.owner), 
        selectinload(channels.videos) 
    ).order_by(
        desc('sub_count'),      
        channels.created.desc(),
        desc('video_count')     
    )
    .offset(rst)
    .limit(processpower)
    .all()
)
        sorted_data = dict(sorted(scoreboard.items(), key=lambda x: x[1], reverse=True))
        c = list(sorted_data.keys())
        def get_channel_rank(wholeobj):
            sub_count, chan,vid_count = wholeobj
            chan_cats = [v.category for v in chan.videos]
            rank = 999
            cs=sub_count
            for index, favorite_cat in enumerate(c):
                if favorite_cat in chan_cats:
                    rank = index*len(chan_cats)
                    if cs>2:
                        rank +=20
                    elif cs>10:
                        rank +=30    
                    rank*=cs**2 if cs>1 else +30
                    if cs< 10 and len(chan_cats)>1:
                        rank+=30
                    if vid_count>10 and cs<20:
                        rank+=30
                    break
            return (rank, -cs) 
        all_channels.sort(key=get_channel_rank)
        start = offset
        end = offset + maxchannelsperpage
        paginated_channels = all_channels[start : end + 1]
        return paginated_channels 
    videosdict={}    
    if not allvids:
        return False
    for v_count, l_count, video_obj in allvids :
            videosdict[video_obj.name] = [
                v_count, 
                video_obj.category, 
                video_obj.created.replace(tzinfo=None), 
                l_count, 
                video_obj.id,
                video_obj
            ]
    # videosdict={
    # "name":[11,"music",datetime.now(),11,id]}   
    totallikesavg=sum(x[3] for x in videosdict.values())/2
    totalviewssavg=sum(x[0] for x in videosdict.values())/2
    calc={}    
    for x in videosdict:
        if videosdict[x][3]>videosdict[x][0]:
            calc[videosdict[x][4]]=videosdict[x][3]*videosdict[x][0]
            continue
        name=videosdict[str(x)][1]
        age_hours = (now - videosdict[x][2]).total_seconds() / 3600
        if age_hours < 6:
            timescore = max(1, 10 / (3 + age_hours))
        elif age_hours < 24 and age_hours>6:
            timescore = max(1, 10 / (2 + age_hours))
        elif age_hours < 72 and age_hours>24:
            timescore = max(1, 10 / (1 + age_hours))
        else:
            timescore = 1
        categoryscore=scoreboard[name]+2 if name in scoreboard else 1.5
        likescore=2 if name in scoreboard else 1.5
        viewscore=5 if int(videosdict[x][0])>=totalviewssavg else 2
        extrascore=4 if name in watch_time else 1
        if int(videosdict[x][3])>=totallikesavg:
            likescore+=2
        for y in Counter(scoreboard).most_common(3):
            v,_=y
            if name==v:
                viewscore+=2
                break
        totalscore=categoryscore+likescore+viewscore+timescore+extrascore        
        i=videosdict[x][4]
        calc[i]=int(totalscore)
    sorted_video_ids = [vid_id for vid_id, score in sorted(calc.items(), key=lambda x: x[1], reverse=True)]
    id_to_tuple = {v[2].id: v for v in allvids} 
    final_sorted_vids = [id_to_tuple[vid_id] for vid_id in sorted_video_ids if vid_id in id_to_tuple]
    if scategory:
        final_sorted_vids.sort(key=lambda x: x[2].category.lower() == scategory.lower(), reverse=True)
        return final_sorted_vids[:maxrecommenedvideo]
    start = offset if offset else 0
    end = start + maxvideoperpage
    return final_sorted_vids[start : end + 1]
