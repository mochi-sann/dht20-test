# Sensor Data Logger and Visualizer

This project reads data from AHT20 (temperature/humidity) and MH-Z19B (CO2) sensors, logs it to a local SQLite database, exposes it via a Flask API, provides Prometheus metrics, and sends it to Grafana Cloud's InfluxDB for remote monitoring.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Hardware Setup](#hardware-setup)
- [Software Setup](#software-setup)
- [Grafana Cloud / InfluxDB Setup](#grafana-cloud--influxdb-setup)
- [Running the Application](#running-the-application)
- [Viewing Data in Grafana](#viewing-data-in-grafana)

## Prerequisites

Before you begin, ensure you have the following:

*   **Raspberry Pi** (or similar single-board computer) with Raspbian OS installed.
*   **AHT20 Temperature/Humidity Sensor**
*   **MH-Z19B CO2 Sensor**
*   **Jumper Wires**
*   **Internet Connection** for the Raspberry Pi.
*   **Grafana Cloud Account** (free tier is sufficient for testing).

## Hardware Setup

Connect your sensors to the Raspberry Pi's GPIO pins.

### AHT20 Sensor (I2C)

The AHT20 sensor uses the I2C protocol. Connect it as follows:

*   **VCC**: To Raspberry Pi's 3.3V or 5V pin (check your AHT20 module's voltage compatibility).
*   **GND**: To Raspberry Pi's GND pin.
*   **SDA**: To Raspberry Pi's SDA (GPIO2) pin.
*   **SCL**: To Raspberry Pi's SCL (GPIO3) pin.

### MH-Z19B CO2 Sensor (UART)

The MH-Z19B sensor uses UART (serial communication). Connect it as follows:

*   **Vin**: To Raspberry Pi's 5V pin.
*   **GND**: To Raspberry Pi's GND pin.
*   **RxD**: To Raspberry Pi's TxD (GPIO14) pin.
*   **TxD**: To Raspberry Pi's RxD (GPIO15) pin.

**Important for MH-Z19B**: You might need to disable the serial console on your Raspberry Pi to free up the UART pins for the sensor.
You can do this via `sudo raspi-config` -> `Interface Options` -> `Serial Port` -> `Would you like a login shell to be accessible over serial?` -> `No` -> `Would you like the serial port hardware to be enabled?` -> `Yes`.

## Software Setup

1.  **Enable I2C and UART**:
    Ensure I2C and UART are enabled on your Raspberry Pi. You can do this using `sudo raspi-config` -> `Interface Options`.

2.  **Update and Upgrade**:
    ```bash
    sudo apt update
    sudo apt upgrade -y
    ```

3.  **Install Python and pip**:
    ```bash
    sudo apt install python3 python3-pip -y
    ```

4.  **Install Project Dependencies**:
    Navigate to your project directory and install the required Python libraries.
    ```bash
    pip3 install -r requirements.txt
    ```

## Grafana Cloud / InfluxDB Setup

To send data to Grafana Cloud, you need to obtain your InfluxDB credentials.

1.  **Log in to Grafana Cloud**: Go to [grafana.com/cloud](https://grafana.com/cloud) and log in to your account.
2.  **Navigate to InfluxDB**: In the Grafana Cloud portal, find the "InfluxDB" section (usually under "Data Sources" or "Integrations").
3.  **Get Connection Details**:
    *   **URL**: Look for the InfluxDB URL (e.g., `https://<your-stack-slug>.influxdata.io`).
    *   **Organization ID**: This will be a string of characters.
    *   **Bucket**: You can use the default `default` bucket or create a new one.
4.  **Generate an API Token**:
    *   Go to "API Tokens" within the InfluxDB section.
    *   Create a new API Token. Ensure it has **write permissions** for the bucket you intend to use. Copy this token immediately as it won't be shown again.

## Running the Application

1.  **Set Environment Variables**:
    Before running `sub.py`, you must set the InfluxDB environment variables with the credentials you obtained from Grafana Cloud.
    Replace the placeholder values with your actual credentials.

    ```bash
    export INFLUXDB_URL="YOUR_INFLUXDB_URL"
    export INFLUXDB_TOKEN="YOUR_INFLUXDB_TOKEN"
    export INFLUXDB_ORG="YOUR_INFLUXDB_ORG_ID"
    export INFLUXDB_BUCKET="YOUR_INFLUXDB_BUCKET_NAME" # e.g., "default" or "sensor_data"
    ```
    It's recommended to add these `export` commands to your `~/.bashrc` or `~/.profile` file if you want them to persist across sessions. After editing, run `source ~/.bashrc` (or `source ~/.profile`).

2.  **Run `sub.py`**:
    ```bash
    python3 sub.py
    ```
    You should see output indicating sensor readings and "Data written to InfluxDB." messages.

## Viewing Data in Grafana

1.  **Add InfluxDB Data Source in Grafana**:
    *   Log in to your Grafana Cloud instance.
    *   Go to `Connections` -> `Data sources` -> `Add new data source`.
    *   Search for `InfluxDB`.
    *   Configure it with the same URL, Token, Organization, and Bucket you used for the environment variables.
    *   Set the `Query Language` to `Flux`.
    *   Save and Test.

2.  **Create a Grafana Dashboard**:
    *   Go to `Dashboards` -> `New Dashboard` -> `Add new panel`.
    *   Select your InfluxDB data source.
    *   Use Flux queries to visualize your sensor data. Here are example queries:

    **Temperature Panel (Gauge or Graph)**:
    ```flux
    from(bucket: "YOUR_INFLUXDB_BUCKET_NAME")
      |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
      |> filter(fn: (r) => r._measurement == "sensor_data" and r._field == "temperature")
      |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
      |> yield(name: "mean_temperature")
    ```

    **Humidity Panel (Gauge or Graph)**:
    ```flux
    from(bucket: "YOUR_INFLUXDB_BUCKET_NAME")
      |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
      |> filter(fn: (r) => r._measurement == "sensor_data" and r._field == "humidity")
      |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
      |> yield(name: "mean_humidity")
    ```

    **CO2 Panel (Gauge or Graph)**:
    ```flux
    from(bucket: "YOUR_INFLUXDB_BUCKET_NAME")
      |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
      |> filter(fn: (r) => r._measurement == "sensor_data" and r._field == "co2")
      |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
      |> yield(name: "mean_co2")
    ```
    Remember to replace `YOUR_INFLUXDB_BUCKET_NAME` with your actual bucket name.
