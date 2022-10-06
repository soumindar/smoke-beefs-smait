# IMPORT LIBRARY
import serial
import pyrebase
import time
import os
import google.cloud
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import storage
import numpy as np
import math
import cv2
from picamera.array import PiRGBArray
from picamera import PiCamera
import datetime
from datetime import date
import pytz
import pyzbar.pyzbar as pyzbar

# setting serial communication
try:
	ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
	print('Serial Connected')

except:
	print('Serial Connection FAILED')
	exit()
	
# setting firestore communication
cred = credentials.Certificate('/home/pi/Desktop/Sapi/firebase_sdk.json')
try:
	firebase_admin.initialize_app(cred, {
		'storageBucket': 'smokebeefs.appspot.com'
	})
	db = firestore.client()
	doc_ref = db.collection('pengukuran_20211117')
	bucket = storage.bucket()
	print('Firestore Connected')

except:
	print('Firestore Connection FAILED')
	exit()
	
# initialize variables
berat = 0.0
reading_flag = 0
point_flag = 0
shift_left = 1
shift_right = 0.1
count_float = 0

# initialize camera
camera = PiCamera()
camera.awb_mode = 'fluorescent'
camera.rotation = 180

# begin looping
print('Process Started')
while True:
	
	# READ FROM SERIAL
	read = ser.read()
	if read != '':
		reading_flag = 1
		
		if read == '.':
			point_flag = 1
		
		if point_flag == 0:
			berat = berat * shift_left  + int(read)
			shift_left = shift_left *10
		
		if (point_flag == 1) and (read != '.') and (count_float < 2):
			berat = berat + int(read) * shift_right
			shift_right = shift_right * 0.1
			count_float = count_float + 1
		
		berat = round(berat, 2)
		
	# FINISH READING, BEGIN PROCESSING	
	if (reading_flag == 1) and (read == ''):

# ===================================================================================		
		# QR CODE READER
		
#		try:
		# capture image
		camera.start_preview()
		time.sleep(1)
		camera.stop_preview()
		
		camera.capture('image.jpg')
		
		img = cv2.imread('image.jpg')
		
		# get roi
		top_crop = 350
		bottom_crop = 650
		left_crop = 900
		right_crop = 1200
		roi = img[top_crop:bottom_crop, left_crop:right_crop]

		codes = pyzbar.decode(roi)

		for code in codes:
			codeData = str(code.data.decode())	
			
		split_string = codeData.split('-')
		
		cow_id = split_string[0]
		str_born = split_string[1]
		gender = 'MALE' if split_string[2] == 'M' else 'FEMALE'
		
		year_born = int(str_born[:4])
		month_born = int(str_born[4:6])
		date_born = int(str_born[6:8])
		hour_born = 0
		minute_born = 0

		tz = pytz.timezone('Asia/Jakarta')
		dt_born = datetime.datetime(year_born, month_born, date_born, hour_born, minute_born)
		dt_born = tz.localize(dt_born)
		
		dt_now = tz.localize(datetime.datetime.now())
		
		
		str_date_now = date.today().strftime("%Y%m%d")
		img_name = cow_id + '-' + str_date_now
		
		print('ID: ' + cow_id)
		print('Jenis Kelamin: ' + gender)
		print('Tanggal Lahir: ' + str(dt_born))
		print('Tanggal Pengukuran: ' + str(dt_now))
			
#		except:
#			print('QR Code Reader FAILED')
		
# ===================================================================================		
		# COW SIZE ESTIMATION
	
