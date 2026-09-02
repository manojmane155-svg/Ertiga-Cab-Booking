// ----------------- GLOBAL STATE ----------------- //
let map, pickupMarker, dropMarker, routeLine;
let selectedPaymentMethod = "UPI";
let currentFareData = {
  distance_km: 15.0,
  rate_per_km: 15.0,
  total_amount: 225.0
};
let currentUser = null;
let currentOtpCode = "";
let currentActiveTab = "map";
let pageLastNotificationId = 0;
let isAudioUnlocked = false;
let currentCancelBookingRef = null;

// Default Landmark Coordinates
const LANDMARK_COORDS = {
  "Pune Railway Station": [18.5284, 73.8744],
  "Pune Airport (PNQ), Lohegaon": [18.5822, 73.9197],
  "Swargate Bus Stand": [18.5018, 73.8587],
  "Hinjewadi Phase 1, IT Park": [18.5913, 73.7389],
  "Hinjewadi Phase 3": [18.5833, 73.6933],
  "Shivaji Nagar, Pune": [18.5314, 73.8446],
  "Kothrud, Chandani Chowk": [18.5074, 73.7925],
  "Hadapsar / Magarpatta City": [18.5089, 73.9260],
  "Viman Nagar": [18.5679, 73.9143],
  "Wakad, Pune": [18.5987, 73.7688],
  "Baner, Pune": [18.5590, 73.7868],
  "Pimpri Chinchwad": [18.6279, 73.8009],
  "Lonavala": [18.7557, 73.4091],
  "Khandala": [18.7614, 73.3740],
  "Mahabaleshwar": [17.9237, 73.6586],
  "Alibaug Beach": [18.6414, 72.8722],
  "Navi Mumbai (Vashi)": [19.0771, 72.9986],
  "Mumbai Airport (T2), CSMIA": [19.0974, 72.8745],
  "Dadar, Mumbai": [19.0178, 72.8478],
  "Shirdi Sai Baba Temple": [19.7667, 74.4762]
};

// ----------------- AUDIO CHIME (WEB AUDIO API) ----------------- //
function playAlertChime() {
  try {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) return;
    const ctx = new AudioContext();
    const now = ctx.currentTime;
    const osc1 = ctx.createOscillator();
    const osc2 = ctx.createOscillator();
    const gain = ctx.createGain();

    osc1.type = "sine";
    osc1.frequency.setValueAtTime(587.33, now); // D5
    osc1.frequency.setValueAtTime(880.00, now + 0.15); // A5

    osc2.type = "triangle";
    osc2.frequency.setValueAtTime(440.00, now); // A4
    osc2.frequency.setValueAtTime(659.25, now + 0.15); // E5

    gain.gain.setValueAtTime(0.3, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.6);

    osc1.connect(gain);
    osc2.connect(gain);
    gain.connect(ctx.destination);

    osc1.start(now);
    osc2.start(now);
    osc1.stop(now + 0.6);
    osc2.stop(now + 0.6);
  } catch (e) {
    console.log("Audio chime error:", e);
  }
}

document.addEventListener("click", () => {
  isAudioUnlocked = true;
}, { once: true });

// ----------------- INITIALIZATION ----------------- //
document.addEventListener("DOMContentLoaded", () => {
  initMap();
  initDatePicker();
  checkCurrentUser();
  checkCabStatus();
  recalculateRoute();
  loadPageBookings();
  loadPageDriverData();

  // Listeners for location change
  document.getElementById("pickupInput").addEventListener("change", recalculateRoute);
  document.getElementById("dropInput").addEventListener("change", recalculateRoute);

  // Check URL params for active tab
  const urlParams = new URLSearchParams(window.location.search);
  const tabParam = urlParams.get("tab");
  if (tabParam && ["map", "rides", "driver"].includes(tabParam)) {
    switchRightTab(tabParam);
  }

  // Periodic refresh for bookings & notifications
  setInterval(() => {
    if (currentActiveTab === "driver") {
      loadPageDriverData();
    } else if (currentActiveTab === "rides") {
      loadPageBookings();
    }
    checkNewNotificationsBackground();
  }, 5000);
});

