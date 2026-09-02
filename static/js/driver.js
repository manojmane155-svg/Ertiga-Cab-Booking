// ----------------- DRIVER PORTAL JS (MANOJ MANE) ----------------- //
let lastNotificationId = 0;
let isAudioUnlocked = false;

// Audio Chime using Web Audio API (no external file dependency)
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

// Unlock audio on first user gesture
document.addEventListener("click", () => {
  isAudioUnlocked = true;
}, { once: true });

// ----------------- DATA LOADING ----------------- //
async function refreshData() {
  await Promise.all([loadDriverProfile(), loadBookings(), checkNewNotifications()]);
}

async function loadDriverProfile() {
  try {
    const res = await fetch("/api/driver-info");
    const data = await res.json();
    if (data.success) {
      const isOnline = data.driver.is_online;
      document.getElementById("onlineToggle").checked = isOnline;
      const label = document.getElementById("availabilityLabel");
      if (isOnline) {
        label.innerText = "AVAILABLE ONLINE";
        label.style.color = "#34d399";
      } else {
        label.innerText = "OFFLINE (NOT ACCEPTING)";
        label.style.color = "#ef4444";
      }
    }
  } catch (e) {
    console.error("Profile load error:", e);
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
      const label = document.getElementById("availabilityLabel");
      if (isOnline) {
        label.innerText = "AVAILABLE ONLINE";
        label.style.color = "#34d399";
      } else {
        label.innerText = "OFFLINE (NOT ACCEPTING)";
        label.style.color = "#ef4444";
      }
    }
  } catch (e) {
    alert("Error updating availability: " + e.message);
  }
}

async function loadBookings() {
  const tbody = document.getElementById("driverBookingsTbody");
  try {
    const res = await fetch("/api/driver/bookings");
    const data = await res.json();

    if (!data.bookings || data.bookings.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:30px; color:#9ca3af;">No bookings placed yet.</td></tr>`;
      updateStats(0, 0, 0);
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
        b.booking_status === 'Confirmed' ? '<span style="background:#dcfce7; color:#15803d; padding:3px 8px; border-radius:12px; font-weight:700; font-size:0.75rem;">CONFIRMED</span>' :
        b.booking_status === 'Driver Assigned' ? '<span style="background:#fef3c7; color:#b45309; padding:3px 8px; border-radius:12px; font-weight:700; font-size:0.75rem;">ASSIGNED</span>' :
        b.booking_status === 'Arrived at Pickup' ? '<span style="background:#e0e7ff; color:#4338ca; padding:3px 8px; border-radius:12px; font-weight:700; font-size:0.75rem;">ARRIVED</span>' :
        b.booking_status === 'Trip Started' ? '<span style="background:#fae8ff; color:#86198f; padding:3px 8px; border-radius:12px; font-weight:700; font-size:0.75rem;">ON TRIP</span>' :
        b.booking_status === 'Completed' ? '<span style="background:#e0f2fe; color:#0369a1; padding:3px 8px; border-radius:12px; font-weight:700; font-size:0.75rem;">COMPLETED</span>' :
        '<span style="background:#fee2e2; color:#b91c1c; padding:3px 8px; border-radius:12px; font-weight:700; font-size:0.75rem;">CANCELLED</span>';

      const customerCleanMobile = b.user_mobile.replace(/[^0-9]/g, '');

      return `
        <tr style="border-bottom:1px solid #f3f4f6;">
          <td style="padding:12px; font-weight:800; color:#111827;">${b.booking_ref}</td>
          <td style="padding:12px;">
            <div style="font-weight:700; color:#111827;">${b.user_name}</div>
            <div style="display:flex; gap:6px; margin-top:2px;">
              <a href="tel:${b.user_mobile}" style="color:#0284c7; text-decoration:none; font-size:0.75rem; font-weight:600;"><i class="fa-solid fa-phone"></i> +91 ${customerCleanMobile}</a>
              <a href="https://wa.me/91${customerCleanMobile}" target="_blank" style="color:#16a34a; text-decoration:none; font-size:0.75rem; font-weight:600;"><i class="fa-brands fa-whatsapp"></i> Chat</a>
            </div>
          </td>
          <td style="padding:12px; max-width:200px;">
            <div style="font-size:0.8rem; color:#15803d;">📍 ${b.pickup_location}</div>
            <div style="font-size:0.8rem; color:#b91c1c; margin-top:2px;">🏁 ${b.drop_location}</div>
          </td>
          <td style="padding:12px; font-size:0.82rem;">
            <strong>${b.onboard_date}</strong><br>
            <span style="color:#6b7280;">${b.onboard_time}</span>
          </td>
          <td style="padding:12px;">
            <div style="font-weight:700; font-size:0.95rem; color:#15803d;">₹${b.fare_amount.toLocaleString('en-IN')}</div>
            <div style="font-size:0.75rem; color:#6b7280;">${b.distance_km} KM @ ₹${b.rate_per_km}/km</div>
          </td>
          <td style="padding:12px; font-size:0.8rem;">
            <span style="font-weight:600;">${b.payment_method}</span><br>
            <span style="color:${b.payment_status === 'Paid' ? '#16a34a' : '#ea580c'};">${b.payment_status}</span>
          </td>
          <td style="padding:12px;">${statusBadge}</td>
          <td style="padding:12px; text-align:right;">
            ${b.booking_status !== 'Cancelled' && b.booking_status !== 'Completed' ? `
              <select onchange="updateBookingStatus('${b.booking_ref}', this.value)" style="padding:4px 8px; border-radius:6px; border:1px solid #cbd5e1; font-size:0.78rem; outline:none;">
                <option value="">Update Status</option>
                <option value="Driver Assigned">Assign Driver</option>
                <option value="Arrived at Pickup">Arrived at Pickup</option>
                <option value="Trip Started">Start Trip</option>
                <option value="Completed">Mark Completed</option>
                <option value="Cancelled">Cancel Ride</option>
              </select>
            ` : `<span style="font-size:0.75rem; color:#9ca3af;">No Actions</span>`}
          </td>
        </tr>
      `;
    }).join('');

    updateStats(data.bookings.length, totalDist, totalEarnings);
  } catch (e) {
    console.error("Bookings load error:", e);
  }
}

