const BP_PRIZE_COLORS = {
  "10 CONVIDADOS ADICIONAIS": "#ff7a18",
  "15 CRIANÇAS DE 6 A 10 ANOS": "#ff5e94",
  "30 CRIANÇAS DE 0 A 8 ANOS": "#18a0fb",
  "DESCONTO DE R$350,00": "#16a34a",
  "TENTE NOVAMENTE": "#9a7d8f"
};

let bpFinished = false;
let bpPlayStarted = false;
let bpConfettiRunning = false;

const bpQs = (s) => document.querySelector(s);
const bpQsa = (s) => Array.from(document.querySelectorAll(s));

function bpResizeConfettiCanvas() {
  const canvas = bpQs("#bp-confetti");
  if (!canvas) return;
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
}

function bpShowToast(message) {
  const toast = bpQs("#bp-toast");
  if (!toast) return;
  toast.textContent = message;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 2200);
}

function bpShowConfetti() {
  const canvas = bpQs("#bp-confetti");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  bpResizeConfettiCanvas();

  const colors = ["#ff8a3d", "#ffd95b", "#ff6ea5", "#87e2ff", "#9d86ff", "#6de0a5", "#ffffff"];
  const pieces = Array.from({ length: 260 }, () => ({
    x: Math.random() * canvas.width,
    y: Math.random() * -canvas.height,
    r: 3 + Math.random() * 6,
    vy: 2 + Math.random() * 4,
    vx: -2 + Math.random() * 4,
    rot: Math.random() * Math.PI,
    vr: -0.2 + Math.random() * 0.4,
    color: colors[Math.floor(Math.random() * colors.length)]
  }));

  bpConfettiRunning = true;
  let frame = 0;

  (function tick() {
    if (!bpConfettiRunning) return;

    frame++;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    pieces.forEach((p) => {
      p.x += p.vx;
      p.y += p.vy;
      p.rot += p.vr;

      if (p.y > canvas.height + 20) {
        p.y = -20;
        p.x = Math.random() * canvas.width;
      }

      ctx.save();
      ctx.translate(p.x, p.y);
      ctx.rotate(p.rot);
      ctx.fillStyle = p.color;
      ctx.fillRect(-p.r, -p.r, p.r * 2, p.r * 2);
      ctx.restore();
    });

    if (frame < 280) {
      requestAnimationFrame(tick);
    } else {
      bpConfettiRunning = false;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
  })();
}

function bpOpenResult(isWin, prize, whatsappText, whatsappNumber, remaining) {
  const modal = bpQs("#bp-result-modal");
  const icon = bpQs("#bp-result-icon");
  const title = bpQs("#bp-result-title");
  const message = bpQs("#bp-result-message");
  const waBtn = bpQs("#bp-wa-btn");
  const remainingEl = bpQs("#bp-remaining");

  if (remainingEl) remainingEl.textContent = remaining;

  if (!modal || !icon || !title || !message || !waBtn) return;

  if (isWin) {
    bpShowConfetti();
    icon.textContent = "🎉";
    title.textContent = "Parabéns!";
    message.innerHTML = `VOCÊ GANHOU <strong style="color:${BP_PRIZE_COLORS[prize] || "#ff7a18"}">${prize}</strong>.`;
    waBtn.style.display = "inline-flex";
    waBtn.href = `https://wa.me/${whatsappNumber}?text=${encodeURIComponent(whatsappText)}`;
  } else {
    icon.textContent = "🐣";
    title.textContent = "Que pena!";
    message.innerHTML = `DESSA VEZ APARECEU <strong style="color:${BP_PRIZE_COLORS["TENTE NOVAMENTE"]}">TENTE NOVAMENTE</strong>.`;
    waBtn.style.display = "none";
  }

  modal.classList.remove("is-hidden");
  modal.setAttribute("aria-hidden", "false");
}

function bpCloseResult() {
  const modal = bpQs("#bp-result-modal");
  if (!modal) return;
  modal.classList.add("is-hidden");
  modal.setAttribute("aria-hidden", "true");
}

function bpBuildEggCover(canvas, theme) {
  const ctx = canvas.getContext("2d", { willReadFrequently: true });
  const rect = canvas.getBoundingClientRect();
  const ratio = Math.max(window.devicePixelRatio || 1, 1);

  canvas.width = Math.floor(rect.width * ratio);
  canvas.height = Math.floor(rect.height * ratio);
  ctx.scale(ratio, ratio);

  const w = rect.width;
  const h = rect.height;

  const gradients = {
    gold: ["#fff0b5", "#ffd95c", "#ffca2d"],
    rose: ["#ffd8ea", "#ff91bc", "#ff6ca3"],
    sky: ["#daf7ff", "#9ce6ff", "#74d5ff"],
    lavender: ["#eee0ff", "#c6abff", "#a686ff"],
    mint: ["#dcffe8", "#a5f0c3", "#6cdb9e"],
    sunset: ["#ffe6c9", "#ffc27e", "#ff9a57"]
  };

  const c = gradients[theme] || gradients.gold;
  const grad = ctx.createLinearGradient(0, 0, 0, h);
  grad.addColorStop(0, c[0]);
  grad.addColorStop(0.5, c[1]);
  grad.addColorStop(1, c[2]);

  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, w, h);

  ctx.globalAlpha = 0.14;
  ctx.fillStyle = "#ffffff";
  for (let i = 0; i < 10; i++) {
    ctx.fillRect((i * 18) % w, 0, 9, h);
  }
  ctx.globalAlpha = 1;

  ctx.fillStyle = "rgba(255,255,255,.30)";
  ctx.beginPath();
  ctx.ellipse(w * 0.30, h * 0.22, w * 0.18, h * 0.12, -0.45, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = "rgba(255,255,255,.74)";
  const barWidth = w * 0.45;
  const barHeight = 12;
  const barX = (w - barWidth) / 2;
  const barY = h * 0.50;
  const radius = barHeight / 2;

  ctx.beginPath();
  ctx.moveTo(barX + radius, barY);
  ctx.lineTo(barX + barWidth - radius, barY);
  ctx.quadraticCurveTo(barX + barWidth, barY, barX + barWidth, barY + radius);
  ctx.lineTo(barX + barWidth, barY + barHeight - radius);
  ctx.quadraticCurveTo(barX + barWidth, barY + barHeight, barX + barWidth - radius, barY + barHeight);
  ctx.lineTo(barX + radius, barY + barHeight);
  ctx.quadraticCurveTo(barX, barY + barHeight, barX, barY + barHeight - radius);
  ctx.lineTo(barX, barY + radius);
  ctx.quadraticCurveTo(barX, barY, barX + radius, barY);
  ctx.fill();
}

function bpTransparentPercent(canvas) {
  const ctx = canvas.getContext("2d", { willReadFrequently: true });
  const data = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
  let transparent = 0;

  for (let i = 3; i < data.length; i += 4) {
    if (data[i] < 30) transparent++;
  }

  return transparent / (data.length / 4);
}

function bpRevealEgg(card) {
  if (card.classList.contains("revealed")) return;
  card.classList.add("revealed");

  const canvas = card.querySelector(".bp-egg-canvas");
  if (canvas) canvas.style.display = "none";

  bpCheckGameState();
}

function bpAttachScratch(canvas) {
  const card = canvas.closest(".bp-egg-card");
  if (!card) return;

  const theme = card.dataset.theme;
  bpBuildEggCover(canvas, theme);

  let down = false;

  const scratch = (clientX, clientY) => {
    const rect = canvas.getBoundingClientRect();
    const ratio = canvas.width / rect.width;
    const x = (clientX - rect.left) * ratio;
    const y = (clientY - rect.top) * ratio;

    const ctx = canvas.getContext("2d", { willReadFrequently: true });
    ctx.globalCompositeOperation = "destination-out";
    ctx.beginPath();
    ctx.arc(x / ratio, y / ratio, 18, 0, Math.PI * 2);
    ctx.fill();
    ctx.globalCompositeOperation = "source-over";

    if (bpTransparentPercent(canvas) >= 0.40) {
      bpRevealEgg(card);
    }
  };

  canvas.addEventListener("pointerdown", (e) => {
    if (bpFinished) return;
    down = true;
    scratch(e.clientX, e.clientY);
  });

  canvas.addEventListener("pointermove", (e) => {
    if (!down || bpFinished) return;
    scratch(e.clientX, e.clientY);
  });

  window.addEventListener("pointerup", () => {
    down = false;
  });
}

function bpCheckGameState() {
  if (bpFinished) return;

  const counts = {};
  bpQsa(".bp-egg-card.revealed").forEach((card) => {
    const value = card.dataset.value;
    counts[value] = (counts[value] || 0) + 1;
  });

  const winningPrize = Object.keys(counts).find(
    (key) => key !== "TENTE NOVAMENTE" && counts[key] >= 3
  );

  if (winningPrize) {
    bpFinished = true;
    fetch("/finish_play", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ outcome: "WIN", prize: winningPrize })
    })
      .then((r) => r.json())
      .then((data) => bpOpenResult(true, winningPrize, data.whatsapp_text, data.whatsapp_number, data.remaining));
    return;
  }

  const revealedCount = bpQsa(".bp-egg-card.revealed").length;
  if (revealedCount === 6) {
    bpFinished = true;
    fetch("/finish_play", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ outcome: "LOSE", prize: "TENTE NOVAMENTE" })
    })
      .then((r) => r.json())
      .then((data) => bpOpenResult(false, "TENTE NOVAMENTE", data.whatsapp_text, data.whatsapp_number, data.remaining));
  }
}

