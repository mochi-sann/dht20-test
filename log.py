import time
import board
import busio
import adafruit_ahtx0
import mh_z19
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# InfluxDB configuration from environment variables
INFLUXDB_URL = os.getenv('INFLUXDB_URL', 'http://localhost:8086')
INFLUXDB_TOKEN = os.getenv('INFLUXDB_TOKEN')
INFLUXDB_ORG = os.getenv('INFLUXDB_ORG')
INFLUXDB_BUCKET = os.getenv('INFLUXDB_BUCKET', 'sensor_data')

# Validate required environment variables
if not INFLUXDB_TOKEN or not INFLUXDB_ORG:
    raise ValueError("""
    Required environment variables are not set.
    Please create a .env file with the following variables:
    INFLUXDB_URL=http://localhost:8086
    INFLUXDB_TOKEN=your-token
    INFLUXDB_ORG=your-org
    INFLUXDB_BUCKET=sensor_data
    """)

# Initialize InfluxDB client
influx_client = InfluxDBClient(
    url=INFLUXDB_URL,
    token=INFLUXDB_TOKEN,
    org=INFLUXDB_ORG
)
write_api = influx_client.write_api(write_options=SYNCHRONOUS)

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
            co2_data = mh_z19.read()
            co2 = co2_data['co2']
            
            # Print readings
            print(f"Temperature: {temperature:.2f} °C")
            print(f"Humidity: {humidity:.2f} %")
            print(f"CO2: {co2} ppm")
            print("------------------------")
            
            # Create data point for InfluxDB
            point = Point("sensor_readings") \
                .field("temperature", temperature) \
                .field("humidity", humidity) \
                .field("co2", co2)
            
            # Write to InfluxDB
            write_api.write(bucket=INFLUXDB_BUCKET, record=point)
            
        except Exception as e:
            print(f"Error reading sensor: {e}")
            print("Trying to continue...")
        
        time.sleep(2)
        
except KeyboardInterrupt:
    print("Exiting program by user request...")
    influx_client.close()
except Exception as e:
    print(f"Fatal error: {e}")
    print("Troubleshooting tips:")
    print("1. Verify your wiring connections (SDA, SCL, VCC, GND)")
    print("2. Ensure sensor is receiving proper voltage (3.3V or 5V)")
    print("3. Check for I2C address conflicts")
    print("4. Try with pull-up resistors on SDA/SCL if not present")
    print("5. Verify InfluxDB connection settings")
    influx_client.close()
