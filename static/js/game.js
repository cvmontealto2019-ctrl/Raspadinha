const BP_PRIZE_COLORS = {
  "10 CONVIDADOS ADICIONAIS": "#ff7a18",
  "15 CRIANÇAS DE 6 A 10 ANOS": "#ff5e94",
  "30 CRIANÇAS DE 0 A 8 ANOS": "#18a0fb",
  "DESCONTO DE R$350,00": "#16a34a",
  "TENTE NOVAMENTE": "#9a7d8f",
  "OVO CHOCO": "#6f4c3b"
};

const BP_ROTTEN_MESSAGES = [
  "Eitaaa... esse ovo passou do ponto 🤢",
  "Ops! Você encontrou um belo ovo choco 😂",
  "Xi... esse coelhinho escondeu o ovo errado 🫣",
  "Ih, esse aí tava premiado com mau cheiro 😅",
  "Socorro! Ovo choco na área 💨🐣"
];

let bpFinished = false;
let bpRoundActive = false;
let bpLives = 3;
let bpFound = {};
let bpRottenHits = 0;

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
  setTimeout(() => toast.classList.remove("show"), 2600);
}

function bpRandomRottenMessage() {
  return BP_ROTTEN_MESSAGES[Math.floor(Math.random() * BP_ROTTEN_MESSAGES.length)];
}