// ----------------- TAB SWITCHER (ALL IN ONE PAGE) ----------------- //
function switchRightTab(tabName) {
  currentActiveTab = tabName;

  // Buttons
  document.querySelectorAll(".dash-tab-btn").forEach(btn => btn.classList.remove("active"));
  document.querySelectorAll(".tab-view").forEach(view => view.classList.remove("active"));

  if (tabName === "map") {
    document.getElementById("tabBtnMap").classList.add("active");
    document.getElementById("viewMap").classList.add("active");
    // Ensure Leaflet recalculates dimensions smoothly
    setTimeout(() => {
      if (map) map.invalidateSize();
    }, 150);
  } else if (tabName === "rides") {
    document.getElementById("tabBtnRides").classList.add("active");
    document.getElementById("viewRides").classList.add("active");
    loadPageBookings();
  } else if (tabName === "driver") {
    document.getElementById("tabBtnDriver").classList.add("active");
    document.getElementById("viewDriver").classList.add("active");
    document.getElementById("driverLiveAlertBadge").style.display = "none";
    loadPageDriverData();
  }
}

// ----------------- MAP SETUP (LEAFLET) ----------------- //
function initMap() {
  map = L.map("map").setView([18.5204, 73.8567], 12);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors | Ertiga MH12 TV 1292 | Manoj Mane'
  }).addTo(map);

  const pickupIcon = L.divIcon({
    className: "custom-pin",
    html: '<div style="background:#10b981; color:#fff; width:30px; height:30px; border-radius:50%; display:flex; align-items:center; justify-content:center; border:2px solid #fff; box-shadow:0 2px 6px rgba(0,0,0,0.3); font-weight:bold; font-size:12px;">📍A</div>',
    iconSize: [30, 30],
    iconAnchor: [15, 30]
  });

  const dropIcon = L.divIcon({
    className: "custom-pin",
    html: '<div style="background:#ef4444; color:#fff; width:30px; height:30px; border-radius:50%; display:flex; align-items:center; justify-content:center; border:2px solid #fff; box-shadow:0 2px 6px rgba(0,0,0,0.3); font-weight:bold; font-size:12px;">🏁B</div>',
    iconSize: [30, 30],
    iconAnchor: [15, 30]
  });

  pickupMarker = L.marker([18.5284, 73.8744], { icon: pickupIcon, draggable: true }).addTo(map);
  dropMarker = L.marker([18.5822, 73.9197], { icon: dropIcon, draggable: true }).addTo(map);

  pickupMarker.bindPopup("<b>Pickup Location</b><br>Pune Railway Station");
  dropMarker.bindPopup("<b>Destination</b><br>Pune Airport (PNQ)");

  pickupMarker.on("dragend", onMarkerDrag);
  dropMarker.on("dragend", onMarkerDrag);

  // Invalidate size once map element settles
  setTimeout(() => {
    map.invalidateSize();
  }, 300);
}

function onMarkerDrag() {
  const pPos = pickupMarker.getLatLng();
  const dPos = dropMarker.getLatLng();
  
  const dLat = (dPos.lat - pPos.lat) * Math.PI / 180;
  const dLon = (dPos.lng - pPos.lng) * Math.PI / 180;
  const a = Math.sin(dLat / 2) ** 2 +
            Math.cos(pPos.lat * Math.PI / 180) * Math.cos(dPos.lat * Math.PI / 180) *
            Math.sin(dLon / 2) ** 2;
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  const km = Math.max(Math.round((6371 * c * 1.3) * 10) / 10, 3.0);

  updateRouteDisplay(pPos, dPos, km);
}