function updateStats(count, dist, earnings) {
  document.getElementById("statTotalBookings").innerText = count;
  document.getElementById("statTotalDistance").innerText = `${dist.toFixed(1)} KM`;
  document.getElementById("statTotalEarnings").innerText = `₹${earnings.toLocaleString('en-IN')}`;
}

async function updateBookingStatus(ref, status) {
  if (!status) return;
  try {
    const res = await fetch("/api/driver/update-status", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ booking_ref: ref, status: status })
    });
    const data = await res.json();
    if (data.success) {
      loadBookings();
    } else {
      alert("Status update failed: " + data.message);
    }
  } catch (e) {
    alert("Error updating status: " + e.message);
  }
}

// ----------------- LIVE NOTIFICATIONS (DRIVER ALERT) ----------------- //
async function checkNewNotifications() {
  try {
    const res = await fetch("/api/driver/notifications");
    const data = await res.json();

    if (data.success && data.notifications && data.notifications.length > 0) {
      const latest = data.notifications[0];
      
      // If a brand new notification arrived
      if (latest.id > lastNotificationId) {
        if (lastNotificationId !== 0) {
          playAlertChime();
        }
        lastNotificationId = latest.id;
        displayAlertBanner(latest);
      }
    }
  } catch (e) {
    console.error("Notification check error:", e);
  }
}

function displayAlertBanner(notif) {
  const banner = document.getElementById("latestAlertBanner");
  document.getElementById("alertTitle").innerText = notif.title;
  document.getElementById("alertTimestamp").innerText = `Dispatched at: ${notif.sent_at} • Recipient: Manoj Mane (+91 9975222099, manojmane155@gmail.com)`;
  document.getElementById("alertBodyContent").innerText = notif.message;

  const encoded = encodeURIComponent(notif.message);
  document.getElementById("alertActionButtons").innerHTML = `
    <a href="https://wa.me/919975222099?text=${encoded}" target="_blank" class="btn-primary" style="background:#25d366; text-decoration:none; font-size:0.85rem; padding:8px 14px; width:auto;">
      <i class="fa-brands fa-whatsapp"></i> Open Alert in WhatsApp
    </a>
    <button onclick="dismissAlert()" class="btn-secondary" style="font-size:0.85rem; padding:8px 14px;">
      Dismiss
    </button>
  `;

  banner.style.display = "block";
}

function dismissAlert() {
  document.getElementById("latestAlertBanner").style.display = "none";
}

// ----------------- AUTO REFRESH LOOP ----------------- //
window.addEventListener("DOMContentLoaded", () => {
  refreshData();
  // Poll every 5 seconds for new bookings/notifications
  setInterval(refreshData, 5000);
});
