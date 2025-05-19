import time
import board
import busio
import adafruit_ahtx0

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
            temperature = sensor.temperature
            humidity = sensor.relative_humidity
            print(f"Temperature: {temperature:.2f} °C")
            print(f"Humidity: {humidity:.2f} %")
            print("------------------------")
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
