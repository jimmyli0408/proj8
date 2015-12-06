import sys
import pymongo
import CONFIG
import arrow
from bson import ObjectId

try:
    client = pymongo.MongoClient(CONFIG.MONGO_URL)
    coll = client['meeting']['proposal'];
except Exception as ex:
    print ('Connect mongodb failed %s' % ex)
    sys.exit()

def add_proposal(begin, end):
    coll.insert({'begin':begin, 'end': end})

def list_proposal():
    cursor = coll.find({})
    proposals = []
    for record in cursor:
        proposals.append({
            'id': '%s' % record['_id'],
            'begin': '%s' % arrow.get(record['begin']).format('MM/DD/YYYY HH:mm'),
            'end': '%s' % arrow.get(record['end']).format('MM/DD/YYYY HH:mm'),
        })
    return proposals

def delete_proposal(key):
    coll.remove({'_id': ObjectId(key)})

def get_proposal(key):
    cursor = coll.find({'_id': ObjectId(key)})
    for record in cursor:
        return record
    return None
