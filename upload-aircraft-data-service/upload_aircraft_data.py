import logging
import os
import threading
import json
import boto3
from botocore.exceptions import ClientError
import uuid
import time
import signal
import sys
import configparser

config_filename = "/home/pi/upload_aircraft_data.ini"

config = configparser.ConfigParser()
config.read(config_filename)

print(config['general']['station_name'])

# Local raspberry pi config #############################################
station_name = config['general']['station_name'] 
ACCESS_KEY = config['general']['aws_access_key']  
SECRET_KEY = config['general']['aws_secret_key'] 
log_filename = config['general']['log_filename'] 
full_aircraft_path = config['general']['full_aircraft_path'] 
global aircraft_upload_interval
aircraft_upload_interval = int(config['general']['aircraft_upload_interval_seconds'])

# Remote config #########################################################
update_station_config_interval = int(config['general']['update_station_config_interval_minutes']) * 60 # 1 * 60 
s3_bucket_name = config['general']['s3_bucket_name'] 

station_config = []
config_run_event = threading.Event()
logging.basicConfig(level=logging.INFO,filename=log_filename, filemode='a', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def get_s3_client():
	s3_client = boto3.client(
		's3', 
		aws_access_key_id=ACCESS_KEY,
		aws_secret_access_key=SECRET_KEY
	)
	return s3_client

#########################################################################
# Update the station config from S3 every X minutes
def update_station_config():
	seconds_between_update = update_station_config_interval
	while config_run_event.is_set():

		# Hacky; do a tight spin, then update (allows for the thred to be shut down quickly)
		if seconds_between_update > 0:
			#logging.info(seconds_between_update)
			time.sleep(1)
			seconds_between_update = seconds_between_update - 1
		else:
			logging.info("in update_station_config")
			get_station_config();
			seconds_between_update = update_station_config_interval 


#########################################################################
# Get the station config from the S3 bucket and save it locally
def get_station_config():

	try:
		s3 = get_s3_client() #boto3.resource('s3')

		key = 'station-config/' + station_name + '.json'
		#logging.info('key=' + key)

		content_object = s3.get_object(Bucket=s3_bucket_name, Key=key)
		file_content = content_object['Body'].read().decode('utf-8')
		logging.info(file_content)
		global station_config
		station_config = json.loads(file_content)
		logging.info(station_config)
	except ClientError as e:
		logging.error(e)
		return False
	return True

#########################################################################
# Upload a file to the S3 bucket
def upload_file(file_name, bucket, object_name=None):
	"""Upload a file to an S3 bucket

	:param file_name: File to upload
	:param bucket: Bucket to upload to
	:param object_name: S3 object name. If not specified then file_name is used
	:return: True if file was uploaded, else False
	"""

	# If S3 object_name was not specified, use file_name
	if object_name is None:
		object_name = file_name

	# Upload the file
	try:
		response = get_s3_client().upload_file(file_name, bucket, object_name)
	except ClientError as e:
		logging.error(e)
		return False

	return True

#########################################################################
# Remove aircraft entries that are older than the last iteration (i.e., have already been sent)
def remove_aircraft_last_seen(input_aircraft_filename, output_aircraft_filename, interval):
	#logging.info("in remove_aircraft_last_seen")

	data = []

	#Open/read the aircraft file
	with open(input_aircraft_filename) as json_file:
		data = json.load(json_file)

	#Not sure how this works, seems like magic
	#re-writes the aircraft list only with those that have been "seen" in the interval
	data['aircraft'] = [obj for obj in data['aircraft'] if(int(obj['seen']) < interval)] 

	#logging.info('aircraft len=' + str(len(data['aircraft'])))
	#if there are no aircraft entries to be output, return False
	if len(data['aircraft']) < 1:
		return False
	
	#Write the updated data to the output file
	with open(output_aircraft_filename, 'w') as output_file:
		json.dump(data, output_file)

	#logging.info('wrote to ' + output_aircraft_filename)

	#Still have aircraft entries, so return True
	return True

#########################################################################
# Handle stop signal from systemd
def handler_stop_signals(signum, frame):
    writeString("in stop_signals: " + str(signum) + " " + str(frame))
    global run
    run = False

#########################################################################
# Main section of the script (TODO: Move this to a main function)

run = True

signal.signal(signal.SIGINT, handler_stop_signals)
signal.signal(signal.SIGTERM, handler_stop_signals)

logging.info('PID=' + str(os.getpid()))
#Get initial station config, will update from thread after this
get_station_config()

#start thread to update the station_config
config_thread = threading.Thread(target=update_station_config, args=())
config_run_event.set()
config_thread.start()

try: 
	while run: 
		logging.info("station_config=" + str(station_config))
		logging.info("aircraft_upload_interval=" + str(aircraft_upload_interval))
		if 'aircraft_upload_interval' in station_config.keys():
			aircraft_upload_interval = int(station_config['aircraft_upload_interval'])
		if station_config['upload'] == 'true':
			temp_filename = str(uuid.uuid4()) + '.json' 
			temp_filepath = '/tmp/' + temp_filename
	
			upload_filename = station_name + '/' + temp_filename
	
			if remove_aircraft_last_seen(full_aircraft_path, temp_filepath, aircraft_upload_interval):
				logging.info('uploading file: ' + temp_filepath)
				upload_file(temp_filepath, s3_bucket_name, upload_filename) 
				os.remove(temp_filepath)
				logging.info('done uploading')
			else:
				logging.info('no entries in file to upload')
		else:
			logging.info('not uploading')
		time.sleep(aircraft_upload_interval)
except Exception as e:
	logging.error(e, exc_info=True)
	logging.info(sys.exc_info())
	logging.info("waiting for threads to complete")
	config_run_event.clear()
	config_thread.join()	
	logging.info("threads complete")
