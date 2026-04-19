from imports import *
from collections import Counter
import random
def generateuserprefferedcategoryvids(userid, offset, community_sorting=False, scategory=False, vidid=False):
    now = datetime.now()
    guserobj = g.user
    user_clicks, watch_time = (None, None)
    if guserobj:
        user_clicks = g.user.userclicks or []
        watch_time = g.user.viewduration or {}
    if not scategory and (not user_clicks or not watch_time):
        return False
    seed = session.get("feed_seed")
    if not seed:
        seed = int(datetime.now().strftime("%Y%m%d"))
        session["feed_seed"] = seed
    rng = random.Random(seed)
    total_eligible = currentdb.query(videos.id).join(channels).join(users).filter(
        videos.display == True,
        channels.ischannelenabled == True,
        users.permanentdisabled == False
 ).count()
    basevidquery = (
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
        if total_eligible <= processpower:
            allvids = basevidquery.order_by(videos.created.desc()).limit(processpower).all()
        else:
            base_start = seed % (total_eligible - processpower)
            allvids = basevidquery.order_by(videos.created.desc()).offset(base_start).limit(processpower).all()
    elif not guserobj and scategory:
        allvids = (
            basevidquery
            .filter(videos.id != vidid)
            .order_by(
                case((func.lower(videos.category) == scategory.lower(), 1), else_=0).desc(),
                desc('view_count'), desc('like_count')
            )
            .limit(maxrecommenedvideo)
            .all()
        )
        return allvids
    else:
        if total_eligible <= processpower:
            allvids = (
                basevidquery
                .filter(videos.id != vidid)
                .order_by(videos.created.desc())
                .limit(processpower)
                .all()
            )
        else:
            base_start = seed % (total_eligible - processpower)
            allvids = (
                basevidquery
                .filter(videos.id != vidid)
                .order_by(videos.created.desc())
                .offset(base_start)
                .limit(processpower)
                .all()
            )
    recency = user_clicks[::-1][:3]
    click_count = Counter(user_clicks)
    top_clicks = [x for x, _ in click_count.most_common(3)]
    top_watch = [x for x, _ in sorted(watch_time.items(), key=lambda x: x[1], reverse=True)[:2]]
    scoreboard = {}
    for category in watch_time:
        score = 0
        score += click_count[category] * 2
        score += watch_time[category] * 0.5
        if category in recency: score *= 1.5
        if category in top_clicks: score *= 1.2
        if category in top_watch: score *= 1.3
        scoreboard[category] = round(score, 2)
    if community_sorting:
        total_c = currentdb.query(channels.id).join(users).filter(
            channels.ischannelenabled == True,
            users.permanentdisabled == False
        )  .count() 
        query = (
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
)
            .order_by(desc('sub_count'))
        )
        if total_c <= processpower:
            all_channels = query.limit(processpower).all()
        else:
            c_start = seed % (total_c - processpower)
            all_channels = query.offset(c_start).limit(processpower).all()
        sorted_data = dict(sorted(scoreboard.items(), key=lambda x: x[1], reverse=True))
        c = list(sorted_data.keys())
        def get_channel_rank(wholeobj):
            sub_count, chan, vid_count = wholeobj
            chan_cats = [v.category for v in chan.videos]
            rank = 999
            cs = sub_count
            for index, favorite_cat in enumerate(c):
                if favorite_cat in chan_cats:
                    rank = index * len(chan_cats)
                    if cs > 2: rank -= 20
                    elif cs > 10: rank -= 30
                    rank *= cs**-2 if cs > 1 else -30
                    if cs < 10 and len(chan_cats) > 1: rank -= 30
                    if vid_count > 10 and cs < 20: rank -= 30
                    break
            return (rank, -cs)
        all_channels.sort(key=get_channel_rank)
        return all_channels[offset: offset + maxchannelsperpage + 1]
    videosdict = {}
    if not allvids:
        return False
    for v_count, l_count, video_obj in allvids:
        videosdict[str(video_obj.id)] = [
            v_count,
            video_obj.category,
            video_obj.created.replace(tzinfo=None),
            l_count,
            video_obj.id,
            video_obj
        ]
    totallikesavg = sum(x[3] for x in videosdict.values()) / len(videosdict)
    totalviewssavg = sum(x[0] for x in videosdict.values()) / len(videosdict)
    calc = {}
    for x in videosdict:
        v_data = videosdict[x]
        vid_id = v_data[4]
        global_boost = 0
        if v_data[0] > (totalviewssavg * 4): global_boost = 20
        elif v_data[0] > (totalviewssavg * 2): global_boost = 10
        if v_data[3] > v_data[0]:
            calc[vid_id] = (v_data[3] > v_data[0] * 0.5) + global_boost
            continue
        name = v_data[1]
        age_hours = (now - v_data[2]).total_seconds() / 3600
        if age_hours < 6:
            timescore = max(1, 10 / (3 + age_hours))
        elif age_hours < 24:
            timescore = max(1, 10 / (2 + age_hours))
        elif age_hours < 72:
            timescore = max(1, 10 / (1 + age_hours))
        else:
            timescore = 1
        v_rand = (rng.uniform(0.9, 1.1) if randomizer else 1)
        categoryscore = (scoreboard.get(name, 1.5) + 2)
        likescore = (8 if name in scoreboard else 1.5) * v_rand
        viewscore = (8 if int(v_data[0]) >= totalviewssavg else 2) * v_rand
        extrascore = (4 if name in watch_time else 1)
        if int(v_data[3]) >= totallikesavg:
            likescore += 4
        for y in Counter(scoreboard).most_common(3):
            if name == y[0]:
                viewscore += 2
                break
        calc[vid_id] = categoryscore + likescore + viewscore + timescore + extrascore + global_boost
    sorted_video_ids = [vid_id for vid_id, _ in sorted(calc.items(), key=lambda x: x[1], reverse=True)]
    id_to_tuple = {video_obj.id: (v_count, l_count, video_obj) for v_count, l_count, video_obj in allvids}
    final_sorted_vids = [id_to_tuple[vid_id] for vid_id in sorted_video_ids if vid_id in id_to_tuple]
    if scategory:
        sc = scategory.lower()
        matching = [v for v in final_sorted_vids if v[2].category.lower() == sc]
        non_matching = [v for v in final_sorted_vids if v[2].category.lower() != sc]
        final_sorted_vids = matching[:3] + non_matching +matching[3:]
        return final_sorted_vids[:maxrecommenedvideo]
    start_idx = min(offset, len(final_sorted_vids))
    end_idx = start_idx + maxvideoperpage + 1
    return final_sorted_vids[start_idx:end_idx]