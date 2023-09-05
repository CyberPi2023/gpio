#-*- coding=utf-8 -*-

import os
import argparse
import cv2
import numpy as np
import sys
import time
from threading import Thread
import importlib.util
from utils.logger import Logger
LOG = Logger(__file__)

def read_args():
# Usage:
    parser = argparse.ArgumentParser()
    parser.add_argument('--modeldir', help='Folder the .tflite file is located in', required=False)
    parser.add_argument('--graph', help='Name of the .tflite file, if different than detect.tflite',
                        default='detect.tflite')
    parser.add_argument('--labels', help='Name of the labelmap file, if different than labelmap.txt',
                        default='labelmap.txt')
    parser.add_argument('--threshold', help='Minimum confidence threshold for displaying detected objects',
                        default=0.5)
    parser.add_argument('--resolution', help='Desired webcam resolution in WxH. If the webcam does not support the resolution entered, errors may occur.',
                        default='1280x720')
    parser.add_argument('--edgetpu', help='Use Coral Edge TPU Accelerator to speed up detection',
                        action='store_true')
    return parser.parse_args()

# Define VideoStream class to handle streaming of video from webcam in separate processing thread
# Source - Adrian Rosebrock, PyImageSearch: https://www.pyimagesearch.com/2015/12/28/increasing-raspberry-pi-fps-with-python-and-opencv/
class VideoStream:
    """Camera object that controls video streaming from the Picamera"""
    def __init__(self,resolution=(640,480),framerate=30):
        # Initialize the PiCamera and the camera image stream
        self.stream = cv2.VideoCapture(0)
        ret = self.stream.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        ret = self.stream.set(3,resolution[0])
        ret = self.stream.set(4,resolution[1])

        # Read first frame from the stream
        (self.grabbed, self.frame) = self.stream.read()

	# Variable to control when the camera is stopped
        self.stopped = False

    def start(self):
	# Start the thread that reads frames from the video stream
        Thread(target=self.update,args=()).start()
        return self

    def update(self):
        # Keep looping indefinitely until the thread is stopped
        while True:
            # If the camera is stopped, stop the thread
            if self.stopped:
                # Close camera resources
                self.stream.release()
                return

            # Otherwise, grab the next frame from the stream
            (self.grabbed, self.frame) = self.stream.read()

    def read(self):
	# Return the most recent frame
        return self.frame

    def stop(self):
	# Indicate that the camera and thread should be stopped
        self.stopped = True

class Recognizer(object):
    def __init__(self, modeldir=None, graph="detect.tflite", labels="labelmap.txt", threshold=0.5, resolution="1280x720", use_TPU=False):
        root_dir = os.path.dirname(os.path.realpath(__file__))
        model_dir = os.path.join(root_dir, 'myModel')
        self.model_dir = model_dir if modeldir is None else modeldir
        self.graph_name = graph
        self.label_map = labels
        self.min_conf_threshold = threshold
        resolution_w, resolution_h = resolution.split('x')
        self.image_w = int(resolution_w)
        self.image_h = int(resolution_h)
        self.use_TPU = use_TPU
        pkg = importlib.util.find_spec('tflite_runtime')
        if pkg:
            LOG.info("tflite_runtime")
            from tflite_runtime.interpreter import Interpreter
            if self.use_TPU:
                from tflite_runtime.interpreter import load_delegate
        else:
            LOG.info('tensorflow.lite.python.interpreter')
            from tensorflow.lite.python.interpreter import Interpreter
            if self.use_TPU:
                from tensorflow.lite.python.interpreter import load_delegate
        if self.use_TPU:
            # If user has specified the name of the .tflite file, use that name, otherwise use default 'edgetpu.tflite'
            if (self.graph_name == 'detect.tflite'):
                self.graph_name = 'edgetpu.tflite'
        self.ckpt_path = os.path.join(self.model_dir, self.graph_name)
        self.labels_path = os.path.join(self.model_dir, self.label_map)
        self.labels = None
        with open(self.labels_path, 'r') as f:
            self.labels = [line.strip() for line in f.readlines()]
        if self.labels[0] == '???':
            del(self.labels[0])
        if self.use_TPU:
            LOG.info("self.useTPU:{}".format(self.use_TPU))
            LOG.info("self.interpreter = Interpreter(model_path=self.ckpt_path, experimental_delegates=[load_delegate('libedgetpu.so.1.0')])")
            self.interpreter = Interpreter(model_path=self.ckpt_path, experimental_delegates=[load_delegate('libedgetpu.so.1.0')])
        else:
            LOG.info("self.useTPU:{}".format(self.use_TPU))
            LOG.info("self.interpreter = Interpreter(model_path=self.ckpt_path)")
            self.interpreter = Interpreter(model_path=self.ckpt_path)

        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        self.height = self.input_details[0]['shape'][1]
        self.width = self.input_details[0]['shape'][2]

        self.floating_model = (self.input_details[0]['dtype'] == np.float32)

        self.input_mean = 127.5
        self.input_std = 127.5

        # Check output layer name to determine if this model was created with TF2 or TF1,
        # because outputs are ordered differently for TF2 and TF1 models
        outname = self.output_details[0]['name']

        if ('StatefulPartitionedCall' in outname): # This is a TF2 model
            self.boxes_idx, self.classes_idx, self.scores_idx = 1, 3, 0
        else: # This is a TF1 model
            self.boxes_idx, self.classes_idx, self.scores_idx = 0, 1, 2

        # Initialize frame rate calculation
        self.frame_rate_calc = 1
        self.freq = cv2.getTickFrequency()

        # Initialize video stream
        self.videostream = VideoStream(resolution=(self.image_w,self.image_h),framerate=30).start()
        self.log_properties()

    def log_properties(self):
        LOG.info(self.__dict__)

    def recognize(self):
        LOG.info("Recognize Result:")
