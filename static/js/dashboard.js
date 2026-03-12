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
  const userProfileEl = document.getElementById("mapUserProfile");
  let selectedUserId = null;

  function setMapUserListError(msg) {
    if (userListEl) userListEl.innerHTML = '<div class="map-empty-hint">' + msg + "</div>";
  }

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

  function batteryHTML(level) {
    if (level === null || level === undefined) return "";
    const pct = Math.max(0, Math.min(100, level));
    let color = "#22c55e", icon = "🔋";
    if (pct <= 15) { color = "#ef4444"; icon = "🪫"; }
    else if (pct <= 30) { color = "#f59e0b"; }
    return `<span class="battery-badge" style="color:${color}" title="Pil: ${pct}%">${icon} ${pct}%</span>`;
  }

  function makeMarkerEl(color) {
    const el = document.createElement("div");
    el.style.cssText = `width:18px;height:18px;border-radius:50%;background:${color};border:3px solid #fff;box-shadow:0 2px 8px rgba(0,0,0,.4);`;
    return el;
  }

  function initMap() {
    if (!mapEl || !window.mapboxgl) return false;
    const token = window.MAPBOX_ACCESS_TOKEN;
    if (!token) { setMapUserListError("Mapbox token təyin edilməyib."); return false; }
    mapboxgl.accessToken = token;
    const map = new mapboxgl.Map({
      container: "map",
      style: "mapbox://styles/mapbox/streets-v12",
      center: [49.8671, 40.4093],
      zoom: 11,
    });
    map.addControl(new mapboxgl.NavigationControl(), "top-right");

    let markers = {};
    let polylineSourceId = null;

    async function loadMapLocations() {
      try {
        const res = await fetch("/api/movqe-son-json/", {
          credentials: "same-origin",
          headers: { "X-CSRFToken": getCSRFToken() || "" },
        });
        if (!res.ok) {
          if (userListEl) userListEl.innerHTML = '<div class="map-empty-hint">Admin girişi lazımdır</div>';
          return;
        }
        const data = await res.json();
        const features = data.features || [];

        // Markerləri yenilə
        Object.values(markers).forEach((m) => m.remove());
        markers = {};

        const pts = [];
        for (const f of features) {
          if (!f.lat || !f.lng) continue;
          const color = getMarkerColor(f);
          const name = f.ad || f.username || "İstifadəçi";
          const statusTxt = f.is_paused ? "Dayandırılıb" : (f.status === "online" ? "Online" : f.status || "—");
          const el = makeMarkerEl(color);
          const popup = new mapboxgl.Popup({ closeButton: false, offset: 14 })
            .setHTML(
              `<div style="padding:8px;min-width:180px;font-family:-apple-system,sans-serif;">` +
              `<b style="font-size:14px;">${name}</b><br>` +
              `<span style="color:#6b7280;font-size:12px;">${statusTxt}</span>` +
              (f.battery_level !== null && f.battery_level !== undefined
                ? `<br>${batteryHTML(f.battery_level)}` : "") +
              `<br><span style="font-size:11px;color:#9ca3af;">📍 ${f.lat.toFixed(5)}, ${f.lng.toFixed(5)}</span>` +
              `</div>`
            );
          markers[f.id] = new mapboxgl.Marker({ element: el, anchor: "center" })
            .setLngLat([f.lng, f.lat])
            .setPopup(popup)
            .addTo(map);
          pts.push([f.lng, f.lat]);
        }

        // Bütün markerlərə uyğun zoom
        if (pts.length > 0 && !selectedUserId) {
          const bounds = pts.reduce((b, p) => b.extend(p), new mapboxgl.LngLatBounds(pts[0], pts[0]));
          map.fitBounds(bounds, { padding: 60, maxZoom: 16 });
        }

        // Seçilmiş user-in marşrutu
        if (polylineSourceId) {
          try { map.removeLayer(polylineSourceId + "-layer"); map.removeSource(polylineSourceId); } catch (_) {}
          polylineSourceId = null;
        }
        if (selectedUserId && !features.find((x) => x.id == selectedUserId)) selectedUserId = null;

        if (selectedUserId) {
          const sel = features.find((x) => x.id == selectedUserId);
          if (sel) {
            try {
              const rRes = await fetch("/api/routes/?user=" + selectedUserId, {
                credentials: "same-origin",
                headers: { "X-CSRFToken": getCSRFToken() || "" },
              });
              if (rRes.ok) {
                const rData = await rRes.json();
                const routes = Array.isArray(rData) ? rData : rData.results || [];
                const active = routes.find((r) => !r.end_time) || routes[routes.length - 1];
                if (active && active.points && active.points.length > 1) {
                  const coords = active.points.map((p) => [parseFloat(p.longitude), parseFloat(p.latitude)]);
                  const srcId = "route-" + selectedUserId;
                  map.addSource(srcId, { type: "geojson", data: { type: "Feature", geometry: { type: "LineString", coordinates: coords } } });
                  map.addLayer({ id: srcId + "-layer", type: "line", source: srcId, paint: {
                    "line-color": getMarkerColor(sel), "line-width": 4, "line-opacity": 0.85,
                    ...( sel.is_paused ? { "line-dasharray": [2, 2] } : {} )
                  }});
                  polylineSourceId = srcId;
                  const bounds2 = coords.reduce((b, c) => b.extend(c), new mapboxgl.LngLatBounds(coords[0], coords[0]));
                  map.fitBounds(bounds2, { padding: 60, maxZoom: 16 });
                  if (userProfileEl) {
                    const startT = active.start_time ? new Date(active.start_time).toLocaleString("az-AZ") : "—";
                    const endT = active.end_time ? new Date(active.end_time).toLocaleString("az-AZ") : "Davam edir";
                    userProfileEl.innerHTML = `<div class="map-user-profile-box"><div class="map-user-profile-title"><i class="fas fa-route"></i> ${sel.ad || sel.username} — Marşrut</div><div class="map-user-profile-row">Başlanğıc: ${startT}</div><div class="map-user-profile-row">Bitmə: ${endT}</div><div class="map-user-profile-row">Nöqtələr: ${active.points.length}</div></div>`;
                    userProfileEl.style.display = "block";
                  }
                } else if (userProfileEl) {
                  userProfileEl.innerHTML = `<div class="map-user-profile-box"><div class="map-user-profile-title">${sel.ad || sel.username} — Marşrut yoxdur</div></div>`;
                  userProfileEl.style.display = "block";
                }
              }
            } catch (_) {}
            if (markers[selectedUserId]) markers[selectedUserId].togglePopup();
          } else if (userProfileEl) userProfileEl.style.display = "none";
        } else if (userProfileEl) userProfileEl.style.display = "none";

        // Siyahı
        if (userListEl) {
          if (features.length === 0) {
            userListEl.innerHTML = '<div class="map-empty-hint">İstifadəçi yoxdur</div>';
          } else {
            userListEl.innerHTML = features.map((f) => {
              const hasLoc = f.lat != null && f.lng != null;
              const clickable = hasLoc ? " map-user-item-clickable" : "";
              const bat = batteryHTML(f.battery_level);
              const isSelected = f.id == selectedUserId;
              return `<div class="map-user-item${clickable}${isSelected ? " selected" : ""}" data-user-id="${f.id}" data-lat="${f.lat ?? ""}" data-lng="${f.lng ?? ""}">
                <span class="status-dot ${getStatusClass(f)}"></span>
                <span class="map-user-name">${f.ad || f.username || "İstifadəçi"}</span>
                ${bat ? `<span class="map-user-battery">${bat}</span>` : ""}
              </div>`;
            }).join("");
            userListEl.querySelectorAll(".map-user-item-clickable").forEach((el) => {
              el.addEventListener("click", function () {
                const uid = this.dataset.userId;
                const lat = parseFloat(this.dataset.lat);
                const lng = parseFloat(this.dataset.lng);
                selectedUserId = selectedUserId == uid ? null : uid;
                loadMapLocations();
                if (!selectedUserId && !isNaN(lat) && !isNaN(lng)) {
                  map.flyTo({ center: [lng, lat], zoom: 15, speed: 1.4 });
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

    map.on("load", function () {
      loadMapLocations();
      setInterval(loadMapLocations, 10000);
    });
    return true;
  }

  function tryInit() {
    const token = window.MAPBOX_ACCESS_TOKEN;
    if (window.mapboxgl && token) {
      const r = initMap();
      if (r) return;
    }
    if (window.L) initLeaflet();
    else setMapUserListError("Xəritə yüklənə bilmədi.");
  }

  var waitCount = 0;
  var t = setInterval(function () {
    waitCount++;
    if (window.mapboxgl || window.L) {
      clearInterval(t);
      tryInit();
    } else if (waitCount > 30) {
      clearInterval(t);
      if (window.L) initLeaflet();
      else setMapUserListError("Xəritə yüklənə bilmədi.");
    }
  }, 100);

  function initLeaflet() {
    if (!mapEl || !window.L) return false;
    const map = L.map("map", { zoomControl: false }).setView([40.4093, 49.8671], 11);
    L.control.zoom({ position: "topright" }).addTo(map);
    L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", {
      maxZoom: 19,
      attribution: "© OpenStreetMap © CARTO"
    }).addTo(map);
    let markers = {};
    let polylines = {};
    const popupHtml = (f) => `<div style="padding:8px;min-width:180px;"><b>${f.ad || f.username || "İstifadəçi"}</b><br><span style="color:#6b7280;font-size:12px;">${f.is_paused ? "Dayandırılıb" : (f.status === "online" ? "Online" : f.status || "—")}</span>${f.battery_level != null ? "<br>" + batteryHTML(f.battery_level) : ""}<br><span style="font-size:11px;color:#9ca3af;">📍 ${f.lat.toFixed(5)}, ${f.lng.toFixed(5)}</span></div>`;
    async function load() {
      try {
        const res = await fetch("/api/movqe-son-json/", { credentials: "same-origin", headers: { "X-CSRFToken": getCSRFToken() || "" } });
        if (!res.ok) { if (userListEl) userListEl.innerHTML = '<div class="map-empty-hint">Admin girişi lazımdır</div>'; return; }
        const data = await res.json();
        const features = data.features || [];
        Object.values(markers).forEach((m) => map.removeLayer(m));
        Object.values(polylines).forEach((p) => map.removeLayer(p));
        markers = {};
        polylines = {};
        const pts = [];
        for (const f of features) {
          if (!f.lat || !f.lng) continue;
          const color = getMarkerColor(f);
          const m = L.circleMarker([f.lat, f.lng], { radius: 12, fillColor: color, color: "#fff", weight: 2, fillOpacity: 1 }).addTo(map).bindPopup(popupHtml(f));
          markers[f.id] = m;
          pts.push([f.lat, f.lng]);
        }
        if (pts.length > 0 && !selectedUserId) {
          try { map.fitBounds(L.latLngBounds(pts), { padding: [40, 40], maxZoom: 16 }); } catch (_) {}
        }
        if (selectedUserId) {
          const sel = features.find((x) => x.id == selectedUserId);
          if (sel) {
            try {
              const rRes = await fetch("/api/routes/?user=" + selectedUserId, { credentials: "same-origin", headers: { "X-CSRFToken": getCSRFToken() || "" } });
              if (rRes.ok) {
                const rData = await rRes.json();
                const routes = Array.isArray(rData) ? rData : rData.results || [];
                const active = routes.find((r) => !r.end_time) || routes[routes.length - 1];
                if (active && active.points && active.points.length > 1) {
                  const linePts = active.points.map((p) => [parseFloat(p.latitude), parseFloat(p.longitude)]);
                  polylines[selectedUserId] = L.polyline(linePts, { color: getMarkerColor(sel), weight: 4, opacity: 0.8, dashArray: sel.is_paused ? "10,5" : null }).addTo(map);
                  map.fitBounds(L.latLngBounds(linePts), { padding: [40, 40], maxZoom: 16 });
                  if (userProfileEl) { userProfileEl.innerHTML = `<div class="map-user-profile-box"><div class="map-user-profile-title"><i class="fas fa-route"></i> ${sel.ad || sel.username} — Marşrut</div></div>`; userProfileEl.style.display = "block"; }
                }
              }
            } catch (_) {}
            if (markers[selectedUserId]) markers[selectedUserId].openPopup();
          } else if (userProfileEl) userProfileEl.style.display = "none";
        } else if (userProfileEl) userProfileEl.style.display = "none";
        if (userListEl) {
          if (features.length === 0) userListEl.innerHTML = '<div class="map-empty-hint">İstifadəçi yoxdur</div>';
          else {
            userListEl.innerHTML = features.map((f) => { const hasLoc = f.lat != null && f.lng != null; const c = hasLoc ? " map-user-item-clickable" : ""; const bat = batteryHTML(f.battery_level); const sel = f.id == selectedUserId ? " selected" : ""; return `<div class="map-user-item${c}${sel}" data-user-id="${f.id}" data-lat="${f.lat ?? ""}" data-lng="${f.lng ?? ""}"><span class="status-dot ${getStatusClass(f)}"></span><span class="map-user-name">${f.ad || f.username || "İstifadəçi"}</span>${bat ? `<span class="map-user-battery">${bat}</span>` : ""}</div>`; }).join("");
            userListEl.querySelectorAll(".map-user-item-clickable").forEach((el) => {
              el.addEventListener("click", function () {
                const uid = this.dataset.userId, lat = parseFloat(this.dataset.lat), lng = parseFloat(this.dataset.lng);
                selectedUserId = selectedUserId == uid ? null : uid;
                document.querySelectorAll(".map-user-item").forEach((e) => e.classList.remove("selected"));
                if (selectedUserId) this.classList.add("selected");
                load().then(function () { if (!isNaN(lat) && !isNaN(lng) && markers[uid]) { map.setView([lat, lng], 15); markers[uid].openPopup(); } });
              });
            });
          }
        }
      } catch (e) { if (userListEl) userListEl.innerHTML = '<div class="map-empty-hint">Yükləmə xətası</div>'; }
    }
    load();
    setInterval(load, 10000);
    return true;
  }
});


