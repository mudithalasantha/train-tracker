#!/usr/bin/env python
import urllib2, sys, re, cgi
sys.path.append('/home/synapps/python-packages')
import MySQLdb
from dbInfo import DbUserSelect, DbUserSelectPass, DbName, JsonContentHeader
try:
	import json
except ImportError:
	import simplejson as json

import cgitb; cgitb.enable()
from pprint import pprint
import pdb

QuerySelectStatus = '''select TL.Name, SDM.TrainWithFirstStopTime, SDM.Direction, SDM.HasCancelledTrain, SDM.Message 
from ServiceDisruptionMessages as SDM, 
	TrainLines as TL join 
	(select * from ServiceUpdates Order by ID desc limit 1) as SU
where SU.ID = SDM.ServiceUpdateID and SDM.TrainLineID = TL.ID and TL.Name like %s
'''

form = cgi.FieldStorage()
trainLine = form.getfirst('trainLine', '%')
db = MySQLdb.connect("localhost",DbUserSelect,DbUserSelectPass,DbName)
cursor = db.cursor()
print '%s\n'%JsonContentHeader

try:
    cursor.execute(QuerySelectStatus, trainLine)
    status = cursor.fetchall()
    if status is None: status = []
    statusObj = {}
    statusObj['statusMessages'] = status
    print json.dumps(statusObj)
except Exception, e:
    print '{"error":"%s"}'%e

db.close()
