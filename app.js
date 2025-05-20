// チャートの共通設定
const chartConfig = {
    type: 'line',
    options: {
        responsive: true,
        scales: {
            x: {
                type: 'time',
                time: {
                    unit: 'minute',
                    displayFormats: {
                        minute: 'HH:mm'
                    }
                },
                title: {
                    display: true,
                    text: '時間'
                }
            },
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: '値'
                }
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
                label: '温度 (°C)',
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
                label: '湿度 (%)',
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
                label: 'CO2 (ppm)',
                data: [],
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }]
        }
    }
);

// 最新データの更新
function updateLatestData(data) {
    document.getElementById('temperature').textContent = `${data.temperature.toFixed(1)} °C`;
    document.getElementById('humidity').textContent = `${data.humidity.toFixed(1)} %`;
    document.getElementById('co2').textContent = `${data.co2} ppm`;
}

// チャートデータの更新
function updateChartData(data) {
    const timestamp = new Date(data.timestamp);

    // 温度データの更新
    tempChart.data.datasets[0].data.push({
        x: timestamp,
        y: data.temperature
    });

    // 湿度データの更新
    humidityChart.data.datasets[0].data.push({
        x: timestamp,
        y: data.humidity
    });

    // CO2データの更新
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

// データの取得と更新
async function fetchData() {
    try {
        const response = await fetch('/api/latest');
        const data = await response.json();
        updateLatestData(data);
        updateChartData(data);
    } catch (error) {
        console.error('Error fetching data:', error);
    }
}

// 履歴データの取得
async function fetchHistory() {
    try {
        const response = await fetch('/api/history');
        const data = await response.json();

        // チャートデータをクリア
        tempChart.data.datasets[0].data = [];
        humidityChart.data.datasets[0].data = [];
        co2Chart.data.datasets[0].data = [];

        // 履歴データを追加
        data.forEach(item => {
            const timestamp = new Date(item.timestamp);

            tempChart.data.datasets[0].data.push({
                x: timestamp,
                y: item.temperature
            });

            humidityChart.data.datasets[0].data.push({
                x: timestamp,
                y: item.humidity
            });

            co2Chart.data.datasets[0].data.push({
                x: timestamp,
                y: item.co2
            });
        });

        // チャートを更新
        tempChart.update();
        humidityChart.update();
        co2Chart.update();
    } catch (error) {
        console.error('Error fetching history:', error);
    }
}

// 初期データの読み込み
fetchHistory();

// 定期的なデータ更新
setInterval(fetchData, 2000);