function bpStartCountdown() {
  const timerEl = bpQs("#bp-timer");
  const timerBox = bpQs("#bp-timer-box");
  if (!timerEl) return;

  const expiresTs = timerEl.dataset.expiresTs;
  if (!expiresTs) {
    timerEl.textContent = "--";
    return;
  }

  let expiredHandled = false;
  const endMs = Number(expiresTs) * 1000;

  function updateTimer() {
    const diff = endMs - Date.now();

    if (diff <= 0) {
      timerEl.textContent = "Tempo encerrado";

      if (timerBox) {
        timerBox.classList.remove("warning");
        timerBox.classList.add("urgent");
      }

      const startBtn = bpQs("#bp-start-btn");
      if (startBtn) {
        startBtn.disabled = true;
        startBtn.classList.add("bp-btn-disabled");
        startBtn.textContent = "TEMPO ENCERRADO";
      }

      if (!expiredHandled) {
        expiredHandled = true;
        setTimeout(() => {
          window.location.reload();
        }, 1500);
      }
      return;
    }

    const totalSeconds = Math.floor(diff / 1000);
    const days = Math.floor(totalSeconds / 86400);
    const hours = Math.floor((totalSeconds % 86400) / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;

    if (days > 0) {
      timerEl.textContent = `${days}d ${String(hours).padStart(2, "0")}h ${String(minutes).padStart(2, "0")}min`;
    } else {
      timerEl.textContent = `${String(hours).padStart(2, "0")}h ${String(minutes).padStart(2, "0")}min ${String(seconds).padStart(2, "0")}s`;
    }

    if (timerBox) {
      timerBox.classList.remove("warning", "urgent");

      if (totalSeconds <= 1800) {
        timerBox.classList.add("urgent");
      } else if (totalSeconds <= 7200) {
        timerBox.classList.add("warning");
      }
    }
  }

  updateTimer();
  setInterval(updateTimer, 1000);
}

function bpShowConfetti() {
  const canvas = bpQs("#bp-confetti");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  bpResizeConfettiCanvas();

  const colors = ["#ff8a3d", "#ffd95b", "#ff6ea5", "#87e2ff", "#9d86ff", "#6de0a5", "#ffffff"];
  const pieces = Array.from({ length: 280 }, () => ({
    x: Math.random() * canvas.width,
    y: Math.random() * -canvas.height,
    r: 3 + Math.random() * 6,
    vy: 2 + Math.random() * 4,
    vx: -2 + Math.random() * 4,
    rot: Math.random() * Math.PI,
    vr: -0.2 + Math.random() * 0.4,
    color: colors[Math.floor(Math.random() * colors.length)]
  }));

  let running = true;
  let frame = 0;

  (function tick() {
    if (!running) return;

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

    if (frame < 300) {
      requestAnimationFrame(tick);
    } else {
      running = false;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
  })();
}

function bpUpdateLives() {
  const livesEl = bpQs("#bp-lives");
  if (livesEl) {
    livesEl.textContent = "❤️".repeat(bpLives);
  }
}

function bpUpdateCurrentPrize(text) {
  const el = bpQs("#bp-current-prize-text");
  if (el) {
    el.textContent = text && String(text).trim() ? text : "Nenhuma ainda";
  }
}

function bpOpenResult(mode, prize, whatsappText, whatsappNumber, currentPrize) {
  const modal = bpQs("#bp-result-modal");
  const icon = bpQs("#bp-result-icon");
  const title = bpQs("#bp-result-title");
  const message = bpQs("#bp-result-message");
  const waBtn = bpQs("#bp-wa-btn");

  if (!modal || !icon || !title || !message || !waBtn) return;

  if (mode === "win") {
    bpShowConfetti();
    icon.textContent = "🎉";
    title.textContent = "Parabéns!";
    message.innerHTML = `VOCÊ ENCONTROU <strong style="color:${BP_PRIZE_COLORS[prize] || "#ff7a18"}">${prize}</strong>. Essa passa a ser sua cortesia atual na campanha.`;
    waBtn.style.display = "inline-flex";
    waBtn.href = `https://wa.me/${whatsappNumber}?text=${encodeURIComponent(whatsappText || "")}`;
    bpUpdateCurrentPrize(currentPrize);
  } else if (mode === "rotten") {
    icon.textContent = "💥";
    title.textContent = "Ah não!";
    message.innerHTML = `Você encontrou <strong style="color:${BP_PRIZE_COLORS["OVO CHOCO"]}">3 OVOS CHOCOS</strong> e a rodada foi reiniciada. Bora tentar de novo?`;
    waBtn.style.display = "none";
  } else {
    icon.textContent = "🥚";
    title.textContent = "Nova rodada";
    message.innerHTML = `Você abriu todos os ovos e não fechou 3 iguais. Os ovos foram embaralhados novamente.`;
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

function bpClassifyValue(value) {
  if (value === "OVO CHOCO") return "rotten";
  if (value === "TENTE NOVAMENTE") return "try";
  return "prize";
}

function bpApplyMobilePositions(board) {
  const isMobile = window.innerWidth <= 640;
  if (!isMobile) return board;

  const mobilePositions = [
    { x: 12, y: 71 },
    { x: 26, y: 46 },
    { x: 38, y: 78 },
    { x: 48, y: 34 },
    { x: 58, y: 59 },
    { x: 69, y: 28 },
    { x: 82, y: 72 },
    { x: 90, y: 47 }
  ];

  return board.map((item, idx) => ({
    ...item,
    x: mobilePositions[idx].x,
    y: mobilePositions[idx].y
  }));
}

function bpRenderBoard(board) {
  const boardEl = bpQs("#bp-board");
  if (!boardEl) return;

  boardEl.innerHTML = "";
  const adjustedBoard = bpApplyMobilePositions(board);

  adjustedBoard.forEach((item) => {
    const card = document.createElement("button");
    card.type = "button";
    card.className = `bp-egg-card theme-${item.theme} size-${item.size}`;
    card.dataset.value = item.value;
    card.dataset.profile = item.profile || "normal";
    card.style.left = `${item.x}%`;
    card.style.top = `${item.y}%`;

    card.innerHTML = `
      <div class="bp-egg-shell theme-${item.theme}">
        <span class="stripe"></span>
        🥚
      </div>
      <div class="bp-egg-open ${bpClassifyValue(item.value)}" style="color:${BP_PRIZE_COLORS[item.value] || "#3b3153"}">
        ${item.value}
      </div>
    `;

    card.addEventListener("click", () => bpRevealEgg(card));
    boardEl.appendChild(card);
  });
}

function bpAllEggsRevealed() {
  const eggs = bpQsa(".bp-egg-card");
  const revealed = bpQsa(".bp-egg-card.revealed");
  return eggs.length > 0 && eggs.length === revealed.length;
}

function bpFinishLoseAndRestart(reason) {
  bpFinished = true;
  bpRoundActive = false;

  fetch("/finish_round", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      outcome: "LOSE",
      prize: null,
      lives_lost: bpRottenHits,
      found: bpFound
    })
  }).finally(() => {
    if (reason === "rotten") {
      bpOpenResult("rotten");
    } else {
      bpOpenResult("reset");
    }
  });
}

function bpCheckOutcomeAfterReveal() {
  if (bpFinished || !bpRoundActive) return;

  const winningPrize = Object.keys(bpFound).find((key) => bpFound[key] >= 3);

  if (winningPrize) {
    bpFinished = true;
    bpRoundActive = false;

    fetch("/finish_round", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        outcome: "WIN",
        prize: winningPrize,
        lives_lost: bpRottenHits,
        found: bpFound
      })
    })
      .then((r) => r.json())
      .then((data) => {
        bpOpenResult(
          "win",
          winningPrize,
          data.whatsapp_text,
          data.whatsapp_number,
          data.current_prize || winningPrize
        );
      })
      .catch(() => {
        bpShowToast("Erro ao finalizar a rodada.");
      });

    return;
  }

  if (bpRottenHits >= 3) {
    bpFinishLoseAndRestart("rotten");
    return;
  }

  if (bpAllEggsRevealed()) {
    bpFinishLoseAndRestart("reset");
  }
}

