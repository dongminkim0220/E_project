
#############################          Imports         ###########################
from __future__ import unicode_literals



from django.template import loader
from django.utils import timezone
import numpy as np
import threading
from django.http import StreamingHttpResponse
from datetime import datetime
import os
import cv2

from django.shortcuts import render,          redirect
from django.http import HttpResponse

from django.contrib.auth.models import User
from django.contrib import auth

import subprocess
import RPi.GPIO as GPIO
import time
from time import sleep
import sys 

from app1.models import Image



######################################

directory = os.getcwd()
filePath = directory + '/app/templates/resources/images/'


GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)


global panServoAngle
global tiltServoAngle
panServoAngle = 90
tiltServoAngle = 90



#############################          Navigate         ###########################

def home(request):
    
    return render(request, 'home.html')


def main(request):
    
    return render(request, 'main.html')

def pictures(request):
    
    return render(request, 'pictures.html')


def main2(request):
    
    return render(request, 'main2.html')

def login(request):

	if request.method =='POST':
		username = request.POST['username']
		password = request.POST['password1']
		user = auth.authenticate(request, username = username, password = password)
		if user is not None:
				auth.login(request, user)
				return redirect('main2')
		else:
			return render(request, 'home.html', {error : 'wrong password'})
	
	else:
		return render(request, 'home.html')


	return render(request, 'home.html')
	
def logout(request):

	if request.method == 'POST':
		auth.logout(request)
		return redirect('home')
		
	return render(request, 'home.html')


#############################          Wheels         ###########################

class Car(object):
	def __init__(self, LF, LB, RF, RB):
		self.LF = LF
		self.LB = LB
		self.RF = RF
		self.RB = RB
		
	def setup(self):
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(self.LF, GPIO.OUT)
		GPIO.setup(self.RF, GPIO.OUT)
		GPIO.setup(self.LB, GPIO.OUT)
		GPIO.setup(self.RB, GPIO.OUT)
    
	def backward(self, t):
		self.setup()
		GPIO.output(self.LF, GPIO.HIGH)
		GPIO.output(self.RF, GPIO.HIGH)
		time.sleep(t)
		GPIO.output(self.LF, GPIO.LOW)
		GPIO.output(self.RF, GPIO.LOW)
		GPIO.cleanup()

	def forward(self, t):
		self.setup()
		GPIO.output(self.LB, GPIO.HIGH)
		GPIO.output(self.RB, GPIO.HIGH)
		time.sleep(t)  
		GPIO.output(self.LB, GPIO.LOW)
		GPIO.output(self.RB, GPIO.LOW)
		GPIO.cleanup()

	def clockwise(self, t):
		self.setup()
		GPIO.output(self.LF, GPIO.HIGH)
		GPIO.output(self.RB, GPIO.HIGH)
		time.sleep(t)  
		GPIO.output(self.LF, GPIO.LOW)
		GPIO.output(self.RB, GPIO.LOW)
		GPIO.cleanup()

	def counterClockwise(self, t):
		self.setup()
		GPIO.output(self.LB, GPIO.HIGH)
		GPIO.output(self.RF, GPIO.HIGH)
		time.sleep(t)  
		GPIO.output(self.LB, GPIO.LOW)
		GPIO.output(self.RF, GPIO.LOW)
		GPIO.cleanup()


# GPIO Pins
LF = 5 
LB = 6 
RF = 13
RB = 19

# Car
smartCar = Car(LF, LB, RF, RB)


def front(request):
	smartCar.forward(0.25)
	return render(request, 'main2.html')

def back(request):
	smartCar.backward(0.25)
	return render(request, 'main2.html')

def cl_wise(request):
	smartCar.clockwise(0.25)
	return render(request, 'main2.html')

def counter_cl(request):
	smartCar.counterClockwise(0.25)
	return render(request, 'main2.html')

#############################          Servos         ###########################


