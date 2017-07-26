from NatNetClient_1Points import NatNetClient
import configparser
import numpy as np
from collections import deque
#import matplotlib.pyplot as plt
from sklearn.metrics.pairwise import euclidean_distances
from scipy.sparse import csr_matrix
from struct import *
import socket  
import time
import pandas as pd
from scipy import stats
from sklearn.metrics.pairwise import manhattan_distances

starttime=time.time()
benchmark = list()
configParser = configparser.ConfigParser(allow_no_value=True)
configParser.read('config.ini')
numFrame = 0
fiveFrames = list()
s = None
xpider_center_connected = False
#slope_list = list()
slope = []
# This is a callback function that gets connected to the NatNet client and called once per mocap frame.
def receiveNewFrame( inMarkerModelName, inMarkerset, markerCount, frameNumber, markerSetCount, unlabeledMarkersCount, rigidBodyCount, skeletonCount,
					labeledMarkerCount, latency, timecode, timecodeSub, timestamp, isRecording, trackedModelsChanged ):
	pass

def receiveRigidBodyFrame( id, position, rotation ):
	pass

def unlabeledMarkerFrame(u_unlabeled):
	
	global print_frame_count, print_object_count, print_data, send_data
	global fiveFrames
	global numFrame
	global slope
	global benchmark
#	robot_data = list()
	if numFrame == 0:
		benchmark = u_unlabeled
	if len(u_unlabeled) > 0:
		relocated = trackPoints(u_unlabeled)
		n_unlabled_markers = np.array(relocated)
	
#	if len(n_unlabled_markers) > 0:
		
#	print(n_unlabled_markers)
		if numFrame%5 == 0 and (len(relocated)>0):
			fiveFrames.append(relocated)
		numFrame = numFrame + 1
		
		if numFrame == 30:
#			print(fiveFrames)
			slope = regression(fiveFrames)
			slope = np.array(slope)		
			numFrame = 0;
			fiveFrames = list()

		if len(slope) == 0:
			slope = [0] * n_unlabled_markers.shape[0]
			slope = np.array(slope)

		if len(n_unlabled_markers) == len(slope.reshape(len(slope), 1)):
			
			robot_data = np.concatenate((n_unlabled_markers, slope.reshape(len(slope), 1)), axis=1)
#			print(robot_data)
		
			if print_frame_count:
				countFrame()
			
			if print_object_count:
				print("Obejcts count", len(robot_data), end="\r") 
				
			if print_data:
				print(robot_data)
				
			if send_data:
				if robot_data is not -1:      
					sendSocket(robot_data)
			#        pass
				else:
					pass
					# print("There's no pair\n")

def countFrame():
	global numFrame
	global starttime 
	if numFrame == 0:
		starttime = time.time()
	numFrame = numFrame + 1
	if time.time() - starttime > 1:
		print("Frame Rate:", numFrame, end = '\r')
		numFrame = 0;

def trackPoints(newFrame):

	global benchmark
	newMat = euclidean_distances(benchmark, newFrame)
#	print(newMat)
	distMatrix = csr_matrix(newMat)
	# the max distance between a pair of points 
	#    maxDistance = 0.05
	idx = list()
	for i in range(distMatrix.shape[0]):
		row = distMatrix.getrow(i).toarray()[0].ravel()
		top_indices = row.argsort()[0]
		top_values = row[row.argsort()[0]]
		idx.append(top_indices)	
#	print(idx)
	relocate = list()
	for i in idx:
		relocate.append(newFrame[i])
#	print(relocate)
#	print(euclidean_distances(benchmark, relocate))
	benchmark = relocate
	return relocate
	
def regression(mat):
	slope_list = list()
	df = pd.DataFrame(mat)
	if len(df)==0:
		return False
	else:
		for i in range(df.shape[1]):
			b = df[:][i]
			b = list(zip(*b))
			dataX = list(b[0])
			dataY = list(b[1])
	#		print(dataX)
	#		print(dataY)
	#		benchSlope = arcCosine(dataX, dataY)
			if ((dataY[-1]-dataY[0]) > 1e-3) or ((dataX[-1]-dataX[0]) > 1e-3):		
				benchSlope = np.arctan2((dataY[-1]-dataY[0]), (dataX[-1]-dataX[0]))
				bench_angle = (benchSlope)
		#		print("bench: ", bench_angle)
				slope, intercept, r_value, p_value, std_err = stats.linregress(dataX,dataY)
				computed_angle = np.arctan(slope)	
		#		print("computed: ", computed_angle)
				if abs(bench_angle - computed_angle) > 0.52:
					computed_angle = computed_angle + np.pi
				revised = (computed_angle+np.pi*2)%(np.pi*2)
		#		print("Revised: ", revised)
				slope_list.append(revised)
			else:
				slope_list.append(-10000)
		return slope_list
#		print(slope_list)
	
