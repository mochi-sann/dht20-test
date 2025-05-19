import time
import board
import busio
import adafruit_ahtx0
import mh_z19
from grafana_client import GrafanaApi
from grafana_client.client import GrafanaClientError
from dotenv import load_dotenv
import os
import json
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Grafana Cloud configuration from environment variables
GRAFANA_URL = os.getenv('GRAFANA_URL', 'https://mochi33i.grafana.net')
GRAFANA_API_KEY = os.getenv('GRAFANA_API_KEY')
GRAFANA_ORG_ID = os.getenv('GRAFANA_ORG_ID')

# Validate required environment variables
if not GRAFANA_API_KEY or not GRAFANA_ORG_ID:
    raise ValueError("""
    Required environment variables are not set.
    Please create a .env file with the following variables:
    GRAFANA_URL=https://mochi33i.grafana.net
    GRAFANA_API_KEY=your-api-key
    GRAFANA_ORG_ID=your-org-id
    """)

# Initialize Grafana client
grafana = GrafanaApi(
    auth=GRAFANA_API_KEY,
    host=GRAFANA_URL
)

# Better error handling and initialization for AHT sensor
try:
    # Initialize I2C
    print("Initializing I2C...")
    i2c = busio.I2C(board.SCL, board.SDA)
    
    # Scan I2C bus and report found devices
    devices = i2c.scan()
    print(f"I2C devices found: {[hex(device) for device in devices]}")
    
    # Check if AHT device (typically at 0x38) is present
    if 0x38 not in devices:
        print("Warning: AHT sensor (0x38) not found on I2C bus!")
        print("Check your wiring connections.")
    
    # Add delay before sensor initialization (helps with some hardware)
    print("Waiting for sensor to stabilize...")
    time.sleep(1)
    
    # Try to initialize the sensor with retry logic
    retry_count = 3
    sensor = None
    
    for attempt in range(retry_count):
        try:
            print(f"Attempt {attempt+1}/{retry_count} to initialize sensor...")
            sensor = adafruit_ahtx0.AHTx0(i2c)
            print("Sensor initialized successfully!")
            break
        except RuntimeError as e:
            print(f"Initialization failed: {e}")
            if attempt < retry_count - 1:
                print("Retrying after delay...")
                time.sleep(2)  # Wait longer between retries
            else:
                print("All initialization attempts failed.")
                raise
    
    # Main sensor reading loop
    print("Starting measurement loop...")
    while True:
        try:
            # Read temperature and humidity
            temperature = sensor.temperature
            humidity = sensor.relative_humidity
            
            # Read CO2
            co2_data = mh_z19.read(serial_console_untouched=True)
            co2 = co2_data['co2']
            
            # Print readings
            print(f"Temperature: {temperature:.2f} °C")
            print(f"Humidity: {humidity:.2f} %")
            print(f"CO2: {co2} ppm")
            print("------------------------")
            
            # Prepare data for Grafana Cloud
            timestamp = int(datetime.now().timestamp() * 1000)  # milliseconds
            data = {
                "temperature": temperature,
                "humidity": humidity,
                "co2": co2,
                "timestamp": timestamp
            }
            
            # Send data to Grafana Cloud
            try:
                grafana.datasource_proxy(
                    org_id=GRAFANA_ORG_ID,
                    datasource_id="prometheus",  # or your specific datasource ID
                    path="/api/v1/write",
                    method="POST",
                    json=data
                )
            except GrafanaClientError as e:
                print(f"Error sending data to Grafana Cloud: {e}")
            
        except Exception as e:
            print(f"Error reading sensor: {e}")
            print("Trying to continue...")
        
        time.sleep(2)
        
except KeyboardInterrupt:
    print("Exiting program by user request...")
except Exception as e:
    print(f"Fatal error: {e}")
    print("Troubleshooting tips:")
    print("1. Verify your wiring connections (SDA, SCL, VCC, GND)")
    print("2. Ensure sensor is receiving proper voltage (3.3V or 5V)")
    print("3. Check for I2C address conflicts")
    print("4. Try with pull-up resistors on SDA/SCL if not present")
    print("5. Verify Grafana Cloud connection settings")
