from imports import *
def grpvids(allvids):    
    allvids=allvids
    if not allvids:
        flash("No videos found",error)
        return ()
    channel_ids = [v[2].channel_id for v in allvids]
    counts = Counter(channel_ids)
    groupedvids={}
    for channelid, count in counts.items():
        if count >= 2:
            cobj=currentdb.get(channels,channelid)
            groupedvids[channelid]={
                "allvideos":[obj for obj in allvids if obj[2].channel_id==channelid],
                "sub_count":cobj.sub_count,
                "channelobj":cobj
            }
            allvids[:] = [obj for obj in allvids if obj[2].channel_id != channelid]
    sorted_groupedvids = dict(sorted(
        groupedvids.items(), 
        key=lambda x: x[1]["sub_count"],
        reverse=True  
    ))  
    return (sorted_groupedvids,allvids)    