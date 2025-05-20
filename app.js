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

// 過去のデータを取得
async function loadHistoricalData() {
    try {
        const response = await fetch('/api/history');
        const data = await response.json();
        
        // データを時系列順に並び替え
        data.reverse().forEach(updateCharts);
    } catch (error) {
        console.error('Error loading historical data:', error);
    }
}

// 最新のデータを定期的に取得
async function fetchLatestData() {
    try {
        const response = await fetch('/api/latest');
        const data = await response.json();
        updateCharts(data);
    } catch (error) {
        console.error('Error fetching latest data:', error);
    }
}

// 初期データの読み込み
loadHistoricalData();

// 2秒ごとに最新データを取得
setInterval(fetchLatestData, 2000); 