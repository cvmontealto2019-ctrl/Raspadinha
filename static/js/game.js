document.addEventListener("DOMContentLoaded", function () {
  const startBtn = document.getElementById("start-btn");
  const board = document.getElementById("board");
  const result = document.getElementById("result");
  const resultText = document.getElementById("resultText");
  const whatsapp = document.getElementById("whatsapp");
  const livesEl = document.getElementById("lives");

  let lives = 3;
  let found = {};
  let playing = false;
  let boardData = [];

  const prizes = [
    "10 CONVIDADOS ADICIONAIS",
    "15 CRIANÇAS DE 6 A 10 ANOS",
    "30 CRIANÇAS DE 0 A 8 ANOS",
    "DESCONTO DE R$350,00"
  ];

  function getRound() {
    return parseInt(localStorage.getItem("round") || "1", 10);
  }

  function nextRound() {
    const next = getRound() + 1;
    localStorage.setItem("round", String(next));
  }

  function updateLives() {
    livesEl.textContent = "❤️".repeat(lives);
  }

  function shuffle(array) {
    return array.sort(() => Math.random() - 0.5);
  }

  function generateBoard() {
    const round = getRound();

    // 1ª rodada: perde com ovos podres
    if (round === 1) {
      return shuffle(["💣", "💣", "💣", "💣", "💣", "💣", "TENTE", "TENTE"]);
    }

    // 2ª rodada: tensão
    if (round === 2) {
      return shuffle(["💣", "💣", "TENTE", "TENTE", prizes[0], prizes[1], prizes[2], prizes[3]]);
    }

    // 3ª em diante: ganha
    const prize = prizes[Math.floor(Math.random() * prizes.length)];
    return shuffle([prize, prize, prize, "💣", "💣", "TENTE", prizes[0], prizes[1]]);
  }

  function renderBoard() {
    board.innerHTML = "";

    boardData.forEach((item) => {
      const div = document.createElement("div");
      div.className = "egg";
      div.textContent = "🥚";

      div.addEventListener("click", function () {
        if (!playing || div.classList.contains("revealed")) return;

        div.classList.add("revealed");
        div.textContent = item;

        if (item === "💣") {
          lives -= 1;
          updateLives();

          if (lives <= 0) {
            alert("💣 Esses ovos estavam estragados! Vamos tentar novamente...");
            startInternal(true);
          }
          return;
        }

        if (item === "TENTE") {
          return;
        }

        found[item] = (found[item] || 0) + 1;

        if (found[item] === 3) {
          win(item);
        }
      });

      board.appendChild(div);
    });
  }

  function startInternal(resetOnly) {
    playing = true;
    lives = 3;
    found = {};
    boardData = generateBoard();

    updateLives();
    renderBoard();

    if (!resetOnly) {
      nextRound();
    }
  }

  async function win(prize) {
    playing = false;

    try {
      const res = await fetch("/finish_play", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          outcome: "WIN",
          prize: prize
        })
      });

      const data = await res.json();

      result.classList.remove("hidden");
      resultText.textContent = "🎉 Você ganhou: " + prize;
      whatsapp.href =
        `https://wa.me/${data.whatsapp_number}?text=${encodeURIComponent(data.whatsapp_text)}`;
      whatsapp.textContent = "Ir para WhatsApp";
    } catch (e) {
      alert("Erro ao finalizar o prêmio.");
      console.error(e);
    }
  }

  if (startBtn) {
    startBtn.addEventListener("click", async function () {
      try {
        const res = await fetch("/start_play", { method: "POST" });
        const data = await res.json();

        if (!data.ok) {
          alert("Sem jogadas disponíveis.");
          return;
        }

        startInternal(false);
      } catch (e) {
        alert("Erro ao iniciar o jogo.");
        console.error(e);
      }
    });
  }
});
