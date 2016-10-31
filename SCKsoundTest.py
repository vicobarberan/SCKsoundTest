import serial, sys, glob, time, datetime, os, shutil
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation


def serial_ports():
    """Lists serial ports

    :raises EnvironmentError:
        On unsupported or unknown platforms
    :returns:
        A list of available serial ports
    """
    if sys.platform.startswith('win'):
        ports = ['COM' + str(i + 1) for i in range(256)]

    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this is to exclude your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')

    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')

    else:
        raise EnvironmentError('Unsupported platform')

    result = []

    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result
class SCKsensor:
	def __init__(self, name, unit, decNum, color, displayPlot=True, displayText=True, keys=[], logValue=True):
		"""
		sensor object
		properties:
			name: the name of the sensor
			data: sensor readings
			unit: the unit of the value
			decNum: number of decimals displayed
		"""
		self.name = name
		self.unit = unit
		self.decNum = decNum
		self.color = color
		self.displayPlot = displayPlot
		self.displayText = displayText
		self.keys = keys
		self.logValue = logValue
		self.dataSet = []
	

#####################################################################
# Sensor data definition 
# Edit here your sensors.
# SCKSensor("Name", "unit", decimalDigits, "color", displayPlot=True, displayText=True, logValue=True, keys=['a', 'b', 'ctrl+e'])
sensors = [	
	SCKsensor("Sound filtered", "mv", 2, "blue"), 
	SCKsensor("Sound RAW", "mv", 2, "purple", displayPlot=False),
	SCKsensor("Gain", "x", 2, "green", displayPlot=False),
	SCKsensor("Resistor 6", "ohms", 0, "orange", displayPlot=False, keys=['4', '5']),
	SCKsensor("Resistor 7", "ohms", 0, "grey", displayPlot=False, keys=['8', '9']),
	SCKsensor("Sampling", "ms", 0, "red", displayPlot=False, keys=['1', '2'], logValue=False)
]
#####################################################################

# BEHAVIOUR VARIABLES
sampleNumber = 1000
minPlot = 0;
manualY = False;
lastManualY = False;
maxY = 100;

# serial port variables
port = serial.Serial(serial_ports()[0], 230400)
serialLine = ""

# Variables related to data text display
textRefreshTime = 0.5		# seconds
textTimer = time.time()
TextAverageCounter = 0


# Prepare datasets with empty values
for sensor in sensors:
	for n in range(sampleNumber):
		sensor.dataSet.append(0)


def numerito(num):
	if num < 10: return '0' + str(num)
	elif num < 100: return str(num) 

def backUpCSV():
	#move old logFiles to BAK
	if not os.path.exists("./BAK"): os.mkdir("BAK")
	for f in os.listdir('.'):
		if ".csv" in f:
			backupName = "./BAK/"+f
			#if backup file exists adds a final secuencial number
			if os.path.exists(backupName):
				num = 1
				backupName += numerito(num)
				while os.path.exists(backupName):
					num += 1
					backupName = backupName[:-2] + numerito(num)
				for i in range(num,1,-1):
					shutil.move("./BAK/"+f+numerito(i-1), "./BAK/"+f+numerito(i))
				shutil.move("./BAK/"+f, "./BAK/"+f+"01")
			shutil.move(f, "./BAK/"+f)
				
backUpCSV()

# Create csv file with headers
logFileName = datetime.datetime.now().strftime("%Y-%m-%d-%H:%M") + "_" + serial_ports()[0].split('/')[2] + '.csv'
if not os.path.exists(logFileName):
	logFile = open(logFileName, 'w')
	#writes header
	line2Write = "timestamp"
	for sensor in sensors:
		if sensor.logValue:
			line2Write = line2Write + "," + sensor.name
	line2Write = line2Write + "\n"
	logFile.write(line2Write)
	logFile.close()
else:
	print "Log file already exists!!!  bye"
	sys.exit()

def logCSV(data):
	
	toWrite = datetime.datetime.now().strftime("%Y/%m/%d-%H:%M:%S.") + str(int(datetime.datetime.now().strftime("%f"))/1000)
	for val in data:
		toWrite = toWrite + "," + val
	toWrite = toWrite + '\n'

	logFile = open(logFileName, 'a')
	logFile.write(toWrite)
	logFile.close()

# Setup matplotlib
matplotlib.rcParams['toolbar'] = 'None'         #removes ugly toolbar
fig = plt.figure(figsize=(18,8), facecolor='white')
ax = fig.add_subplot(111)
dataFont =  matplotlib.font_manager.FontProperties(weight='normal', size=14)

# Data to be plotted
lines = []
texts = []
keys = []
i = 0
for sensor in sensors:
	if sensor.displayPlot:
		sensor.plot = plt.plot(sensor.dataSet, color=sensor.color, antialiased=True, animated=True, linewidth=0.5, zorder=i, alpha=0.9)
		lines.append(sensor.plot[0])
	if sensor.displayText:
		sensor.text = plt.text(0.01, 0.98 - (0.04*i), '0', color=sensor.color, verticalalignment='top', horizontalalignment='left', fontproperties=dataFont, alpha=0.9, transform=ax.transAxes)
		texts.append(sensor.text)
	for k in sensor.keys:
		keys.append(k)
	i = i + 1