# Start timer (for calculating frame rate)
        t1 = cv2.getTickCount()

        # Grab frame from video stream
        frame1 = self.videostream.read()

        # Acquire frame and resize to expected shape [1xHxWx3]
        frame = frame1.copy()
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_resized = cv2.resize(frame_rgb, (self.width, self.height))
        input_data = np.expand_dims(frame_resized, axis=0)

        # Normalize pixel values if using a floating model (i.e. if model is non-quantized)
        if self.floating_model:
            input_data = (np.float32(input_data) - self.input_mean) / self.input_std

        # Perform the actual detection by running the model with the image as input
        self.interpreter.set_tensor(self.input_details[0]['index'],input_data)
        self.interpreter.invoke()

        # Retrieve detection results
        boxes = self.interpreter.get_tensor(self.output_details[self.boxes_idx]['index'])[0] # Bounding box coordinates of detected objects
        classes = self.interpreter.get_tensor(self.output_details[self.classes_idx]['index'])[0] # Class index of detected objects
        scores = self.interpreter.get_tensor(self.output_details[self.scores_idx]['index'])[0] # Confidence of detected objects

        # Loop over all detections and draw detection box if confidence is above minimum threshold
        for i in range(len(scores)):
            if ((scores[i] > self.min_conf_threshold) and (scores[i] <= 1.0)):

                # Get bounding box coordinates and draw box
                # Interpreter can return coordinates that are outside of image dimensions, need to force them to be within image using max() and min()
                ymin = int(max(1,(boxes[i][0] * self.image_h)))
                xmin = int(max(1,(boxes[i][1] * self.image_w)))
                ymax = int(min(self.image_h,(boxes[i][2] * self.image_h)))
                xmax = int(min(self.image_w,(boxes[i][3] * self.image_w)))

                cv2.rectangle(frame, (xmin,ymin), (xmax,ymax), (10, 255, 0), 2)

                # Draw label
                object_name = self.labels[int(classes[i])] # Look up object name from "labels" array using class index
                label = '%s: %d%%' % (object_name, int(scores[i]*100)) # Example: 'person: 72%'
                labelSize, baseLine = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2) # Get font size
                label_ymin = max(ymin, labelSize[1] + 10) # Make sure not to draw label too close to top of window
                cv2.rectangle(frame, (xmin, label_ymin-labelSize[1]-10), (xmin+labelSize[0], label_ymin+baseLine-10), (255, 255, 255), cv2.FILLED) # Draw white box to put label text in
                cv2.putText(frame, label, (xmin, label_ymin-7), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2) # Draw label text

                LOG.info('%s: %d%%' % (object_name, int(scores[i]*100)))
                self.object_name = object_name
                self.object_score = int(scores[i]*100)

        # Draw framerate in corner of frame
        cv2.putText(frame,'FPS: {0:.2f}'.format(self.frame_rate_calc),(30,50),cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,0),2,cv2.LINE_AA)

        # All the results have been drawn on the frame, so it's time to display it.
        cv2.imshow('Object detector', frame)

        # Calculate framerate
        t2 = cv2.getTickCount()
        time1 = (t2-t1)/self.freq
        self.frame_rate_calc= 1/time1

    def loop(self):
        while True:
            self.recognize()
            # Press 'q' to quit
            if cv2.waitKey(1) == ord('q'):
                break

        # Clean up
        cv2.destroyAllWindows()
        self.videostream.stop()



if __name__ == "__main__":
    args = read_args()
    recognizer = Recognizer(modeldir=args.modeldir,graph=args.graph,labels=args.labels,threshold=float(args.threshold),resolution=args.resolution,use_TPU=args.edgetpu)
    recognizer.loop()
