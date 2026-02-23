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
  const userListEl = document.getElementById("mapUserList");

  function setMapUserListError(msg) {
    if (userListEl) userListEl.innerHTML = '<div class="map-empty-hint">' + msg + "</div>";
  }

  function initMap() {
    if (!mapEl || !window.L) return false;
    let map = L.map("map", { zoomControl: false }).setView([40.4093, 49.8671], 11);
    L.control.zoom({ position: "topright" }).addTo(map);
    let markers = {};
    let polylines = {};
    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
      maxZoom: 19,
      attribution: "© OpenStreetMap © CARTO",
      subdomains: "abcd",
    }).addTo(map);

    function getCSRFToken() {
      const cookies = document.cookie.split(";");
      for (let c of cookies) {
        const parts = c.trim().split("=");
        if (parts[0] === "csrftoken") return parts[1] || "";
      }
      return document.querySelector("[name=csrfmiddlewaretoken]")?.value || "";
    }

    function getMarkerColor(f) {
      if (f.is_paused) return "#fbbf24";
      if (f.status === "online") return "#22c55e";
      if (f.status === "offline") return "#ef4444";
      return "#6b7280";
    }

    function getStatusClass(f) {
      if (f.is_paused) return "status-paused";
      if (f.status === "online") return "status-online";
      if (f.status === "offline") return "status-offline";
      return "status-unknown";
    }

    /** Pil ikonası HTML-i */
    function batteryHTML(level) {
      if (level === null || level === undefined) return "";
      const pct = Math.max(0, Math.min(100, level));
      let color = "#22c55e";   // yaşıl
      let icon  = "🔋";
      if (pct <= 15) { color = "#ef4444"; icon = "🪫"; }
      else if (pct <= 30) { color = "#f59e0b"; }
      return `<span class="battery-badge" style="color:${color}" title="Pil: ${pct}%">${icon} ${pct}%</span>`;
    }

    async function loadMapLocations() {
      try {
        const url = "/api/movqe-son-json/";
        const res = await fetch(url, {
          credentials: "same-origin",
          headers: { "X-CSRFToken": getCSRFToken() || "" },
        });
        if (!res.ok) {
          if (res.status === 403) console.warn("[MAP] Admin girişi lazımdır");
          if (userListEl) userListEl.innerHTML = '<div class="map-empty-hint">Admin girişi lazımdır</div>';
          return;
        }
        const data = await res.json();
        const features = data.features || [];

        Object.values(markers).forEach((m) => map.removeLayer(m));
        Object.values(polylines).forEach((p) => map.removeLayer(p));
        markers = {};
        polylines = {};

        const csrf = getCSRFToken();
        for (const f of features) {
          if (!f.lat || !f.lng) continue;
          const color = getMarkerColor(f);
          const name = f.ad || f.username || "İstifadəçi";
          const m = L.circleMarker([f.lat, f.lng], {
            radius: 12,
            fillColor: color,
            color: "#fff",
            weight: 2,
            fillOpacity: 1,
          })
            .addTo(map)
            .bindPopup(
              `<div style="padding:8px;min-width:160px;">` +
              `<b>${name}</b><br>` +
              `<span style="color:#6b7280;font-size:12px;">${f.is_paused ? "Dayandırılıb" : (f.status === "online" ? "Online" : f.status || "—")}</span>` +
              (f.battery_level !== null && f.battery_level !== undefined
                ? `<br><span style="font-size:12px;">${batteryHTML(f.battery_level)}</span>`
                : "") +
              `</div>`
            );
          markers[f.id] = m;

          try {
            const rRes = await fetch("/api/routes/?user=" + f.id, {
              credentials: "same-origin",
              headers: { "X-CSRFToken": csrf || "" },
            });
            if (rRes.ok) {
              const rData = await rRes.json();
              const routes = Array.isArray(rData) ? rData : rData.results || [];
              const active = routes.find((r) => !r.end_time);
              if (active && active.points && active.points.length > 1) {
                const pts = active.points.map((p) => [parseFloat(p.latitude), parseFloat(p.longitude)]);
                const pl = L.polyline(pts, {
                  color: color,
                  weight: 4,
                  opacity: 0.8,
                  dashArray: f.is_paused ? "10,5" : null,
                }).addTo(map);
                polylines[f.id] = pl;
              }
            }
          } catch (_) {}
        }

        if (userListEl) {
          if (features.length === 0) {
            userListEl.innerHTML = '<div class="map-empty-hint">İstifadəçi yoxdur</div>';
          } else {
            userListEl.innerHTML = features
              .map((f) => {
                const hasLoc = f.lat != null && f.lng != null;
                const clickable = hasLoc ? " map-user-item-clickable" : "";
                const batHtml = batteryHTML(f.battery_level);
                return `<div class="map-user-item${clickable}" data-user-id="${f.id}" data-lat="${f.lat ?? ""}" data-lng="${f.lng ?? ""}">
                  <span class="status-dot ${getStatusClass(f)}"></span>
                  <span class="map-user-name">${f.ad || f.username || "İstifadəçi"}</span>
                  ${batHtml ? `<span class="map-user-battery">${batHtml}</span>` : ""}
                </div>`;
              })
              .join("");
            userListEl.querySelectorAll(".map-user-item-clickable").forEach((el) => {
              el.addEventListener("click", function () {
                const uid = this.dataset.userId;
                const lat = parseFloat(this.dataset.lat);
                const lng = parseFloat(this.dataset.lng);
                if (!isNaN(lat) && !isNaN(lng) && markers[uid]) {
                  const pl = polylines[uid];
                  if (pl && pl.getBounds) {
                    try {
                      const bounds = pl.getBounds();
                      map.fitBounds(bounds, { padding: [30, 30], maxZoom: 15 });
                    } catch (_) {
                      map.setView([lat, lng], 15);
                    }
                  } else {
                    map.setView([lat, lng], 15);
                  }
                  markers[uid].openPopup();
                }
              });
            });
          }
        }
      } catch (e) {
        console.warn("[MAP] Konum yüklənmədi:", e);
        if (userListEl) userListEl.innerHTML = '<div class="map-empty-hint">Yükləmə xətası</div>';
      }
    }

    loadMapLocations();
    setInterval(loadMapLocations, 10000);
    setTimeout(function () { if (map && map.invalidateSize) map.invalidateSize(); }, 500);
    return true;
  }

  if (!window.L) {
    var waitCount = 0;
    var waitL = setInterval(function () {
      waitCount++;
      if (window.L) { clearInterval(waitL); initMap(); }
      else if (waitCount > 50) { clearInterval(waitL); setMapUserListError("Xəritə kitabxanası yüklənə bilmədi."); }
    }, 100);
  } else {
    initMap();
  }
});