#def NNeighbor(mat):
#	idx = list()
#	distMatrix = euclidean_distances(mat)
#	distMatrix = csr_matrix(distMatrix)
#	# the max distance between a pair of points 
#	maxDistance = float(configParser.get('positionConfig', 'maxDistance'))
##    maxDistance = 0.05
#	for i in range(distMatrix.shape[0]):
#		row = distMatrix.getrow(i).toarray()[0].ravel()
#		top_indices = row.argsort()[1]
#		top_values = row[row.argsort()[1]]
#		if top_values > maxDistance:
#			idx.append(-1)
#		else:
#			idx.append(top_indices)
#	return idx

def trace( *args ):
	pass 
#    print( "".join(map(str,args)) )

#def compute_Pos_Angle(posData):
##    unlabeled_markers = ([[1, 1, 0.1], [-2, -2, 0.2], [7, 0., 0.1], 
##                         [1, 2, 0.3],[-3, -2, 0.4],[8, 1, 0.2]])
#	unlabeled_markers = posData
#	n_unlabled_markers = np.array(unlabeled_markers)
#
#	trace("raw markers:")
##    trace(n_unlabled_markers[:,0:3])
#	if len(n_unlabled_markers) < 2:
#		return -1
#	else:
#		markers_index = regression(n_unlabled_markers[:,0:2])
#		trace("neighbor markers index:")
#		trace(markers_index)
	


#		# marker_set contains all the pairs of ID collected. 
#		markers_set = [] 
#
#		for i in range(len(markers_index)):
#			if(markers_index[i] > i):
#				markers_set.append([i, markers_index[i]])
#
#		n_markers_set = np.array(markers_set)
#		trace("markers set:")
#		trace(markers_set)
#
#		front_markers_set = list()
#		back_markers_set = list()
#		for i, j in markers_set:
#			if n_unlabled_markers[i][2] > n_unlabled_markers[j][2]:
#				front_markers_set.append(i)
#				back_markers_set.append(j)
#			else:
#				front_markers_set.append(j)
#				back_markers_set.append(i)
#		# print(front_markers)
#
#		back_markers = (n_unlabled_markers[back_markers_set])[:,0:2]
#		front_markers = (n_unlabled_markers[front_markers_set])[:,0:2]
#		trace("back markers:")
#		trace(back_markers)
#		trace("font markers:")
#		trace(front_markers)
#
#		robot_location = (back_markers+front_markers)/2
#		trace("robot location:")
#		trace(robot_location)
#
#		delta_points = front_markers - back_markers
#		robot_theta = (np.arctan2(delta_points[:,1], delta_points[:,0])+np.pi*2) % (np.pi*2)
#		trace("robot theta:")
#		trace(robot_theta)
#
#		trace("robot_data:")
#		robot_data = np.hstack((robot_location, robot_theta.reshape(robot_theta.shape[0],1)))
#		trace(robot_data)
#		if len(robot_data) == 0:
#			return -1 
#		else:                    
#			return robot_data

def sendSocket(pos_angle):
	global xpider_center_connected, s

	if xpider_center_connected == False:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Create a socket object
		host = configParser.get('socketInfo', 'severIP')
		port = int(configParser.get('socketInfo', 'port'))
		try:
			s.connect((host, port))
			xpider_center_connected = True
		except:
			s.close()
			xpider_center_connected = False
			print("Can not connect to XpiderCenter")
	else:
		data = np.random.rand(4,4)
		data = pos_angle
		newString = ''
		for row in data:
			rowString = ",".join(map(str, row))
			newString = newString + rowString + '\r\n'
		newString = newString.encode()
		lenth = len(newString)+6
		# print(lenth)
		lenth = pack('<i',  lenth)
		# print(newString)        
		try:                                    
			header = bytes([0x4a, 0x44, 0x43, 0x43, 0x09]) + lenth
			s.sendall(header)
			s.sendall(newString)  
			# print(newString)                             
		except:
			print("send failed")
			s.close()
			xpider_center_connected = False;

send_data = False
print_data = False
print_frame_count = False
print_object_count = False

if configParser.get('positionConfig', 'printFramesCount') == "True":
	print_frame_count = True;

if configParser.get('positionConfig', 'printObejctsCount') == "True":
	print_object_count = True;
	
if configParser.get('positionConfig', 'printData') == "True":
	print_data = True;
	
if configParser.get('positionConfig', 'sendSocket') == "True":
	send_data = True;
	
# This will create a new NatNet client
streamingClient = NatNetClient()

# Configure the streaming client to call our rigid body handler on the emulator to send data out.
streamingClient.newFrameListener = receiveNewFrame
streamingClient.rigidBodyListener = receiveRigidBodyFrame
streamingClient.unlabeledMarkerListener = unlabeledMarkerFrame
# Start up the streaming client now that the callbacks are set up.
# This will run perpetually, and operate on a separate thread.

streamingClient.run()
#ani = animation.FuncAnimation(fig, update, interval=100)
#plt.show()
