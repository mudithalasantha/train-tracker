import urllib2, sys, re
sys.path.insert(0,'/home/synapps/python-packages/')
from BeautifulSoup import BeautifulSoup
#from bs4 import BeautifulSoup
import MySQLdb
from dbInfo import DbUserInsert, DbUserInsertPass, DbName
try:
    import json
except ImportError:
    import simplejson as json
        
from pprint import pprint
import pdb

UnixSocket = "/Applications/XAMPP/xamppfiles/var/mysql/mysql.sock" #local machine

QueryInsertServiceUpdates = 'insert into ServiceUpdates(HasDisruptions) Values(%s)'

QueryGetLatestUpdatesID = '''SELECT ID
    FROM ServiceUpdates
    ORDER BY ID DESC 
    LIMIT 1'''

QueryInsertDisruptionMessage = '''insert into 
    ServiceDisruptionMessages(ServiceUpdateID,TrainLineID,StatusType,Message,TrainWithFirstStopTime,Direction,HasCancelledTrain)
    Values(%s,(SELECT ID FROM `TrainLines` WHERE Name = %s),%s,%s,%s,%s,%s)'''

MetroTrainsURL = 'http://www.metrotrains.com.au/'
#MetroTrainsURL = 'http://www.metrotrains.com.au/healthboard/service-refresh'
ServicesUpdateClass = 'serviceUpdates'
RegexCancellation = re.compile('^([0-9]{1,2}[:.][0-9]{2} ?[ap]m) (.*) bound train has been cancelled')
RegexCancellation2 = re.compile('([012]?[0-9][:.][0-5][0-9]) ?([ap]m)? ([A-Z].*?) ?- ?([A-Z][^,.]*)')
RegexCancellation3 = re.compile('([012]?[0-9][:.][0-5][0-9]) ?([ap]m)? ([A-Z].*?) to ([A-Z][^,.]*)')
#RegexCancellation2 = re.compile('^Cancelled train - ([012]?[0-9]:[0-5][0-9][ap]m)?) (.*) to (.*)')
#RegexCancellation3 = re.compile('^Cancelled trains - ([012]?[0-9]:[0-5][0-9]([ap]m)?) (.*) to ([A-Z][a-z-]*)+.* ([012]?[0-9]:[0-5][0-9]([ap]m)?) (.*) to (.*)\.')
TableHead = '<table id="metro-healthboard-service"'
TableTail = '</table>'

StatusType = ['placeholder', 'good', 'minor', 'major', 'suspended', 'works', 'travel']
StatusIcon = {
    'Good': 'icon-category-good.png',
    'Minor': 'icon-category-minor.png',
    'Major': 'icon-category-major.png',
    'Suspended': 'icon-category-suspended.png',
    'Works': 'icon-category-works.png',
    'Travel': 'icon-category-travel.png'
    }
RegexStatusIcon = re.compile('(icon-category-([tgmsw][a-z]*)\.png)')

def getAllText(s):
    t=''
    if not s: return ''
    elif s.string: return getText(s)
    for i in s:
        t += ' ' + getText(i)
    return t.strip()

def getText(s):
    if not s: return ''
    while not s.string:
        s = s.next
    return str(s.string).strip()
    
def parseMessage(msg, line):
    ''' return (trainStopTime, directionFromCity, isCancelled)'''
    t = RegexCancellation.findall(msg)
    if len(t) == 0:
        t = RegexCancellation2.findall(msg)
        if len(t) == 0:
            t = RegexCancellation3.findall(msg)
            if len(t) == 0:
                return [(None, None, False)]

    result = []
    for infoFound in t:
        if len(infoFound) == 2:
            firstStopTime,direction = infoFound # e.g. ('8:09am', 'Craigieburn')
            fromCity = (direction != 'city') or (line == direction == 'Stony Point')
            firstStopTime = firstStopTime.replace('.', ':').replace(' ', '')
            result.append((firstStopTime, fromCity, True))
        elif len(infoFound) == 4:
            firstStopTime,ampm,fromStation,toStation = infoFound #e.g. ('5:17', 'pm', 'Flinders Street', 'Alamein')
            firstStopTime = firstStopTime.replace('.', ':').replace(' ', '')
            fromStation = fromStation.strip()
            toStation = toStation.strip()
            if ampm == '':
                firstStopTime = convertTo12HrTime(firstStopTime)
            else:
                firstStopTime += ampm
            fromCity = (toStation.lower() == line.lower()) or (fromStation.lower().find('flinder') > -1)
            result.append((firstStopTime, fromCity, True))
    return result

