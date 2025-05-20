#!/bin/bash

# エラーが発生したら即座に終了
set -e

echo "GrafanaとPrometheusのセットアップを開始します..."

# 必要なパッケージのインストール
echo "必要なパッケージをインストール中..."
sudo apt-get update
sudo apt-get install -y apt-transport-https software-properties-common wget

# GrafanaのGPGキーを追加
echo "GrafanaのGPGキーを追加中..."
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -

# Grafanaのリポジトリを追加
echo "Grafanaのリポジトリを追加中..."
echo "deb https://packages.grafana.com/oss/deb stable main" | sudo tee /etc/apt/sources.list.d/grafana.list

# Prometheusのダウンロードとインストール
echo "Prometheusをインストール中..."
PROMETHEUS_VERSION="2.45.0"
wget https://github.com/prometheus/prometheus/releases/download/v${PROMETHEUS_VERSION}/prometheus-${PROMETHEUS_VERSION}.linux-armv7.tar.gz
tar xvfz prometheus-${PROMETHEUS_VERSION}.linux-armv7.tar.gz
sudo mv prometheus-${PROMETHEUS_VERSION}.linux-armv7/prometheus /usr/local/bin/
sudo mv prometheus-${PROMETHEUS_VERSION}.linux-armv7/promtool /usr/local/bin/
sudo mkdir -p /etc/prometheus
sudo mkdir -p /var/lib/prometheus

# Prometheusの設定ファイルをコピー
echo "Prometheusの設定ファイルを配置中..."
sudo cp prometheus.yml /etc/prometheus/

# Prometheusのサービスファイルを作成
echo "Prometheusのサービスを設定中..."
sudo tee /etc/systemd/system/prometheus.service << EOF
[Unit]
Description=Prometheus
Wants=network-online.target
After=network-online.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/usr/local/bin/prometheus \
    --config.file /etc/prometheus/prometheus.yml \
    --storage.tsdb.path /var/lib/prometheus \
    --web.console.templates=/etc/prometheus/consoles \
    --web.console.libraries=/etc/prometheus/console_libraries

[Install]
WantedBy=multi-user.target
EOF

# Prometheusユーザーの作成
echo "Prometheusユーザーを作成中..."
sudo useradd -rs /bin/false prometheus
sudo chown -R prometheus:prometheus /etc/prometheus
sudo chown -R prometheus:prometheus /var/lib/prometheus

# Prometheusサービスを有効化して起動
echo "Prometheusサービスを有効化して起動中..."
sudo systemctl daemon-reload
sudo systemctl enable prometheus
sudo systemctl start prometheus

# パッケージリストを更新
echo "パッケージリストを更新中..."
sudo apt-get update

# Grafanaをインストール
echo "Grafanaをインストール中..."
sudo apt-get install -y grafana

# Grafanaサービスを有効化して起動
echo "Grafanaサービスを有効化して起動中..."
sudo systemctl enable grafana-server
sudo systemctl start grafana-server

# ファイアウォールで必要なポートを開放
echo "ファイアウォールでポートを開放中..."
sudo ufw allow 3000/tcp  # Grafana
sudo ufw allow 9090/tcp  # Prometheus

# セットアップ完了メッセージ
echo "セットアップが完了しました！"
echo ""
echo "Grafana: http://localhost:3000"
echo "デフォルトのログイン情報："
echo "ユーザー名: admin"
echo "パスワード: admin"
echo ""
echo "Prometheus: http://localhost:9090"
echo ""
echo "初回ログイン時にパスワードの変更を求められます。"
echo ""
echo "Grafanaでデータを表示するには："
echo "1. データソースとしてPrometheusを追加（URL: http://localhost:9090）"
echo "2. 新しいダッシュボードを作成"
echo "3. 以下のメトリクスを追加："
echo "   - temperature_celsius（温度）"
echo "   - humidity_percent（湿度）"
echo "   - co2_ppm（CO2濃度）"
echo ""
echo "センサーデータの表示を開始するには："
echo "python sub.py を実行してください" 