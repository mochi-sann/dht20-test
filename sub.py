import time
import board
import busio
import adafruit_ahtx0
import mh_z19
import json
from datetime import datetime
import sqlite3
import os
from flask import Flask, jsonify, send_from_directory
import threading
from queue import Queue
import contextlib
from prometheus_client import generate_latest, Counter, Gauge, CONTENT_TYPE_LATEST

app = Flask(__name__)

# Prometheus metrics
temperature_gauge = Gauge('temperature_celsius', 'Temperature in Celsius')
humidity_gauge = Gauge('humidity_percent', 'Humidity in percent')
co2_gauge = Gauge('co2_ppm', 'CO2 in ppm')

# データ保存用のキュー
data_queue = Queue()

# データベースの初期化
def init_db():
    db_path = 'sensor_data.db'
    is_new_db = not os.path.exists(db_path)
    
    with contextlib.closing(sqlite3.connect(db_path)) as conn:
        c = conn.cursor()
        if is_new_db:
            c.execute('''
                CREATE TABLE sensor_readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    temperature REAL,
                    humidity REAL,
                    co2 INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

# データベースにデータを保存する関数
def save_to_db(temperature, humidity, co2):
    with contextlib.closing(sqlite3.connect('sensor_data.db')) as conn:
        c = conn.cursor()
        c.execute('''
            INSERT INTO sensor_readings (temperature, humidity, co2)
            VALUES (?, ?, ?)
        ''', (temperature, humidity, co2))
        conn.commit()

# データベースワーカースレッド
def db_worker():
    while True:
        try:
            # キューからデータを取得
            data = data_queue.get()
            if data is None:  # 終了シグナル
                break
            
            # データベースに保存
            save_to_db(data['temperature'], data['humidity'], data['co2'])
            
            # タスク完了をマーク
            data_queue.task_done()
        except Exception as e:
            print(f"Database error: {e}")

# データ取得用の関数
def get_db_connection():
    conn = sqlite3.connect('sensor_data.db')
    conn.row_factory = sqlite3.Row
    return conn

# Flaskルート
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/app.js')
def app_js():
    return send_from_directory('.', 'app.js')

@app.route('/api/latest')
def get_latest():
    with contextlib.closing(get_db_connection()) as conn:
        c = conn.cursor()
        c.execute('''
            SELECT temperature, humidity, co2, timestamp
            FROM sensor_readings
            ORDER BY timestamp DESC
            LIMIT 1
        ''')
        row = c.fetchone()
        if row:
            return jsonify({
                'temperature': row[0],
                'humidity': row[1],
                'co2': row[2],
                'timestamp': row[3]
            })
        return jsonify({'error': 'No data available'}), 404

@app.route('/api/history')
def get_history():
    with contextlib.closing(get_db_connection()) as conn:
        c = conn.cursor()
        c.execute('''
            SELECT temperature, humidity, co2, timestamp
            FROM sensor_readings
            ORDER BY timestamp DESC
            LIMIT 1000
        ''')
        rows = c.fetchall()
        data = [{
            'temperature': row[0],
            'humidity': row[1],
            'co2': row[2],
            'timestamp': row[3]
        } for row in rows]
        return jsonify(data)

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

# センサーデータを読み取る関数
def read_sensor_data():
    while True:
        try:
            # センサーデータを読み取る
            temperature = sensor.temperature
            humidity = sensor.relative_humidity
            co2_data = mh_z19.read(serial_console_untouched=True)
            co2 = co2_data['co2']

            # Prometheusメトリクスを更新
            temperature_gauge.set(temperature)
            humidity_gauge.set(humidity)
            co2_gauge.set(co2)

            # データをキューに追加
            data_queue.put({
                'temperature': temperature,
                'humidity': humidity,
                'co2': co2
            })

            # コンソールに出力
            print(f"Temperature: {temperature:.2f} °C")
            print(f"Humidity: {humidity:.2f} %")
            print(f"CO2: {co2} ppm")
            print("------------------------")

        except Exception as e:
            print(f"Error reading sensor: {e}")
            print("Trying to continue...")

        time.sleep(2)

# Better error handling and initialization for AHT sensor
try:
    # データベースの初期化
    init_db()
    
    # データベースワーカースレッドを開始
    db_thread = threading.Thread(target=db_worker)
    db_thread.daemon = True
    db_thread.start()
    
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

    # センサーデータ読み取りスレッドを開始
    sensor_thread = threading.Thread(target=read_sensor_data)
    sensor_thread.daemon = True
    sensor_thread.start()

    # Flaskサーバーを起動
    print("Starting Flask server...")
    app.run(host='0.0.0.0', port=5000)

except KeyboardInterrupt:
    print("Exiting program by user request...")
    # データベースワーカーの終了
    data_queue.put(None)
    data_queue.join()
except Exception as e:
    print(f"Fatal error: {e}")
    print("Troubleshooting tips:")
    print("1. Verify your wiring connections (SDA, SCL, VCC, GND)")
    print("2. Ensure sensor is receiving proper voltage (3.3V or 5V)")
    print("3. Check for I2C address conflicts")
    print("4. Try with pull-up resistors on SDA/SCL if not present")
    # データベースワーカーの終了
    data_queue.put(None)
    data_queue.join()