def convertTo12HrTime(t):
    hour,minute = t.split(':')
    hour = int(hour)
    ampm = 'am'
    if hour == 0:
        hour = 12
    elif hour == 12:
        ampm = 'pm'
    elif hour > 12:
        hour -= 12
        ampm = 'pm'
    return '%d:%s%s'%(hour,minute,ampm)

def parseStatusType(imgSrc):
    status = RegexStatusIcon.findall(str(imgSrc.img))
    if len(status) == 0:
        return 0
    logo,statusType = status[0]
    return StatusType.index(statusType)

if __name__ == "__main__":
    print 'fetching %s...'%MetroTrainsURL
    content = urllib2.urlopen(MetroTrainsURL).read()

    # HACK for the new MetroTrain website on 22 July 2012
    # string searching for the service updates table
    tableHeadIndex = content.find(TableHead)
    tableTailIndex = content.find(TableTail, tableHeadIndex)+len(TableTail)
    theTable = content[tableHeadIndex:tableTailIndex]

    # NOTE: using eval is dangerous...need to find a better solution
    #theTable = eval(content.split('"data":')[1][:-2])
    
    print 'BeautifulSouping...'
    #bs = BeautifulSoup(content)
    serviceUpdatesTable = BeautifulSoup(theTable)
    # END HACK
    #pdb.set_trace()
    
    #scraping the service status...
    #serviceUpdatesTable = bs.find('table', ServicesUpdateClass)

    # this following line doesn't work, as BeautifulSoup is not able to parse this page correctly
    #serviceUpdatesTable = bs.find('table', {'id':'metro-healthboard-service'})
    
    serviceUpdates = serviceUpdatesTable.tbody.findAll('tr')
    
    #db = MySQLdb.connect("localhost",DbUserInsert,DbUserInsertPass,DbName,unix_socket=UnixSocket)
    db = MySQLdb.connect("localhost",DbUserInsert,DbUserInsertPass,DbName)
    cursor = db.cursor()
    
    try:
        # insert an service update entry
        #hasDisruptions = serviceUpdatesTable.find('div', 'disruptions') != None
        hasDisruptions = serviceUpdatesTable.find('div', 'healthboard-service-hover-wrapper') != None
        assert cursor.execute(QueryInsertServiceUpdates,(hasDisruptions,)) == 1, 'Failed to insert into ServiceUpdates'
        
        # get the ID of the service update entry just inserted
        assert cursor.execute(QueryGetLatestUpdatesID) == 1, 'Failed to get latest ServiceUpdateID'
        serviceUpdateID = cursor.fetchone()[0]
        print 'serviceUpdateID:', serviceUpdateID

        if hasDisruptions is False:
            print 'no disruption'
            db.commit()
            sys.exit(0)

        for serviceUpdate in serviceUpdates:
            tds = serviceUpdate.findAll('td')
            line = getAllText(tds[0])
            statusType = parseStatusType(tds[1])
            statusText = getAllText(tds[2])
            
            # insert disruption messages if any
            if (statusType > 1):
                for updateMsg in tds[-1].findAll('div', 'healthboard-service-update'):
                    msgNode = updateMsg.find('div', 'healthboard-service-update-notice-full')
                    if msgNode == None:
                        msgNode = updateMsg.find('div', 'healthboard-service-update-notice')
                    msg = getAllText(msgNode)
                    print '%s, %s, %s'%(statusType, statusText, msg)
                    parsedMsg = parseMessage(msg,line)
                    for trainFirstStopTime, direction, isTrainCancelled in parsedMsg:
                        query = QueryInsertDisruptionMessage%(serviceUpdateID,line,statusType,msg,trainFirstStopTime,direction,isTrainCancelled)
                        #print query 
                        assert cursor.execute(QueryInsertDisruptionMessage,
                           (serviceUpdateID,line,statusType,msg,trainFirstStopTime,direction,isTrainCancelled)) == 1, 'Insertion failed: %s'%query
        
        db.commit()
    except SystemExit:
	pass
    except Exception, e:
        db.rollback()
        db.close()
        raise e
        
    db.close()
