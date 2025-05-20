// チャートの設定
const chartConfig = {
    type: 'line',
    options: {
        responsive: true,
        animation: false,
        scales: {
            x: {
                type: 'time',
                time: {
                    unit: 'second',
                    displayFormats: {
                        second: 'HH:mm:ss'
                    }
                },
                title: {
                    display: true,
                    text: '時間'
                }
            },
            y: {
                beginAtZero: false
            }
        },
        plugins: {
            legend: {
                display: false
            }
        }
    }
};

// 温度チャートの初期化
const tempChart = new Chart(
    document.getElementById('tempChart'),
    {
        ...chartConfig,
        data: {
            datasets: [{
                label: '温度',
                data: [],
                borderColor: 'rgb(255, 99, 132)',
                tension: 0.1
            }]
        }
    }
);

// 湿度チャートの初期化
const humidityChart = new Chart(
    document.getElementById('humidityChart'),
    {
        ...chartConfig,
        data: {
            datasets: [{
                label: '湿度',
                data: [],
                borderColor: 'rgb(54, 162, 235)',
                tension: 0.1
            }]
        }
    }
);

// CO2チャートの初期化
const co2Chart = new Chart(
    document.getElementById('co2Chart'),
    {
        ...chartConfig,
        data: {
            datasets: [{
                label: 'CO2',
                data: [],
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }]
        }
    }
);

// データを更新する関数
function updateCharts(data) {
    const timestamp = new Date(data.timestamp);

    // 現在の値を更新
    document.getElementById('current-temp').textContent = data.temperature.toFixed(1);
    document.getElementById('current-humidity').textContent = data.humidity.toFixed(1);
    document.getElementById('current-co2').textContent = data.co2;

    // チャートデータを更新
    tempChart.data.datasets[0].data.push({
        x: timestamp,
        y: data.temperature
    });
    humidityChart.data.datasets[0].data.push({
        x: timestamp,
        y: data.humidity
    });
    co2Chart.data.datasets[0].data.push({
        x: timestamp,
        y: data.co2
    });

    // データが多すぎる場合は古いデータを削除
    const maxDataPoints = 100;
    if (tempChart.data.datasets[0].data.length > maxDataPoints) {
        tempChart.data.datasets[0].data.shift();
        humidityChart.data.datasets[0].data.shift();
        co2Chart.data.datasets[0].data.shift();
    }

    // チャートを更新
    tempChart.update();
    humidityChart.update();
    co2Chart.update();
}

// WebSocket接続
const ws = new WebSocket('ws://localhost:8765');

// WebSocketイベントハンドラ
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    updateCharts(data);
};

ws.onerror = function(error) {
    console.error('WebSocket error:', error);
};

ws.onclose = function() {
    console.log('WebSocket connection closed');
    // 接続が切れた場合は5秒後に再接続を試みる
    setTimeout(() => {
        console.log('Attempting to reconnect...');
        window.location.reload();
    }, 5000);
}; 