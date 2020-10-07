#TODO: try KCF, CSRT and MedianFlow Tracker to determine which is better for this specific application
from imutils.video import VideoStream
from imutils.video import FPS
import imutils
import argparse
import time
import cv2
import numpy as np

#Take command line arguments
ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video", type=str, help="video file path")
ap.add_argument("-t", "--tracker", type=str, default="kcf", help="kcf, csrt or medianflow")
args = vars(ap.parse_args())

#dictionary of trackers to be tested
trackers = {
	"kcf": cv2.TrackerKCF_create,
	"csrt": cv2.TrackerCSRT_create, #best results so far are with csrt
	"medianflow": cv2.TrackerMedianFlow_create
}

tracker = trackers[args["tracker"]]()

initBounding = None

if not args.get("video", False):
	vidStream = VideoStream(src=0).start()
	time.sleep(1.0)

else:
	vidStream = cv2.VideoCapture(args["video"])

fps = None

#These variables are used to trace the lines over the frame to visualize the bar paths
x1 = 0
y1 = 0
canvas = None

#While loop to operate frame by frame
while True:
	frame = vidStream.read()
	frame = frame[1] if args.get("video", False) else frame

	#this is only occurs for video clips
	if frame is None:
		break

	#For some reason .mov files need to be rotated so uncomment if using .mov
	#if args.get("video", False):
	#	frame = imutils.rotate(frame, 180)

	#reduce the size to speed up processing
	frame = imutils.resize(frame, width=500)
	height, width = frame.shape[:2]

	#Only executed once the roi has been selected
	if initBounding is not None:
		#use the tracker
		success, box = tracker.update(frame)

		if success:
			#logic to create "line" connecting previous point to current point
			if canvas is None:
				canvas = np.zeros_like(frame)
			x, y, w, h = [int(v) for v in box]
			#bounding box around the object of interest (barbell/dumbell)
			cv2.rectangle(frame, (x,y), (x+w, y+h), (0,255,0), 2)
			
			x2 = (int)(x+w/2)
			y2 = (int)(y+h/2)
			if x1 == 0 and y1 == 0:
				x1,y1= x2,y2
			else:
				canvas = cv2.line(canvas, (x1, y1), (x2,y2), [255,255,255], 2)
			x1,y1 = x2,y2
			#Overlays bar path over the video frame
			frame = cv2.add(frame,canvas)

		#Used for fps calculations
		fps.update()
		fps.stop()

		#Info to overlay on the frame
		info = [
			("Tracker", args["tracker"]),
			("Success", "Yes" if success else "No"),
			("FPS", "{:.2f}".format(fps.fps()))
		]
		#Overlay above info onto the frame
		for (i, (k,v)) in enumerate(info):
			text = "{}: {}".format(k, v)
			cv2.putText(frame, text, (10, height - ((i*20) + 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
	#display the frame
	cv2.imshow("Frame", frame)


	key = cv2.waitKey(1) & 0xFF
	#Use s key to select the roi
	if key == ord("s"):
		initBounding = cv2.selectROI("Frame", frame, fromCenter=False, showCrosshair=True)
		tracker.init(frame, initBounding)
		fps = FPS().start()
	#Use q key to exit the program
	elif key == ord("q"):
		break
#End the video or webcam stream accordingly
if not args.get("video", False):
	vidStream.stop()
else:
	vidStream.release()
#Close the display windows
cv2.destroyAllWindows()
