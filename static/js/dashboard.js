document.addEventListener("DOMContentLoaded", function () {
  const mainChartEl = document.getElementById("mainChart");
  if (mainChartEl && window.Chart) {
    const ctx = mainChartEl.getContext("2d");
    new Chart(ctx, {
      type: "line",
      data: {
        labels: [
          "JAN",
          "FEB",
          "MAR",
          "APR",
          "MAY",
          "JUN",
          "JUL",
          "AUG",
          "SEP",
          "OCT",
          "NOV",
          "DEC",
        ],
        datasets: [
          {
            label: "Performance",
            data: [105, 75, 70, 85, 70, 85, 65, 75, 85, 90, 110, 105],
            borderColor: "#3b82f6",
            backgroundColor: "rgba(59, 130, 246, 0.1)",
            tension: 0.4,
            fill: true,
            pointRadius: 4,
            pointBackgroundColor: "#3b82f6",
            pointBorderColor: "#fff",
            pointBorderWidth: 2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false,
          },
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: {
              color: "rgba(255, 255, 255, 0.05)",
            },
            ticks: {
              color: "rgba(255, 255, 255, 0.5)",
            },
          },
          x: {
            grid: {
              display: false,
            },
            ticks: {
              color: "rgba(255, 255, 255, 0.5)",
            },
          },
        },
      },
    });
  }

  const usersChartEl = document.getElementById("usersChart");
  const routesChartEl = document.getElementById("routesChart");
  const locationsChartEl = document.getElementById("locationsChart");

  if (window.Chart) {
    if (usersChartEl) {
      new Chart(usersChartEl.getContext("2d"), {
        type: "line",
        data: {
          labels: ["JUL", "AUG", "SEP", "OCT", "NOV", "DEC"],
          datasets: [
            {
              data: [80, 95, 70, 85, 120, 150],
              borderColor: "#3b82f6",
              backgroundColor: "rgba(59, 130, 246, 0.1)",
              tension: 0.4,
              fill: true,
              pointRadius: 0,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: { y: { display: false }, x: { display: false } },
        },
      });
    }

    if (routesChartEl) {
      new Chart(routesChartEl.getContext("2d"), {
        type: "line",
        data: {
          labels: ["JUL", "AUG", "SEP", "OCT", "NOV", "DEC"],
          datasets: [
            {
              data: [55, 30, 20, 70, 95, 130],
              borderColor: "#a855f7",
              backgroundColor: "rgba(168, 85, 247, 0.1)",
              tension: 0.4,
              fill: true,
              pointRadius: 0,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: { y: { display: false }, x: { display: false } },
        },
      });
    }

    if (locationsChartEl) {
      new Chart(locationsChartEl.getContext("2d"), {
        type: "line",
        data: {
          labels: ["JUL", "AUG", "SEP", "OCT", "NOV", "DEC"],
          datasets: [
            {
              data: [120, 160, 140, 180, 220, 260],
              borderColor: "#22c55e",
              backgroundColor: "rgba(34, 197, 94, 0.1)",
              tension: 0.4,
              fill: true,
              pointRadius: 0,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: { y: { display: false }, x: { display: false } },
        },
      });
    }
  }

  const mapEl = document.getElementById("map");
  if (mapEl && window.L) {
    const map = L.map("map").setView([40.4093, 49.8671], 11); // Baku

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: "&copy; OpenStreetMap contributors",
    }).addTo(map);
  }
});