function bpRevealEgg(card) {
  if (!bpRoundActive || bpFinished || card.classList.contains("revealed")) return;

  card.classList.add("revealed");
  const value = card.dataset.value;

  if (value === "OVO CHOCO") {
    bpRottenHits += 1;
    bpLives = Math.max(0, 3 - bpRottenHits);
    bpUpdateLives();
    bpShowToast(bpRandomRottenMessage());
  } else if (value === "TENTE NOVAMENTE") {
    bpShowToast("Quase! Esse ovo veio só com suspense ✨");
  } else {
    bpFound[value] = (bpFound[value] || 0) + 1;
  }

  bpCheckOutcomeAfterReveal();
}

async function bpStartRound(showToastOnError = true) {
  bpFinished = false;
  bpRoundActive = false;
  bpLives = 3;
  bpRottenHits = 0;
  bpFound = {};
  bpUpdateLives();

  try {
    const res = await fetch("/start_round", { method: "POST" });
    const data = await res.json();

    if (!data.ok) {
      if (showToastOnError) {
        if (data.error === "expired") {
          bpShowToast("Seu tempo para jogar expirou.");
        } else {
          bpShowToast("Não foi possível iniciar a rodada.");
        }
      }
      return;
    }

    bpRenderBoard(data.board || []);
    bpRoundActive = true;
  } catch (error) {
    console.error(error);
    if (showToastOnError) bpShowToast("Erro ao iniciar a rodada.");
  }
}

window.addEventListener("resize", () => {
  bpResizeConfettiCanvas();
});

window.addEventListener("DOMContentLoaded", () => {
  bpResizeConfettiCanvas();
  bpUpdateLives();
  bpStartCountdown();

  const startBtn = bpQs("#bp-start-btn");
  const playAgainBtn = bpQs("#bp-play-again-btn");

  if (startBtn) {
    startBtn.addEventListener("click", async () => {
      startBtn.style.display = "none";
      await bpStartRound(true);
    });
  }

  if (playAgainBtn) {
    playAgainBtn.addEventListener("click", async () => {
      bpCloseResult();
      await bpStartRound(true);
    });
  }
});
