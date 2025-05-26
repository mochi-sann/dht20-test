# センサーデータロガーとビジュアライザー

このプロジェクトは、AHT20（温度/湿度）およびMH-Z19B（CO2）センサーからデータを読み取り、ローカルのSQLiteデータベースに記録し、Flask APIを介して公開し、Prometheusメトリクスを提供し、リモート監視のためにGrafana CloudのInfluxDBに送信します。

## 目次

- [前提条件](#前提条件)
- [ハードウェアのセットアップ](#ハードウェアのセットアップ)
- [ソフトウェアのセットアップ](#ソフトウェアのセットアップ)
- [Grafana Cloud / InfluxDBのセットアップ](#grafana-cloud--influxdbのセットアップ)
- [アプリケーションの実行](#アプリケーションの実行)
- [Grafanaでのデータ表示](#grafanaでのデータ表示)

## 前提条件

始める前に、以下のものがあることを確認してください。

*   **Raspberry Pi**（または同様のシングルボードコンピューター）とRaspbian OSがインストールされていること。
*   **AHT20 温度/湿度センサー**
*   **MH-Z19B CO2センサー**
*   **ジャンパーワイヤー**
*   Raspberry Piの**インターネット接続**。
*   **Grafana Cloudアカウント**（無料枠で十分です）。

## ハードウェアのセットアップ

センサーをRaspberry PiのGPIOピンに接続します。

### AHT20センサー (I2C)

AHT20センサーはI2Cプロトコルを使用します。次のように接続します。

*   **VCC**: Raspberry Piの3.3Vまたは5Vピンへ（AHT20モジュールの電圧互換性を確認してください）。
*   **GND**: Raspberry PiのGNDピンへ。
*   **SDA**: Raspberry PiのSDA（GPIO2）ピンへ。
*   **SCL**: Raspberry PiのSCL（GPIO3）ピンへ。

### MH-Z19B CO2センサー (UART)

MH-Z19BセンサーはUART（シリアル通信）を使用します。次のように接続します。

*   **Vin**: Raspberry Piの5Vピンへ。
*   **GND**: Raspberry PiのGNDピンへ。
*   **RxD**: Raspberry PiのTxD（GPIO14）ピンへ。
*   **TxD**: Raspberry PiのRxD（GPIO15）ピンへ。

**MH-Z19Bに関する重要事項**: センサーのためにUARTピンを解放するには、Raspberry Piのシリアルコンソールを無効にする必要があるかもしれません。
これは、`sudo raspi-config` -> `Interface Options` -> `Serial Port` -> `Would you like a login shell to be accessible over serial?` -> `No` -> `Would you like the serial port hardware to be enabled?` -> `Yes` で行えます。

## ソフトウェアのセットアップ

1.  **I2CとUARTの有効化**:
    Raspberry PiでI2CとUARTが有効になっていることを確認してください。これは`sudo raspi-config` -> `Interface Options`を使用して行えます。

2.  **更新とアップグレード**:
    ```bash
    sudo apt update
    sudo apt upgrade -y
    ```

3.  **Pythonとpipのインストール**:
    ```bash
    sudo apt install python3 python3-pip -y
    ```

4.  **プロジェクトの依存関係のインストール**:
    プロジェクトディレクトリに移動し、必要なPythonライブラリをインストールします。
    ```bash
    pip3 install -r requirements.txt
    ```

## Grafana Cloud / InfluxDBのセットアップ

Grafana Cloudにデータを送信するには、InfluxDBの認証情報を取得する必要があります。

1.  **Grafana Cloudにログイン**: [grafana.com/cloud](https://grafana.com/cloud) にアクセスし、アカウントにログインします。
2.  **InfluxDBへ移動**: Grafana Cloudポータルで、「InfluxDB」セクションを見つけます（通常、「Data Sources」または「Integrations」の下にあります）。
3.  **接続詳細の取得**:
    *   **URL**: InfluxDBのURLを探します（例: `https://<your-stack-slug>.influxdata.io`）。
    *   **Organization ID**: これは文字列です。
    *   **Bucket**: デフォルトの`default`バケットを使用するか、新しいバケットを作成できます。
4.  **APIトークンの生成**:
    *   InfluxDBセクション内の「API Tokens」に移動します。
    *   新しいAPIトークンを作成します。使用するバケットへの**書き込み権限**があることを確認してください。このトークンは二度と表示されないため、すぐにコピーしてください。

## アプリケーションの実行

1.  **環境変数の設定**:
    `sub.py`を実行する前に、Grafana Cloudから取得した認証情報でInfluxDBの環境変数を設定する必要があります。
    プレースホルダーの値を実際の認証情報に置き換えてください。

    ```bash
    export INFLUXDB_URL="YOUR_INFLUXDB_URL"
    export INFLUXDB_TOKEN="YOUR_INFLUXDB_TOKEN"
    export INFLUXDB_ORG="YOUR_INFLUXDB_ORG_ID"
    export INFLUXDB_BUCKET="YOUR_INFLUXDB_BUCKET_NAME" # 例: "default" または "sensor_data"
    ```
    これらの`export`コマンドを`~/.bashrc`または`~/.profile`ファイルに追加すると、セッション間で永続化されるため推奨されます。編集後、`source ~/.bashrc`（または`source ~/.profile`）を実行してください。

2.  **`sub.py`の実行**:
    ```bash
    python3 sub.py
    ```
    センサーの読み取りと「Data written to InfluxDB.」メッセージを示す出力が表示されるはずです。

## Grafanaでのデータ表示

1.  **GrafanaでInfluxDBデータソースを追加**:
    *   Grafana Cloudインスタンスにログインします。
    *   `Connections` -> `Data sources` -> `Add new data source` に移動します。
    *   `InfluxDB`を検索します。
    *   環境変数に使用したのと同じURL、トークン、組織、バケットで設定します。
    *   `Query Language`を`Flux`に設定します。
    *   保存してテストします。

2.  **Grafanaダッシュボードの作成**:
    *   `Dashboards` -> `New Dashboard` -> `Add new panel` に移動します。
    *   InfluxDBデータソースを選択します。
    *   Fluxクエリを使用してセンサーデータを視覚化します。以下にクエリの例を示します。

    **温度パネル (ゲージまたはグラフ)**:
    ```flux
    from(bucket: "YOUR_INFLUXDB_BUCKET_NAME")
      |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
      |> filter(fn: (r) => r._measurement == "sensor_data" and r._field == "temperature")
      |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
      |> yield(name: "mean_temperature")
    ```

    **湿度パネル (ゲージまたはグラフ)**:
    ```flux
    from(bucket: "YOUR_INFLUXDB_BUCKET_NAME")
      |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
      |> filter(fn: (r) => r._measurement == "sensor_data" and r._field == "humidity")
      |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
      |> yield(name: "mean_humidity")
    ```

    **CO2パネル (ゲージまたはグラフ)**:
    ```flux
    from(bucket: "YOUR_INFLUXDB_BUCKET_NAME")
      |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
      |> filter(fn: (r) => r._measurement == "sensor_data" and r._field == "co2")
      |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
      |> yield(name: "mean_co2")
    ```
    `YOUR_INFLUXDB_BUCKET_NAME`を実際のバケット名に置き換えることを忘れないでください。