function updateRouteDisplay(pCoords, dCoords, distanceKm) {
  if (routeLine) {
    map.removeLayer(routeLine);
  }

  routeLine = L.polyline([pCoords, dCoords], {
    color: "#00c853",
    weight: 5,
    opacity: 0.85,
    dashArray: "8, 6"
  }).addTo(map);

  map.fitBounds(routeLine.getBounds(), { padding: [40, 40] });

  const rate = 15.0;
  const total = Math.round(distanceKm * rate);

  currentFareData = {
    distance_km: distanceKm,
    rate_per_km: rate,
    total_amount: total
  };

  document.getElementById("displayDistance").innerText = `${distanceKm} KM`;
  document.getElementById("displayFormula").innerText = `${distanceKm} KM × ₹15 / KM`;
  document.getElementById("displayTotalFare").innerText = `₹${total.toLocaleString("en-IN")}`;
  
  const estMins = Math.round(distanceKm * 2.2) + 8;
  const h = Math.floor(estMins / 60);
  const m = estMins % 60;
  document.getElementById("displayDuration").innerText = h > 0 ? `${h}h ${m}m` : `${m} mins`;

  document.getElementById("bookNowBtn").innerHTML = `<i class="fa-solid fa-circle-check"></i> Book Ertiga Cab (₹${total.toLocaleString("en-IN")})`;
}

async function recalculateRoute() {
  const pickup = document.getElementById("pickupInput").value.trim();
  const drop = document.getElementById("dropInput").value.trim();

  let pCoords = LANDMARK_COORDS[pickup] || [18.5284, 73.8744];
  let dCoords = LANDMARK_COORDS[drop] || [18.5822, 73.9197];

  pickupMarker.setLatLng(pCoords).bindPopup(`<b>Pickup:</b> ${pickup}`);
  dropMarker.setLatLng(dCoords).bindPopup(`<b>Destination:</b> ${drop}`);

  try {
    const res = await fetch("/api/calculate-fare", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pickup, drop })
    });
    const data = await res.json();
    if (data.success) {
      updateRouteDisplay(pCoords, dCoords, data.distance_km);
    }
  } catch (err) {
    console.error("Fare calculation error:", err);
  }
}

// ----------------- DATE & TIME INITIALIZER ----------------- //
function initDatePicker() {
  const dateInput = document.getElementById("pickupDate");
  const today = new Date().toISOString().split("T")[0];
  dateInput.min = today;
  dateInput.value = today;
}

// ----------------- PAYMENT SELECTION ----------------- //
function selectPaymentMethod(method) {
  selectedPaymentMethod = method;
  document.querySelectorAll(".payment-option").forEach(el => {
    if (el.getAttribute("data-method") === method) {
      el.classList.add("selected");
    } else {
      el.classList.remove("selected");
    }
  });
}

// ----------------- CAB AVAILABILITY CHECK ----------------- //
async function checkCabStatus() {
  try {
    const res = await fetch("/api/driver-info");
    const data = await res.json();
    if (data.success) {
      const isOnline = data.driver.is_online;
      const badge = document.getElementById("cabAvailabilityBadge");
      const text = document.getElementById("cabStatusText");
      const btn = document.getElementById("bookNowBtn");
      const pageToggle = document.getElementById("pageOnlineToggle");
      const pageLabel = document.getElementById("pageDriverAvailabilityLabel");

      if (pageToggle) pageToggle.checked = isOnline;
      if (pageLabel) {
        pageLabel.innerText = isOnline ? "ONLINE & READY" : "OFFLINE (PAUSED)";
        pageLabel.style.color = isOnline ? "#34d399" : "#ef4444";
      }

      if (isOnline) {
        badge.style.background = "#dcfce7";
        badge.style.color = "#15803d";
        text.innerText = "Ertiga MH12 TV 1292 Available Now";
        btn.disabled = false;
      } else {
        badge.style.background = "#fee2e2";
        badge.style.color = "#b91c1c";
        text.innerText = "Manoj Mane is Currently Offline";
        btn.disabled = true;
        btn.innerHTML = `<i class="fa-solid fa-ban"></i> Cab Currently Offline`;
      }
    }
  } catch (e) {
    console.error("Cab status check error:", e);
  }
}

async function toggleCabAvailability(isOnline) {
  try {
    const res = await fetch("/api/driver/toggle-status", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ is_online: isOnline })
    });
    const data = await res.json();
    if (data.success) {
      checkCabStatus();
    }
  } catch (e) {
    alert("Error updating availability: " + e.message);
  }
}

// ----------------- AUTH & OTP HANDLING ----------------- //
function openLoginModal() {
  document.getElementById("loginModal").style.display = "flex";
  document.getElementById("otpStep1").style.display = "block";
  document.getElementById("otpStep2").style.display = "none";
}

