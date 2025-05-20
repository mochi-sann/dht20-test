import time
import board
import busio
import adafruit_ahtx0
import mh_z19
import asyncio
import websockets
import json
from datetime import datetime
import sqlite3
import os

# データベースの初期化
def init_db():
    db_path = 'sensor_data.db'
    is_new_db = not os.path.exists(db_path)
    
    conn = sqlite3.connect(db_path)
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
    
    return conn

# データベースにデータを保存
def save_to_db(conn, temperature, humidity, co2):
    c = conn.cursor()
    c.execute('''
        INSERT INTO sensor_readings (temperature, humidity, co2)
        VALUES (?, ?, ?)
    ''', (temperature, humidity, co2))
    conn.commit()

# Better error handling and initialization for AHT sensor
try:
    # データベースの初期化
    db_conn = init_db()
    
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

    # WebSocket接続を保持するセット
    connected_clients = set()

    # WebSocketサーバーのハンドラ
    async def websocket_handler(websocket, path):
        connected_clients.add(websocket)
        try:
            # 接続時に最新のデータを送信
            c = db_conn.cursor()
            c.execute('''
                SELECT temperature, humidity, co2, timestamp
                FROM sensor_readings
                ORDER BY timestamp DESC
                LIMIT 100
            ''')
            historical_data = c.fetchall()
            
            # データを逆順にして時系列順に
            for row in reversed(historical_data):
                data = {
                    'temperature': row[0],
                    'humidity': row[1],
                    'co2': row[2],
                    'timestamp': row[3]
                }
                await websocket.send(json.dumps(data))
            
            async for message in websocket:
                # クライアントからのメッセージを処理（必要な場合）
                pass
        finally:
            connected_clients.remove(websocket)

    # センサーデータを送信する関数
    async def send_sensor_data():
        while True:
            try:
                # センサーデータを読み取る
                temperature = sensor.temperature
                humidity = sensor.relative_humidity
                co2_data = mh_z19.read(serial_console_untouched=True)
                co2 = co2_data['co2']

                # データベースに保存
                save_to_db(db_conn, temperature, humidity, co2)

                # データをJSON形式に変換
                data = {
                    'temperature': temperature,
                    'humidity': humidity,
                    'co2': co2,
                    'timestamp': datetime.now().isoformat()
                }

                # 接続中の全クライアントにデータを送信
                if connected_clients:
                    websockets.broadcast(connected_clients, json.dumps(data))

                # コンソールに出力
                print(f"Temperature: {temperature:.2f} °C")
                print(f"Humidity: {humidity:.2f} %")
                print(f"CO2: {co2} ppm")
                print("------------------------")

            except Exception as e:
                print(f"Error reading sensor: {e}")
                print("Trying to continue...")

            await asyncio.sleep(2)

    # メインループ
    async def main():
        # WebSocketサーバーを起動
        server = await websockets.serve(websocket_handler, "localhost", 8765)
        print("WebSocket server started on ws://localhost:8765")

        # センサーデータ送信タスクを開始
        await send_sensor_data()

    # イベントループを実行
    asyncio.run(main())

except KeyboardInterrupt:
    print("Exiting program by user request...")
    db_conn.close()
except Exception as e:
    print(f"Fatal error: {e}")
    print("Troubleshooting tips:")
    print("1. Verify your wiring connections (SDA, SCL, VCC, GND)")
    print("2. Ensure sensor is receiving proper voltage (3.3V or 5V)")
    print("3. Check for I2C address conflicts")
    print("4. Try with pull-up resistors on SDA/SCL if not present")
    db_conn.close()
