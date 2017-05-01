#!/usr/bin/env python
import urllib2, sys, re, cgi
sys.path.append('/home/synapps/python-packages')
import MySQLdb
from dbInfo import DbUserSelect, DbUserSelectPass, DbName, JsonContentHeader
try:
	import json
except ImportError:
	import simplejson as json

# return all entries, grouped by duplicated rows, for today
QuerySelectUserReports = '''SELECT `TimetableID`,`TrainOrder`,`ReportType`, count(*)
FROM `UserReports`
WHERE `Timestamp` >= DATE_ADD(NOW(), INTERVAL -3 HOUR) %s
group by TimetableID, TrainOrder, ReportType'''

WhereClause = '''AND `TimetableID` IN (%s)'''

form = cgi.FieldStorage()
timetableIDs = form.getfirst('timetableIDs', '')
if len(timetableIDs) > 0:
	timetableIDs = json.loads(timetableIDs)
	# todo: deal with exception
db = MySQLdb.connect("localhost",DbUserSelect,DbUserSelectPass,DbName)
cursor = db.cursor()
print '%s\n'%JsonContentHeader

try:
    listFormat = ','.join(['%s'] * len(timetableIDs))
    if listFormat == '':	# get all reports
        cursor.execute(QuerySelectUserReports%listFormat)
    else:
        whereClause = WhereClause%listFormat
        cursor.execute(QuerySelectUserReports%whereClause, tuple(timetableIDs))    
    userReports = cursor.fetchall()
    if userReports is None: userReports = []
    print json.dumps({'userReports': userReports})
except Exception, e:
    print '{"error":"%s"}'%e

db.close()