function closeLoginModal() {
  document.getElementById("loginModal").style.display = "none";
}

async function requestOtp() {
  const mobile = document.getElementById("modalUserMobile").value.trim();
  const name = document.getElementById("modalUserName").value.trim();

  if (!mobile || mobile.length < 10) {
    alert("Please enter a valid 10-digit mobile number");
    return;
  }

  try {
    const res = await fetch("/api/auth/send-otp", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mobile, name })
    });
    const data = await res.json();

    if (data.success) {
      currentOtpCode = data.otp;
      document.getElementById("otpSentMobileText").innerText = `+91 ${data.mobile}`;
      document.getElementById("demoOtpNumber").innerText = data.otp;
      document.getElementById("otpStep1").style.display = "none";
      document.getElementById("otpStep2").style.display = "block";
    } else {
      alert("Error: " + data.message);
    }
  } catch (err) {
    alert("Failed to send OTP: " + err.message);
  }
}

function autoFillOtp() {
  if (!currentOtpCode) currentOtpCode = "123456";
  for (let i = 0; i < 6; i++) {
    const input = document.getElementById(`otp${i + 1}`);
    if (input) input.value = currentOtpCode[i] || "0";
  }
}

function moveOtpFocus(current, nextId) {
  if (current.value.length >= 1 && nextId) {
    document.getElementById(nextId).focus();
  }
}

async function verifyOtpCode() {
  const mobile = document.getElementById("modalUserMobile").value.trim();
  const name = document.getElementById("modalUserName").value.trim();
  
  let enteredOtp = "";
  for (let i = 1; i <= 6; i++) {
    enteredOtp += document.getElementById(`otp${i}`).value;
  }

  if (enteredOtp.length !== 6) {
    alert("Please enter full 6-digit OTP code");
    return;
  }

  try {
    const res = await fetch("/api/auth/verify-otp", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mobile, otp: enteredOtp, name })
    });
    const data = await res.json();

    if (data.success) {
      currentUser = data.user;
      localStorage.setItem("ertiga_user_mobile", currentUser.mobile);
      localStorage.setItem("ertiga_user_name", currentUser.name);

      document.getElementById("passengerName").value = currentUser.name;
      document.getElementById("passengerMobile").value = currentUser.mobile;
      document.getElementById("pageSearchMobileInput").value = currentUser.mobile;

      updateUserNav();
      closeLoginModal();
      loadPageBookings();
    } else {
      alert("Verification Failed: " + data.message);
    }
  } catch (err) {
    alert("Verification error: " + err.message);
  }
}

function updateUserNav() {
  const navContainer = document.getElementById("userProfileNav");
  if (currentUser) {
    navContainer.innerHTML = `
      <div class="user-badge">
        <i class="fa-solid fa-user-circle"></i>
        <span>${currentUser.name} (+91 ${currentUser.mobile})</span>
        <a href="javascript:void(0)" onclick="logoutUser()" style="color:#ef4444; font-size:0.75rem; text-decoration:underline; margin-left:6px;">Logout</a>
      </div>
    `;
  }
}

async function checkCurrentUser() {
  try {
    const res = await fetch("/api/auth/current-user");
    const data = await res.json();
    if (data.logged_in) {
      currentUser = data.user;
      document.getElementById("passengerName").value = currentUser.name;
      document.getElementById("passengerMobile").value = currentUser.mobile;
      document.getElementById("pageSearchMobileInput").value = currentUser.mobile;
      updateUserNav();
    } else {
      const savedMobile = localStorage.getItem("ertiga_user_mobile");
      const savedName = localStorage.getItem("ertiga_user_name");
      if (savedMobile) {
        document.getElementById("passengerMobile").value = savedMobile;
        document.getElementById("pageSearchMobileInput").value = savedMobile;
      }
      if (savedName) document.getElementById("passengerName").value = savedName;
    }
  } catch (e) {
    console.error("User check error:", e);
  }
}

async function logoutUser() {
  await fetch("/api/auth/logout", { method: "POST" });
  currentUser = null;
  localStorage.removeItem("ertiga_user_mobile");
  localStorage.removeItem("ertiga_user_name");
  window.location.reload();
}

