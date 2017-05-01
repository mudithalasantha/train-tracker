#!/usr/bin/env python
import urllib2, sys, re, cgi
sys.path.append('/home/synapps/python-packages')
import MySQLdb
from dbInfo import DbUserInsert, DbUserInsertPass, DbName, JsonContentHeader
try:
    import json
except ImportError:
    import simplejson as json
#import cgitb; cgitb.enable()

QueryInsertUserReport = '''INSERT INTO `UserReports` (`TimetableID`,`TrainOrder`,`ReportType`)
VALUES (%s, %s, %s)'''

print '%s\n'%JsonContentHeader

form = cgi.FieldStorage()
userReport = form.getfirst('userReport', '')
if len(userReport) == 0:
    print json.dumps({'userReportUpdateResponse':0})
    sys.exit(0)

try:
    db = MySQLdb.connect("localhost",DbUserInsert,DbUserInsertPass,DbName)
    cursor = db.cursor()
    userReport = json.loads(userReport)
    rowChanged = cursor.execute(QueryInsertUserReport, tuple(userReport))
    print json.dumps({'userReportUpdateResponse':rowChanged})
    db.commit()
except Exception, e:
    print '{"error":"%s"}'%e
    db.rollback()

db.close()
