console.log("GAME.JS NOVO CARREGADO - TESTE 123");

document.addEventListener("DOMContentLoaded", () => {
  const startBtn = document.getElementById("bp-start-btn");
  const board = document.getElementById("bp-board");
  const timer = document.getElementById("bp-timer");

  console.log("DOM carregado");
  console.log("startBtn:", startBtn);
  console.log("board:", board);
  console.log("timer:", timer);

  if (timer) {
    timer.textContent = "JS carregado";
  }

  if (startBtn) {
    startBtn.addEventListener("click", async () => {
      console.log("BOTÃO CLICADO");

      try {
        const res = await fetch("/start_round", { method: "POST" });
        const data = await res.json();
        console.log("RESPOSTA /start_round:", data);

        if (!data.ok) {
          alert("Não foi possível iniciar: " + (data.error || "erro desconhecido"));
          return;
        }

        if (board) {
          board.innerHTML = "<div style='color:#fff;padding:20px;font-weight:bold;'>JOGO INICIOU ✅</div>";
        }
      } catch (e) {
        console.error("ERRO NO START:", e);
        alert("Erro ao iniciar rodada");
      }
    });
  }
});