// ----------------- BOOKING FLOW ----------------- //
async function proceedToBooking() {
  const name = document.getElementById("passengerName").value.trim();
  const mobile = document.getElementById("passengerMobile").value.trim();
  const pickup = document.getElementById("pickupInput").value.trim();
  const drop = document.getElementById("dropInput").value.trim();
  const date = document.getElementById("pickupDate").value;
  const timeSlot = document.getElementById("pickupTimeSlot").value;

  if (!name) {
    alert("Please enter Passenger Name.");
    document.getElementById("passengerName").focus();
    return;
  }
  if (!mobile || mobile.length < 10) {
    alert("Please enter a valid 10-digit mobile number.");
    document.getElementById("passengerMobile").focus();
    return;
  }
  if (!pickup || !drop) {
    alert("Please select both Pickup and Destination.");
    return;
  }
  if (!date) {
    alert("Please select onboard pickup date.");
    return;
  }

  localStorage.setItem("ertiga_user_name", name);
  localStorage.setItem("ertiga_user_mobile", mobile);

  const payload = {
    user_name: name,
    user_mobile: mobile,
    pickup_location: pickup,
    drop_location: drop,
    distance_km: currentFareData.distance_km,
    onboard_date: date,
    onboard_time: timeSlot,
    payment_method: selectedPaymentMethod
  };

  const btn = document.getElementById("bookNowBtn");
  btn.disabled = true;
  btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Booking Cab & Notifying Manoj Mane...`;

  try {
    const res = await fetch("/api/bookings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    if (data.success) {
      playAlertChime();
      showBookingConfirmation(data.booking, data.notification);
      loadPageBookings();
      loadPageDriverData();
    } else {
      alert("Booking failed: " + data.message);
    }
  } catch (err) {
    alert("Booking request error: " + err.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<i class="fa-solid fa-circle-check"></i> Book Ertiga Cab (₹${currentFareData.total_amount.toLocaleString("en-IN")})`;
  }
}