#		try:		
		# get region of interest
		top_crop = 250
		bottom_crop = 950
		left_crop = 600
		right_crop = 1370
		roi = img[top_crop:bottom_crop, left_crop:right_crop]

		# convert to hsv
		hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

		# thresholding
		lower_green = np.array([40,180,40])
		upper_green = np.array([80,255,255])
		mask = cv2.inRange(hsv, lower_green, upper_green)

		mask = cv2.bitwise_not(mask)

		# smoothing
		smoothed = mask
		for i in range(5):
			smoothed = cv2.GaussianBlur(smoothed,(7,7),0)
			ret, smoothed = cv2.threshold(smoothed, 120, 255, cv2.THRESH_BINARY)

		# get roi of legs
		top_crop = 480 
		bottom_crop = 481
		left_crop = 0
		right_crop = 770
		roi_legs = smoothed[top_crop:bottom_crop, left_crop:right_crop][0]

		# get back and front legs
		obj = []
		detected = 0
		index = 0
		empty_section = 0
		right_saved = 0
		for i in range(0, roi_legs.shape[0]):
			if (roi_legs[i] == 255) and (detected == 0):
				detected = 1
				left = i
				obj.append([left])

			if (roi_legs[i] == 0) and (detected == 1):
				if right_saved == 0:
					right_temp = i-1
					right_saved = 1
				empty_section = empty_section + 1

			if empty_section > 30:
				obj[index].append(right_temp)
				detected = 0
				empty_section = 0
				right_saved = 0
				center = (obj[index][0] + obj[index][1]) // 2
				obj[index].append(center)
				index = index + 1
				if obj[index-1][1] - obj[index-1][0] < 40:
					obj.pop()
					index = index - 1

			if (roi_legs[i] == 255) and (detected == 1) and (empty_section < 30):
				empty_section = 0
				right_saved = 0

			if (i == roi_legs.shape[0]-1) and (detected == 1):
				obj[index].append(i)
				center = (obj[index][0] + obj[index][1]) // 2
				obj[index].append(center)
				index = index + 1
				if obj[index-1][1] - obj[index-1][0] < 40:
					obj.pop()

		if index == 3:
			obj.pop(1)

		legs = np.array(obj)

		# get roi back leg
		top_crop = 0
		bottom_crop = 700
		left_crop = legs[1,0]
		right_crop = left_crop + 1
		roi_back_leg = smoothed[top_crop:bottom_crop, left_crop:right_crop]
		roi_back_leg = np.swapaxes(roi_back_leg, 1, 0)[0]

		# get tinggi pinggul
		detected = 0
		obj_section = 0
		empty_section = 0

		for i in range(0, roi_back_leg.shape[0]):
			if (roi_back_leg[i] == 255) and (detected == 0):
				detected = 1
				top = i
				obj_section = obj_section + 1

			if (roi_back_leg[i] == 255) and (detected == 1):
				obj_section = obj_section + 1
				if empty_section > 30:
					if obj_section-empty_section < 200:
						detected = 0
						obj_section = 0
					else:
						break
				empty_section = 0

			if (roi_back_leg[i] == 0) and (detected == 1):
				empty_section = empty_section + 1
				obj_section = obj_section + 1

		detected = 0
		empty_section = 0

		for i in range(roi_back_leg.shape[0]-1, 0, -1):
			if (roi_back_leg[i] == 255) and (detected == 0):
				detected = 1
				bottom = i

			if (roi_back_leg[i] == 255) and (detected == 1):
				if empty_section > 10:
					bottom = i
					break    
				empty_section = 0

			if (roi_back_leg[i] == 0) and (detected == 1):
				empty_section = empty_section + 1

		tinggi_pinggul = bottom - top

		# get roi back of hump
		top_crop = 0
		bottom_crop = 700
		left_crop = legs[0,1]
		right_crop = left_crop + 1
		roi_back_of_hump = smoothed[top_crop:bottom_crop, left_crop:right_crop]
		roi_back_of_hump = np.swapaxes(roi_back_of_hump, 1, 0)[0]

		# get tinggi panggul
		detected = 0
		obj_section = 0
		empty_section = 0

		for i in range(0, roi_back_of_hump.shape[0]):
			if (roi_back_of_hump[i] == 255) and (detected == 0):
				detected = 1
				top2 = i
				obj_section = obj_section + 1

			if (roi_back_of_hump[i] == 255) and (detected == 1):
				obj_section = obj_section + 1
				if empty_section > 30:
					if obj_section-empty_section < 200:
						detected = 0
						obj_section = 0
					else:
						break
				empty_section = 0

			if (roi_back_of_hump[i] == 0) and (detected == 1):
				empty_section = empty_section + 1
				obj_section = obj_section + 1

		tinggi_panggul = bottom - top2

		# get pin bone
		top_crop = int(bottom - 0.9 * tinggi_pinggul)
		bottom_crop = top_crop + 1
		left_crop = legs[1,1]
		right_crop = 770
		roi_pin_bone = smoothed[top_crop:bottom_crop, left_crop:right_crop][0]

		detected = 0
		empty_section = 0
		for i in range(0, roi_pin_bone.shape[0]):
			if (roi_pin_bone[i] == 255) and (detected == 0):
				detected = 1
				x_pin_bone = i

			if (roi_pin_bone[i] == 0) and (detected == 1):
				empty_section = empty_section + 1

			if (roi_pin_bone[i] == 255) and (detected == 1):
				if empty_section > 20:
					break
				else:
					x_pin_bone = i

		pin_bone = (x_pin_bone + legs[1,1], int(bottom - (0.9 * tinggi_pinggul)))

		# get shoulder
		shoulder = (legs[0,0], int(bottom - (0.55 * tinggi_panggul)))

		# get panjang
		panjang = round(math.sqrt((shoulder[0] - pin_bone[0])**2 + (shoulder[1] - pin_bone[1])**2))

		# cow size
		pixel_ratio = 0.05
		tinggi_panggul = round(tinggi_panggul * pixel_ratio, 1)
		tinggi_pinggul = round(tinggi_pinggul * pixel_ratio, 1)
		panjang = round(panjang * pixel_ratio, 1)

		print('Berat: ' + str(berat) + ' kg')
		print('Panjang:  ' + str(panjang) + ' cm')
		print('Tinggi Panggul: ' + str(tinggi_panggul) + ' cm')
		print('Tinggi Pinggul: ' + str(tinggi_pinggul) + ' cm')
			
#		except:
#			print('Cow Size Estimation FAILED')

# ==================================================================================
		# UPLOAD TO SERVER
#		try:
		# uplload image
		blob = bucket.blob(img_name + '.jpg')
		blob.upload_from_filename('image.jpg')
		img_url = 'gs://smokebeefs.appspot.com/' + img_name + '.jpg'
		print('Image Uploaded')
		
		# upload data
		doc_ref.add({
			'id': unicode(cow_id),
			'jenisKelamin': unicode(gender),
			'tanggalLahir': dt_born,
			'tanggalPengukuran': dt_now,
			'gambarURL': unicode(img_url),
			'berat': berat,
			'tinggiPanggul': tinggi_panggul,
			'tinggiPinggul': tinggi_pinggul,
			'panjang': panjang
		})
		print('Data Uploaded')
				
#		except:
#			print('Upload FAILED')

# ==================================================================================		
		
		# inform arduino that process has been done
		ser.write(b'OK')

		# reset variables
		berat = 0.0
		reading_flag = 0
		point_flag = 0
		shift_left = 1
		shift_right = 0.1
		count_float = 0
		
		# delete image
		os.remove('image.jpg')
		
		print('Process Has Been Completed\n\n')