function bpRenderBoard(board) {
  const boardEl = bpQs("#bp-board");
  if (!boardEl) return;

  boardEl.innerHTML = "";

  board.forEach((item) => {
    const prizeClass = item.value.length > 20 ? "small-text" : "";
    const loseClass = item.value === "TENTE NOVAMENTE" ? "lose" : "";

    const card = document.createElement("article");
    card.className = `bp-egg-card theme-${item.theme}`;
    card.dataset.value = item.value;
    card.dataset.theme = item.theme;

    card.innerHTML = `
      <div class="bp-egg-label">${item.name}</div>
      <div class="bp-egg-wrap">
        <div class="bp-egg-prize ${prizeClass} ${loseClass}" style="color:${BP_PRIZE_COLORS[item.value] || "#5f5675"}">
          ${item.value}
        </div>
        <canvas class="bp-egg-canvas"></canvas>
      </div>
    `;

    boardEl.appendChild(card);
  });

  bpQsa(".bp-egg-canvas").forEach(bpAttachScratch);
}

async function bpStartPlay() {
  if (bpPlayStarted) return;

  try {
    const res = await fetch("/start_play", { method: "POST" });
    const data = await res.json();

    if (!data.ok) {
      bpShowToast("VOCÊ NÃO TEM JOGADAS DISPONÍVEIS.");
      return;
    }

    bpPlayStarted = true;
    bpFinished = false;

    const remainingEl = bpQs("#bp-remaining");
    if (remainingEl) remainingEl.textContent = data.remaining;

    bpRenderBoard(data.board);

    const startBtn = bpQs("#bp-start-btn");
    if (startBtn) startBtn.style.display = "none";
  } catch (error) {
    bpShowToast("ERRO AO INICIAR O JOGO.");
    console.error(error);
  }
}

window.addEventListener("resize", bpResizeConfettiCanvas);

window.addEventListener("DOMContentLoaded", () => {
  bpResizeConfettiCanvas();

  const startBtn = bpQs("#bp-start-btn");
  const closeBtn = bpQs("#bp-close-modal-btn");

  if (startBtn) {
    startBtn.addEventListener("click", bpStartPlay);
  }

  if (closeBtn) {
    closeBtn.addEventListener("click", bpCloseResult);
  }
});