function showBookingConfirmation(booking, notif) {
  const receiptContainer = document.getElementById("bookingReceipt");
  
  receiptContainer.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1.5px dashed #cbd5e1; padding-bottom:10px;">
      <div>
        <div style="font-size:0.75rem; color:#6b7280; text-transform:uppercase;">Booking Reference</div>
        <div style="font-size:1.25rem; font-weight:800; color:#111827;">${booking.booking_ref}</div>
      </div>
      <span class="owner-reg-tag" style="font-size:0.85rem; padding:4px 10px;">MH12 TV 1292</span>
    </div>

    <div class="ticket-row">
      <span>Driver & Cab:</span>
      <span class="ticket-val">Manoj Mane (Maruti Ertiga 6+1 AC)</span>
    </div>
    <div class="ticket-row">
      <span>Passenger:</span>
      <span class="ticket-val">${booking.user_name} (+91 ${booking.user_mobile})</span>
    </div>
    <div class="ticket-row">
      <span>Pickup:</span>
      <span class="ticket-val">${booking.pickup_location}</span>
    </div>
    <div class="ticket-row">
      <span>Drop:</span>
      <span class="ticket-val">${booking.drop_location}</span>
    </div>
    <div class="ticket-row">
      <span>Onboard Time:</span>
      <span class="ticket-val" style="color:#0284c7;">${booking.onboard_date} at ${booking.onboard_time}</span>
    </div>
    <div class="ticket-row">
      <span>Distance & Rate:</span>
      <span class="ticket-val">${booking.distance_km} KM × ₹15/KM</span>
    </div>
    <div class="ticket-row" style="border-top:1px solid #e2e8f0; padding-top:8px;">
      <span style="font-weight:700; font-size:1rem;">Total Fare Amount:</span>
      <span style="font-size:1.3rem; font-weight:800; color:#15803d;">₹${booking.fare_amount.toLocaleString('en-IN')}</span>
    </div>
    <div class="ticket-row">
      <span>Payment Option:</span>
      <span class="ticket-val">${booking.payment_method} (${booking.payment_status})</span>
    </div>
  `;

  if (notif && notif.whatsapp_url) {
    document.getElementById("whatsappShareBtn").href = notif.whatsapp_url;
  }

  document.getElementById("confirmModal").style.display = "flex";
}

function closeConfirmModal() {
  document.getElementById("confirmModal").style.display = "none";
}

// ----------------- IN-PAGE MY RIDES & CANCELLATION ----------------- //
async function loadPageBookings() {
  const container = document.getElementById("pageBookingsContainer");
  const searchMobile = document.getElementById("pageSearchMobileInput").value.trim();
  let url = "/api/user/bookings";
  if (searchMobile) {
    url += "?mobile=" + encodeURIComponent(searchMobile);
  }

  try {
    const res = await fetch(url);
    const data = await res.json();
    
    const count = data.bookings ? data.bookings.length : 0;
    document.getElementById("myRidesCountBadge").innerText = count;

    if (!data.bookings || data.bookings.length === 0) {
      container.innerHTML = `
        <div style="text-align:center; padding: 40px 20px; background:#f8fafc; border-radius:12px; border:1px dashed #cbd5e1;">
          <i class="fa-solid fa-car-rear fa-2x" style="color:#9ca3af; margin-bottom:10px;"></i>
          <h4 style="color:#374151;">No Bookings Found</h4>
          <p style="color:#6b7280; font-size:0.85rem; margin-top:4px;">No rides placed with this mobile number yet.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = data.bookings.map(b => {
      const isCancellable = b.booking_status === 'Confirmed' || b.booking_status === 'Driver Assigned';
      const statusColor = b.booking_status === 'Confirmed' ? '#15803d' :
                          b.booking_status === 'Cancelled' ? '#b91c1c' :
                          b.booking_status === 'Completed' ? '#0369a1' : '#b45309';
      const statusBg = b.booking_status === 'Confirmed' ? '#dcfce7' :
                       b.booking_status === 'Cancelled' ? '#fee2e2' :
                       b.booking_status === 'Completed' ? '#e0f2fe' : '#fef3c7';

      return `
        <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:12px; padding:16px; box-shadow:0 1px 3px rgba(0,0,0,0.05); display:flex; flex-direction:column; gap:10px;">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
              <strong style="font-size:1rem; color:#111827;">${b.booking_ref}</strong>
              <span style="font-size:0.75rem; color:#6b7280; margin-left:8px;">${b.created_at}</span>
            </div>
            <span style="background:${statusBg}; color:${statusColor}; font-weight:700; font-size:0.75rem; padding:3px 8px; border-radius:12px;">
              ${b.booking_status}
            </span>
          </div>

          <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; font-size:0.85rem;">
            <div>
              <div style="font-size:0.75rem; color:#6b7280;"><i class="fa-solid fa-circle" style="color:#10b981; font-size:8px;"></i> PICKUP</div>
              <strong>${b.pickup_location}</strong>
            </div>
            <div>
              <div style="font-size:0.75rem; color:#6b7280;"><i class="fa-solid fa-location-dot" style="color:#ef4444; font-size:9px;"></i> DROP</div>
              <strong>${b.drop_location}</strong>
            </div>
            <div>
              <div style="font-size:0.75rem; color:#6b7280;">📅 ONBOARD TIME</div>
              <span>${b.onboard_date} (${b.onboard_time})</span>
            </div>
            <div>
              <div style="font-size:0.75rem; color:#6b7280;">🚘 CAB & DRIVER</div>
              <span>Ertiga (MH12 TV 1292) • Manoj Mane</span>
            </div>
          </div>

          <div style="background:#f8fafc; border-radius:8px; padding:10px 12px; display:flex; justify-content:space-between; align-items:center;">
            <div style="font-size:0.8rem; color:#475569;">
              ${b.distance_km} KM @ ₹15/km • ${b.payment_method} (${b.payment_status})
            </div>
            <div style="font-size:1.15rem; font-weight:800; color:#15803d;">
              ₹${b.fare_amount.toLocaleString('en-IN')}
            </div>
          </div>

          ${b.booking_status === 'Cancelled' ? `
            <div style="font-size:0.78rem; color:#991b1b; background:#fef2f2; padding:6px 10px; border-radius:6px;">
              <i class="fa-solid fa-circle-info"></i> Cancelled. Reason: <em>${b.cancel_reason || 'Customer request'}</em>
            </div>
          ` : ''}

          ${isCancellable ? `
            <div style="display:flex; justify-content:flex-end;">
              <button class="btn-danger" onclick="openPageCancelModal('${b.booking_ref}')">
                <i class="fa-solid fa-xmark"></i> Cancel Booking
              </button>
            </div>
          ` : ''}
        </div>
      `;
    }).join('');
  } catch (err) {
    container.innerHTML = `<div style="color:#ef4444; text-align:center;">Error loading bookings: ${err.message}</div>`;
  }
}