def setServoAngle(servo, angle):
#	GPIO.cleanup()
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(servo, GPIO.OUT)
	#assert angle >=30 and angle <= 150
	if angle >= 30 and angle <= 150 :
		pwm = GPIO.PWM(servo, 50)
		pwm.start(8)
		dutyCycle = angle / 18. + 3.
		pwm.ChangeDutyCycle(dutyCycle)
		sleep(0.3)
		pwm.stop()
		GPIO.cleanup()
		return''
	else :
		GPIO.cleanup()
		return 'Angle of the motor must be within 30~150'


panPin = 27
tiltPin = 17

def moveServo(servo, angle):
	global panServoAngle
	global tiltServoAngle
	warning = ''
	if angle >= 30 and angle <= 150 :
		if servo == 27 :
			if angle == 1 and panServoAngle < 150:
				panServoAngle = panServoAngle + 10
			elif angle == 0 and panServoAngle > 30:
				panServoAngle = panServoAngle - 10
			warning = setServoAngle(27, panServoAngle)
		elif servo == 17 :
			if angle == 1 and tiltServoAngle < 150 :
				tiltServoAngle = tiltServoAngle + 10
			elif  angle ==0 and tiltServoAngle > 30:
				tiltServoAngle = tiltServoAngle - 10
			warning = setServoAngle(17, tiltServoAngle)
	else:
		warning = 'Angle of the motor must be within 30~150'
	
	return warning




def right(request):
	warning = moveServo(27, 1)
	
	return render(request, 'main2.html', {'panServoAngle' : panServoAngle, 'tiltServoAngle' : tiltServoAngle, 'warning' : warning })

def left(request):
	warning = moveServo(27, 0)
	
	return render(request, 'main2.html', {'panServoAngle' : panServoAngle, 'tiltServoAngle' : tiltServoAngle, 'warning' : warning })

def up(request):
	warning = moveServo(17, 1)
	
	return render(request, 'main2.html', {'panServoAngle' : panServoAngle, 'tiltServoAngle' : tiltServoAngle, 'warning' : warning })
	
def down(request):
	warning = moveServo(17, 0)
	
	return render(request, 'main2.html', {'panServoAngle' : panServoAngle, 'tiltServoAngle' : tiltServoAngle, 'warning' : warning })
	


###################################################################################3


#############################          Camera         ###########################

class VideoCamera(object):
	def __init__(self):
		self.video = cv2.VideoCapture(0)
		(self.grabbed, self.frame) = self.video.read()
		threading.Thread(target=self.update, args=()).start()

	def __del__(self):
		self.video.release()

	def get_frame(self):
		image = self.frame
		ret, jpeg = cv2.imencode('.jpg', image)
		return jpeg.tobytes()		

	def update(self):
		while True:
			(self.grabbed, self.frame) = self.video.read()

	def take_frame(self):
		now = datetime.now()
		fileName = filePath + now.strftime('%y%m%d_%H%M%S') + '.png'
		print (fileName)
		cv2.imwrite(fileName, self.frame)

		db = Image(image_name=now.strftime('%y%m%d_%H%M%S'), pub_date=timezone.now())
		db.save()


cam = VideoCamera()

def gen(camera):
	while True:
		frame = cam.get_frame()
		yield(b'--frame\r\n'
			b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

def stream(request):
	try:
		return StreamingHttpResponse(gen(()), content_type="multipart/x-mixed-replace;boundary=frame")
	except:  # This is bad! replace it with proper handling
		pass



"""
def live(request):
	if request.method == 'POST':
		cam.take_frame()

	return render(request, 'design/html/live.html')

def playback(request):
	image_list = Image.objects.all()
	return render(request, 'design/html/playback.html',
							{'image_list' : image_list})

def playback_show(request, select_image):
	image_list = Image.objects.all()
	return render(request, 'design/html/playback.html',
							{'image_list' : image_list,  'select_image' : select_image})
"""