# Manual or automatic Y axis scale
sText = plt.text(0.01, 0.01, 'Automatic Y axis scale [m]', color='black', horizontalalignment='left', fontproperties=dataFont, alpha=0.9, transform=ax.transAxes)
texts.append(sText)

# Text showing log file
logText = plt.text(0.99, 0.01, logFileName, color='black', horizontalalignment='right', fontproperties=dataFont, alpha=0.9, transform=ax.transAxes)
texts.append(logText)

# ax.get_yaxis().set_ticks([])					# Removes numbers in Y axis ticks
plt.ylim([minPlot, maxY * 1.15])				# Defines the limits in y axis
fig.tight_layout()								# Eliminates extra space


def remapVertical(dataSet):
	in_max = max(dataSet)
	in_min = min(dataSet)
	newList = []
	if (in_max - in_min) != 0:
		for val in dataSet:
			newList.append((((float(val) - in_min) * (maxY - minPlot))/(in_max - in_min)) + minPlot)
	else:
		return dataSet
	return newList

def animate(ix):
	global textTimer
	global manualY
	global serialLine
	global TextAverageCounter

	if time.time() - textTimer > textRefreshTime:
		updateTextAndLog = True;
		textTimer = time.time()
	else:
		updateTextAndLog = False
		TextAverageCounter = TextAverageCounter + 1
	
	serialLine = port.readline().strip('\t\n\r').split(',')
	valuesToLog = []

	i = 0
	for sensor in sensors:
		sensor.dataSet.pop(0)
		sensor.dataSet.append(float(serialLine[i]))
		if sensor.displayPlot:
			if (manualY):
				sensor.plot[0].set_ydata(sensor.dataSet)
			else:
				sensor.plot[0].set_ydata(remapVertical(sensor.dataSet))
		if sensor.displayText and updateTextAndLog:
			if len(sensor.keys) > 0:
				extraText = ' ['
				nn = 0
				for k in sensor.keys:
					extraText = extraText + k 
					if nn < len(sensor.keys) - 1:
						extraText = extraText + ','
					nn = nn + 1
				extraText = extraText + ']'
			else:
				extraText = ''

			parcialValues  = sensor.dataSet[(-1 * TextAverageCounter):]
			averagedValues = round(sum(parcialValues)/float(len(parcialValues)), sensor.decNum)

			if sensor.decNum == 0:
				formatedValue =  str(int(averagedValues))
			else:
				formatedValue = str(averagedValues)
			sensor.text.set_text("")
			sensor.text.set_text(sensor.name + ":  " + formatedValue + " " + sensor.unit + extraText)
		# if sensor.logValue and updateTextAndLog:
			# valuesToLog.append(str(averagedValues))
		if sensor.logValue:
			valuesToLog.append(str(serialLine[i]))
			
		i = i + 1


	if updateTextAndLog: 
		# logCSV(valuesToLog)
		TextAverageCounter = 0

	logCSV(valuesToLog)

	return lines + texts

ani = animation.FuncAnimation(fig, animate, frames=None, init_func=None, interval=0, blit=True)

def onScroll(event):
	global lastManualY
	global manualY

	for sensor in sensors:
		if len(sensor.keys) > 0:
			mycoords = sensor.text.get_window_extent()
			if event.button == 'down':
				print "down"
				if event.y > mycoords.y0 and event.y < mycoords.y1 and event.x > mycoords.x0 and event.x < mycoords.x1:
					port.write(sensor.keys[0])
					return True
		 	elif event.button == 'up':
		 		print "up"
				if event.y > mycoords.y0 and event.y < mycoords.y1 and event.x > mycoords.x0 and event.x < mycoords.x1:
					port.write(sensor.keys[1])
					return True

	if manualY:
		if event.button == 'down':
			lastManualY = lastManualY - (lastManualY/20)
		elif event.button == 'up':
			lastManualY = lastManualY + (lastManualY/20)
		plt.ylim([minPlot, lastManualY])
		plt.draw()

moo = fig.canvas.mpl_connect('scroll_event', onScroll)

def onKey(event):
	global lastManualY
	global manualY

	if event.key in ['q','escape','ctrl+w','alt+f4']: 
		plt.close('all')
	elif event.key in keys:
		port.write(event.key)
	elif event.key in ['m']:
		manualY = not manualY
		if manualY:
			sText.set_text('Manual Y axis scale [m]')
			if not lastManualY: lastManualY = maxY * 1.15
			plt.ylim([minPlot, lastManualY])
			plt.draw()
		else:
			sText.set_text('Automatic Y axis scale [m]')
			plt.ylim([minPlot, maxY * 1.15])
			plt.draw()
	elif event.key in ['+']:
		if manualY:
			lastManualY = lastManualY + (lastManualY/20)
			plt.ylim([minPlot, lastManualY])
			plt.draw()
	elif event.key in ['-']:
		if manualY:
			lastManualY = lastManualY - (lastManualY/20)
			plt.ylim([minPlot, lastManualY])
			plt.draw()
	else:
		print event.key

cid = fig.canvas.mpl_connect('key_press_event', onKey)

plt.show()

