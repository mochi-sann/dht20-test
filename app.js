// チャートの設定
const ctx = document.getElementById('sensorChart').getContext('2d');
const chart = new Chart(ctx, {
    type: 'line',
    data: {
        datasets: [
            {
                label: 'Temperature (°C)',
                data: [],
                borderColor: 'rgb(255, 99, 132)',
                tension: 0.1
            },
            {
                label: 'Humidity (%)',
                data: [],
                borderColor: 'rgb(54, 162, 235)',
                tension: 0.1
            },
            {
                label: 'CO2 (ppm)',
                data: [],
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }
        ]
    },
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
                    text: 'Time'
                }
            },
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Value'
                }
            }
        }
    }
});

// 最新データの更新
function updateLatestData(data) {
    document.getElementById('temperature').textContent = `${data.temperature.toFixed(1)} °C`;
    document.getElementById('humidity').textContent = `${data.humidity.toFixed(1)} %`;
    document.getElementById('co2').textContent = `${data.co2} ppm`;
}

// チャートデータの更新
function updateChartData(data) {
    const timestamp = new Date(data.timestamp);
    
    chart.data.datasets[0].data.push({
        x: timestamp,
        y: data.temperature
    });
    chart.data.datasets[1].data.push({
        x: timestamp,
        y: data.humidity
    });
    chart.data.datasets[2].data.push({
        x: timestamp,
        y: data.co2
    });

    // データが多すぎる場合は古いデータを削除
    const maxDataPoints = 100;
    if (chart.data.datasets[0].data.length > maxDataPoints) {
        chart.data.datasets.forEach(dataset => {
            dataset.data.shift();
        });
    }

    chart.update();
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
        chart.data.datasets.forEach(dataset => {
            dataset.data = [];
        });

        // 履歴データを追加
        data.forEach(item => {
            const timestamp = new Date(item.timestamp);
            chart.data.datasets[0].data.push({
                x: timestamp,
                y: item.temperature
            });
            chart.data.datasets[1].data.push({
                x: timestamp,
                y: item.humidity
            });
            chart.data.datasets[2].data.push({
                x: timestamp,
                y: item.co2
            });
        });

        chart.update();
    } catch (error) {
        console.error('Error fetching history:', error);
    }
}

// 初期データの読み込み
fetchHistory();

// 定期的なデータ更新
setInterval(fetchData, 2000); 