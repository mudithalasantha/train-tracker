import urllib2, sys
from BeautifulSoup import BeautifulSoup
#from bs4 import BeautifulSoup
from pprint import pprint
import pdb
#from guppy import hpy

STATION_LIST_ONLY = False	# indicate whether to generate a list of all stations only
TimeTableURL = 'http://tt.ptv.vic.gov.au/tt/XSLT_TTB_REQUEST?command=direct&language=en&outputFormat=0&net=vic&line=%(line)s&project=ttb&itdLPxx_selLineDir=%(direction)s&itdLPxx_selWDType=%(type)s&sup=%%20&count=1'
Filename = 'timetable-%(line)s-%(direction)s-%(type)s.csv'
MetroTrainsURL = 'http://www.metrotrains.com.au/'
#DayTypesID = 'ctl00_ContentPlaceHolder1_ctlLayoutContainer_ctl06_ctl00_ctl00_ucTimetableSearch_ddlDay'
DayTypesID = 'edit-day'
#TrainLinesID = 'ctl00_ContentPlaceHolder1_ctlLayoutContainer_ctl06_ctl00_ctl00_ucTimetableSearch_ddlTrainLine'
TrainLinesID = 'edit-line'

allStations = []

TrainLinesHTML = '''<select name="line" class="form-select jquery_dropdown" id="edit-line" style="display: none; "><option value="02ALM">Alamein</option><option value="02BEL">Belgrave</option><option value="02BDM">Craigieburn</option><option value="02CRB">Cranbourne</option><option value="02FKN">Frankston</option><option value="02GLW">Glen Waverley</option><option value="02HBG">Hurstbridge</option><option value="02LIL">Lilydale</option><option value="02PKM">Pakenham</option><option value="02SDM">Sandringham</option><option value="02EPP">South Morang</option><option value="02SPT">Stony Point</option><option value="02SYM">Sydenham</option><option value="02UFD">Upfield</option><option value="02WBE">Werribee</option><option value="02WMN">Williamstown</option></select><option value="02SYM">Sunbury</option>'''

DayTypesHTML = '''<select name="day" class="form-select jquery_dropdown" id="edit-day" style="display: none; "><option value="T0">Mon - Fri</option><option value="T2">Saturday</option><option value="UJ">Sunday</option></select>'''

def getAllText(s):
    t=''
    if not s: return ''
    elif s.string: return getText(s)
    for i in s:
        t += getText(i)
    return t.strip()

def getText(s):
    if not s: return ''
    while not s.string:
        s = s.next
    return str(s.string).strip()

def scrape(url):
	print 'fetching URL content...'
	content = urllib2.urlopen(url).read()
	
	print "bs'ing..."
	bs = BeautifulSoup(content)
	
	# find stations
	ttMargin = bs.find(id="ttMargin")
	stations = [getText(station).strip() for station in ttMargin]
	if STATION_LIST_ONLY:
		allStations.extend([s.split('(')[0] for s in stations])
		return
	#pdb.set_trace()
	#stations = [getAllText(station).split('(')[0] for station in ttMargin]
	#stations = [''.join(station.a.stripped_strings).split('(')[0] for station in ttMargin]
	
	# find times
	ttBody = bs.find(id="ttBody")
	#times = [[time.string.strip() for time in row] for row in ttBody.findAll('div', 'ttBodyTP')]

	times = []
	for row in ttBody.findAll('div', 'ttBodyTP'):
		timesInRow = []
		for time in row:
			timeString = getText(time)
			timeString = timeString and timeString.strip() or ''
			if timeString.find(':') == -1:
				timesInRow.append(timeString)
				continue
			
			hour,minute = timeString.split(':')
			
			# convert to 24-hour format
			if time.find('b') is None:	#AM
				if hour == '12':
					timesInRow.append('0:%s'%(minute))
				else:
					timesInRow.append(timeString)
			else:	#PM
				if hour != '12': hour = int(hour) + 12
				timesInRow.append('%s:%s'%(hour, minute))

		times.append(timesInRow)

	#pdb.set_trace()	
	assert len(times) == len(stations), 'number of stations and times mismatch'
	
	# build timetable: list of tuples
	timetable = []
	i = 0
	for station in stations:
		timetable.append((station.strip(), times[i]))
		i += 1
	
	return timetable
	
def getTimetableTypes(typeNode):
#	return {'Weekdays': 'T0', 'Saturday': 'T2', 'Sunday': 'UJ', 'ANZAC': 'UG'}
	return dict((node.string.replace(' ','').strip(), node['value']) for node in typeNode.findAll('option') if node['value'])

def getLines(linesNode):
    #return dict((node.string.replace(' ',''), node['rel'].strip()) for node in linesNode.findAll('a') if node['rel']
	return dict((node.string.replace(' ','').strip(), node['value'].strip()) for node in linesNode.findAll('option') if node['value'])

def getDirections():
	return {'ToCity': 'H', 'FromCity': 'R'}

def convertToCSV(timetable, filename):
	print 'write to: %s'%filename
	outputFile = open(filename, 'w')
	for row in timetable:
		#print row
		outputFile.write('%s,%s\n'%(row[0], ','.join(row[1])))
	outputFile.close()

if __name__ == "__main__":
	print 'fetching %s...'%MetroTrainsURL
	content = urllib2.urlopen(MetroTrainsURL).read()
	
	print 'BeautifulSouping...'
	bs = BeautifulSoup(content)
	
	trainLines = bs.find(id=TrainLinesID) or BeautifulSoup(TrainLinesHTML)
	dayTypes = bs.find(id=DayTypesID) or BeautifulSoup(DayTypesHTML)

	timetableTypes = getTimetableTypes(dayTypes);
	print 'timetable types: '
	pprint(timetableTypes)
	
	trainLines = getLines(trainLines)
	print 'available lines: '
	pprint(trainLines)
	
	

	# may restrict which train lines to download through command line
	# e.g. MMTScraper.py "Werribee" "Upfield"
	lines = sys.argv[1:]
	print lines
	
	for line in trainLines.iteritems():
		# if certain train lines are given, only run those
		if len(lines) > 0 and line[0] not in lines: continue
		#print hpy().heap()
		
		#pdb.set_trace()
		print line[0]
		for direction in getDirections().iteritems():
			print '\t%s'%direction[0]
			for type in timetableTypes.iteritems():
				args = {'line': line[1], 'direction': direction[1], 'type': type[1]}
				args2 = {'line': line[0], 'direction': direction[0], 'type': type[0]}
				print '\t\t%s'%type[0]
				print '\t\tscraping url:',TimeTableURL%args
				try:
					timetable = scrape(TimeTableURL%args)
					if STATION_LIST_ONLY:
						break
					
					# determine the direction by the first station
					if timetable[0][0].replace(' ', '').find(line[0]) >= 0:
						args2['direction'] = 'ToCity'
					else:
						args2['direction'] = 'FromCity'
					print timetable[0][0], line[0], args2
					
					convertToCSV(timetable, Filename%args2)
				except SystemExit:
					raise
				except KeyboardInterrupt:
					raise
				except:
					print 'FAILED:',args2
					raise
			if STATION_LIST_ONLY:
				break
	if STATION_LIST_ONLY:
		print allStations
		open('stations.csv', 'w').write('\n'.join(allStations))
