# import the necessary packages
from picamera.array import PiRGBArray
from camera import CameraGPIO
from threading import Thread
import cv2

class PiVideoStream:
	def __init__(self, resolution=(320, 240), framerate=32, **kwargs):
		# initialize the camera
		self.camera = CameraGPIO()

		# set camera parameters
		self.camera.resolution = resolution
		self.camera.framerate = framerate

		# set optional camera parameters (refer to PiCamera docs)
		for (arg, value) in kwargs.items():
			setattr(self.camera, arg, value)

		# initialize the stream
		self.rawCapture = PiRGBArray(self.camera, size=resolution)
		self.stream = self.camera.capture_continuous(self.rawCapture,
			format="bgr", use_video_port=True)

		# initialize the frame and the variable used to indicate
		# if the thread should be stopped
		self.frame = None
		self.stopped = False
		
		self.hasGotten = False
		
	def start(self):
		# start the thread to read frames from the video stream
		t = Thread(target=self.update, args=())
		t.daemon = True
		t.start()
		return self

	def update(self):
		# keep looping infinitely until the thread is stopped
		for f in self.stream:
			# grab the frame from the stream and clear the stream in
			# preparation for the next frame
			self.frame = f.array
			self.rawCapture.truncate(0)
			self.hasGotten = False

			# if the thread indicator variable is set, stop the thread
			# and resource camera resources
			if self.stopped:
				self.stream.close()
				self.rawCapture.close()
				self.camera.close()
				return

	def read(self):
		# return the frame most recently read
		self.hasGotten = True
		return self.frame
	    
	def getFramerate(self):
                return self.camera.getFramerate()

	def stop(self):
		# indicate that the thread should be stopped
		self.stopped = True
