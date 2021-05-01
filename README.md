# upload-aircraft-data

# Service Configuration / Installation

1. Build a PiAware receiver: https://flightaware.com/adsb/piaware/build (if you already have a Raspberry Pi and receiver: https://flightaware.com/adsb/piaware/install)
3. Install bobo3 library: pip3 install boto3
4. Copy https://github.com/nathanzumwalt/upload-aircraft-data/tree/main/upload-aicraft-data-service to /home/pi/upload-aircraft-data-service
5. Update values in upload_aircraft_data.ini (will need server-side configuration values)
6. Place the service definition: sudo cp /home/pi/upload-aircraft-data-service/upload_aircraft_data.service /etc/systemd/system/upload_aircraft_data.service
7. Enable the service: sudo systemctl enable upload_aircraft_data
8. Start the service: sudo systemctl start upload_aircraft_data
9. Validate the service is running: tail -f /tmp/upload_aircraft_data.log
10. See if data is appearing on the test map: https://zumwalt-map-html.s3-us-west-2.amazonaws.com/map2.html
