// data for showing the line chart
console.log(chart_dates)
console.log(chart_exp)
console.log(chart_og_sp)
console.log(chart_daily_sp)

// Creating line chart
let ctx = 
document.getElementById('linechart').getContext('2d');
let linechart = new Chart(ctx, {
type: 'line',
data: {
labels: chart_dates,
datasets: [
  {
      label: 'Original Spend Avg',
      data: chart_og_sp,
      borderColor: 'blue',
      borderWidth: 2,
      fill: false,
  },
  {
      label: 'Actual Expense',
      data: chart_exp,
      borderColor: 'red',
      borderWidth: 2,
      fill: false,
  },
  {
      label: 'Daily Spend Avg',
      data: chart_daily_sp,
      borderColor: 'green',
      borderWidth: 2,
      fill: true,
  }
]
},
options: {
responsive: true,
maintainAspectRatio: false,
scales: {
  x: {
      title: {
          display: true,
          text: 'Days',
          font: {
              padding: 4,
              size: 20,
              weight: 'bold',
              family: 'Arial'
          },
          color: 'black'
      }
  },
  y: {
      title: {
          display: true,
          text: 'Dollars ($)',
          font: {
              size: 20,
              weight: 'bold',
              family: 'Arial'
          },
          color: 'black'
      },
      beginAtZero: true,
      scaleLabel: {
          display: true,
          labelString: 'Values',
      }
  }
}
}
});