function openPageCancelModal(ref) {
  currentCancelBookingRef = ref;
  document.getElementById("pageCancelModalRef").innerText = ref;
  document.getElementById("pageCancelModal").style.display = "flex";
}

function closePageCancelModal() {
  document.getElementById("pageCancelModal").style.display = "none";
  currentCancelBookingRef = null;
}

async function confirmPageCancellation() {
  if (!currentCancelBookingRef) return;
  const reason = document.getElementById("pageCancelReasonSelect").value;

  try {
    const res = await fetch(`/api/bookings/${currentCancelBookingRef}/cancel`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason })
    });
    const data = await res.json();
    if (data.success) {
      alert(`Booking ${currentCancelBookingRef} has been cancelled.`);
      closePageCancelModal();
      loadPageBookings();
      loadPageDriverData();
    } else {
      alert("Cancellation failed: " + data.message);
    }
  } catch (err) {
    alert("Error: " + err.message);
  }
}

// ----------------- IN-PAGE DRIVER CONSOLE (MANOJ MANE) ----------------- //
async function loadPageDriverData() {
  const tbody = document.getElementById("pageDriverBookingsTbody");
  try {
    const res = await fetch("/api/driver/bookings");
    const data = await res.json();

    if (!data.bookings || data.bookings.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:20px; color:#9ca3af;">No bookings recorded yet.</td></tr>`;
      return;
    }

    let totalDist = 0;
    let totalEarnings = 0;

    tbody.innerHTML = data.bookings.map(b => {
      if (b.booking_status !== 'Cancelled') {
        totalDist += b.distance_km;
        totalEarnings += b.fare_amount;
      }

      const statusBadge = 
        b.booking_status === 'Confirmed' ? '<span style="background:#dcfce7; color:#15803d; padding:2px 6px; border-radius:10px; font-weight:700; font-size:0.72rem;">CONFIRMED</span>' :
        b.booking_status === 'Driver Assigned' ? '<span style="background:#fef3c7; color:#b45309; padding:2px 6px; border-radius:10px; font-weight:700; font-size:0.72rem;">ASSIGNED</span>' :
        b.booking_status === 'Arrived at Pickup' ? '<span style="background:#e0e7ff; color:#4338ca; padding:2px 6px; border-radius:10px; font-weight:700; font-size:0.72rem;">ARRIVED</span>' :
        b.booking_status === 'Trip Started' ? '<span style="background:#fae8ff; color:#86198f; padding:2px 6px; border-radius:10px; font-weight:700; font-size:0.72rem;">ON TRIP</span>' :
        b.booking_status === 'Completed' ? '<span style="background:#e0f2fe; color:#0369a1; padding:2px 6px; border-radius:10px; font-weight:700; font-size:0.72rem;">COMPLETED</span>' :
        '<span style="background:#fee2e2; color:#b91c1c; padding:2px 6px; border-radius:10px; font-weight:700; font-size:0.72rem;">CANCELLED</span>';

      const customerClean = b.user_mobile.replace(/[^0-9]/g, '');

      return `
        <tr style="border-bottom:1px solid #f3f4f6;">
          <td style="padding:8px; font-weight:800; color:#111827;">${b.booking_ref}</td>
          <td style="padding:8px;">
            <strong>${b.user_name}</strong>
            <div style="display:flex; gap:6px; margin-top:2px;">
              <a href="tel:${b.user_mobile}" style="color:#0284c7; font-size:0.75rem; text-decoration:none;"><i class="fa-solid fa-phone"></i> +91 ${customerClean}</a>
              <a href="https://wa.me/91${customerClean}" target="_blank" style="color:#16a34a; font-size:0.75rem; text-decoration:none;"><i class="fa-brands fa-whatsapp"></i> Chat</a>
            </div>
          </td>
          <td style="padding:8px; font-size:0.8rem; max-width:180px;">
            <div style="color:#15803d;">📍 ${b.pickup_location}</div>
            <div style="color:#b91c1c;">🏁 ${b.drop_location}</div>
          </td>
          <td style="padding:8px; font-size:0.78rem;">
            ${b.onboard_date}<br>${b.onboard_time}
          </td>
          <td style="padding:8px; font-weight:700; color:#15803d;">
            ₹${b.fare_amount.toLocaleString('en-IN')}
          </td>
          <td style="padding:8px;">${statusBadge}</td>
          <td style="padding:8px; text-align:right;">
            ${b.booking_status !== 'Cancelled' && b.booking_status !== 'Completed' ? `
              <select onchange="pageUpdateBookingStatus('${b.booking_ref}', this.value)" style="padding:3px 6px; border-radius:6px; border:1px solid #cbd5e1; font-size:0.75rem;">
                <option value="">Update</option>
                <option value="Driver Assigned">Assign Driver</option>
                <option value="Arrived at Pickup">Arrived</option>
                <option value="Trip Started">Start Trip</option>
                <option value="Completed">Completed</option>
                <option value="Cancelled">Cancel</option>
              </select>
            ` : `<span style="font-size:0.75rem; color:#9ca3af;">Done</span>`}
          </td>
        </tr>
      `;
    }).join('');

    document.getElementById("pageStatBookings").innerText = data.bookings.length;
    document.getElementById("pageStatDistance").innerText = `${totalDist.toFixed(1)} KM`;
    document.getElementById("pageStatEarnings").innerText = `₹${totalEarnings.toLocaleString('en-IN')}`;
  } catch (e) {
    console.error("Driver data load error:", e);
  }
}

