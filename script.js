const APP_URL = "https://ai-resume-analyser-y5cv.onrender.com"; // replace with your Render app URL

const progressBar = document.getElementById("progressBar");
const progressPercent = document.getElementById("progressPercent");
const elapsedTime = document.getElementById("elapsedTime");
const rotatingText = document.getElementById("rotatingText");
const statusState = document.getElementById("statusState");
const statusDetail = document.getElementById("statusDetail");
const liveStatusLabel = document.getElementById("liveStatusLabel");
const loadingHeadline = document.getElementById("loadingHeadline");
const readyModal = document.getElementById("readyModal");
const openAppBtn = document.getElementById("openAppBtn");
const openAppInline = document.getElementById("openAppInline");
const closeModalBtn = document.getElementById("closeModalBtn");

const loadingMessages = [
  "Initializing container...",
  "Installing dependencies...",
  "Injecting environment variables...",
  "Connecting AI services...",
  "Loading backend workers...",
  "Optimizing runtime...",
  "Doing Something...",
  "Preparing interface...",
  "Initializing ResumeAI...",
  "Connecting to the live server...",
  "Checking app status...",
  "Almost ready..."
];

let rotatingIndex = 0;
let progress = 0;
let ready = false;
let elapsed = 0;
let lastPingAt = 0;
let progressTimer = null;
let messageTimer = null;
let pingTimer = null;

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function setProgress(value) {
  progress = clamp(value, 0, 100);
  progressBar.style.width = `${progress}%`;
  progressPercent.textContent = `${Math.round(progress)}%`;
}

function setStatus(phase, detail, badgeText) {
  statusState.textContent = phase;
  statusDetail.textContent = detail;
  liveStatusLabel.textContent = badgeText;
  loadingHeadline.textContent = phase;
}

function openModal() {
  readyModal.classList.remove("hidden");
  document.body.style.overflow = "hidden";
}

function closeModal() {
  readyModal.classList.add("hidden");
  document.body.style.overflow = "";
}

function completeLoading() {
  if (ready) return;
  ready = true;

  if (progressTimer) clearInterval(progressTimer);
  if (messageTimer) clearInterval(messageTimer);
  if (pingTimer) clearInterval(pingTimer);

  setProgress(100);
  setStatus(
    "ResumeAI is ready",
    "The application woke up successfully and is ready to open.",
    "Ready"
  );

  openAppBtn.disabled = false;
  openAppInline.disabled = false;

  setTimeout(() => {
    openModal();
  }, 350);
}

async function pingApp() {
  if (ready) return;

  lastPingAt = Date.now();
  try {
    await fetch(APP_URL.replace(/\/$/, "") + "/", {
      method: "GET",
      mode: "no-cors",
      cache: "no-store",
      credentials: "omit",
    });

    // If the network request resolves, the app is reachable.
    completeLoading();
  } catch (error) {
    // Still warming up; keep trying.
  }
}

function startProgress() {
  const startAt = Date.now();
  const maxAutoFillMs = 60000;
  const targetMaxBeforeReady = 99;

  progressTimer = setInterval(() => {
    if (ready) return;

    elapsed = Math.floor((Date.now() - startAt) / 1000);
    elapsedTime.textContent = `${elapsed}s`;

    // Steady fill to 95% over 60 seconds, then hover near completion.
    const autoProgress = Math.min((elapsed / 60) * 95, 95);
    const next = Math.max(progress, autoProgress);

    if (elapsed >= 60) {
      setStatus(
        "ResumeAI is still waking up",
        "The server is taking a little longer than expected. Still checking every second.",
        "Warming up"
      );
      setProgress(Math.min(Math.max(next, 96), targetMaxBeforeReady));
    } else {
      setProgress(next);
    }
  }, 1000);
}

function startRotatingMessages() {
  rotatingText.textContent = loadingMessages[0];

  messageTimer = setInterval(() => {
    if (ready) return;
    rotatingIndex = (rotatingIndex + 1) % loadingMessages.length;
    rotatingText.textContent = loadingMessages[rotatingIndex];
  }, 2200);
}

function startPinging() {
  pingApp();
  pingTimer = setInterval(() => {
    pingApp();
  }, 1000);
}

openAppBtn.addEventListener("click", () => {
  window.location.href = APP_URL;
});

openAppInline.addEventListener("click", () => {
  window.location.href = APP_URL;
});

closeModalBtn.addEventListener("click", closeModal);

readyModal.addEventListener("click", (event) => {
  if (event.target === readyModal) {
    closeModal();
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !readyModal.classList.contains("hidden")) {
    closeModal();
  }
});

setStatus(
  "Connecting to ResumeAI...",
  "Checking the live app every second while the page remains fully usable.",
  "Connecting"
);

setProgress(0);
startRotatingMessages();
startProgress();
startPinging();
