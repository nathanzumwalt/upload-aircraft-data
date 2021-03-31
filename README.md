# upload-aircraft-data

# Service Configuration / Installation

1. Build a PiAware receiver: https://flightaware.com/adsb/piaware/build
1. Install bobo3 library: pip3 install boto3
1. Copy https://github.com/nathanzumwalt/upload-aircraft-data/tree/main/upload-aicraft-data-service to /home/pi/upload-aircraft-data-service
1. Update values in upload_aircraft_data.ini
1. Place the service definition: sudo cp upload_aircraft_data.service /etc/systemd/system/upload_aircraft_data.service
1. Enable the service: sudo systemctl enable upload_aircraft_data
1. Start the service: sudo systemctl start upload_aircraft_data
2. Validate the service is running: tail -f /tmp/upload_aircraft_data.log