async function pageUpdateBookingStatus(ref, status) {
  if (!status) return;
  try {
    const res = await fetch("/api/driver/update-status", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ booking_ref: ref, status: status })
    });
    const data = await res.json();
    if (data.success) {
      loadPageDriverData();
      loadPageBookings();
    }
  } catch (e) {
    alert("Status update error: " + e.message);
  }
}

async function checkNewNotificationsBackground() {
  try {
    const res = await fetch("/api/driver/notifications");
    const data = await res.json();
    if (data.success && data.notifications && data.notifications.length > 0) {
      const latest = data.notifications[0];
      if (latest.id > pageLastNotificationId) {
        if (pageLastNotificationId !== 0) {
          playAlertChime();
          document.getElementById("driverLiveAlertBadge").style.display = "inline-block";
        }
        pageLastNotificationId = latest.id;
        displayPageAlertBanner(latest);
      }
    }
  } catch (e) {
    console.error("Notification check error:", e);
  }
}

function displayPageAlertBanner(notif) {
  const banner = document.getElementById("pageLatestAlertBanner");
  document.getElementById("pageAlertTitle").innerText = notif.title;
  document.getElementById("pageAlertTimestamp").innerText = `Dispatched: ${notif.sent_at} • Manoj Mane (+91 9975222099, manojmane155@gmail.com)`;
  document.getElementById("pageAlertBodyContent").innerText = notif.message;

  const encoded = encodeURIComponent(notif.message);
  document.getElementById("pageAlertActionButtons").innerHTML = `
    <a href="https://wa.me/919975222099?text=${encoded}" target="_blank" class="btn-primary" style="background:#25d366; text-decoration:none; font-size:0.8rem; padding:6px 12px; width:auto;">
      <i class="fa-brands fa-whatsapp"></i> Open Alert in WhatsApp
    </a>
    <button onclick="dismissPageAlert()" class="btn-secondary" style="font-size:0.8rem; padding:6px 12px;">
      Dismiss
    </button>
  `;
  banner.style.display = "block";
}

function dismissPageAlert() {
  document.getElementById("pageLatestAlertBanner").style.display = "none";
}
