let lives = 3;
let boardData = [];
let found = {};
let playing = false;

const prizes = [
  "10 CONVIDADOS ADICIONAIS",
  "15 CRIANÇAS DE 6 A 10 ANOS",
  "30 CRIANÇAS DE 0 A 8 ANOS",
  "DESCONTO DE R$350,00"
];

function getRound(){
  return parseInt(localStorage.getItem("round") || "1");
}

function nextRound(){
  let r = getRound()+1;
  localStorage.setItem("round", r);
}

function generateBoard(){
  let round = getRound();
  let board = [];

  if(round === 1){
    board = ["💣","💣","💣","💣","💣","💣","💣","💣"];
  } else if(round === 2){
    board = ["💣","💣","TENTE","TENTE",prizes[0],prizes[1],prizes[2],prizes[3]];
  } else {
    let prize = prizes[Math.floor(Math.random()*prizes.length)];
    board = [prize,prize,prize,"💣","TENTE","TENTE","💣","💣"];
  }

  return board.sort(()=>Math.random()-0.5);
}

function renderBoard(){
  const boardEl = document.getElementById("board");
  boardEl.innerHTML="";

  boardData.forEach((item,i)=>{
    let div = document.createElement("div");
    div.className="egg";
    div.innerText="🥚";

    div.onclick=()=>{
      if(!playing || div.classList.contains("revealed")) return;

      div.classList.add("revealed");
      div.innerText=item;

      if(item==="💣"){
        lives--;
        updateLives();

        if(lives<=0){
          alert("💣 Os ovos estavam estragados! Tentando novamente...");
          startGame(true);
        }
      }

      else if(item==="TENTE"){
        return;
      }

      else{
        found[item] = (found[item]||0)+1;

        if(found[item]===3){
          win(item);
        }
      }
    };

    boardEl.appendChild(div);
  });
}

function updateLives(){
  document.getElementById("lives").innerText="❤️".repeat(lives);
}

function startGame(reset=false){
  playing = true;
  lives = 3;
  found = {};
  boardData = generateBoard();

  updateLives();
  renderBoard();

  if(!reset) nextRound();
}

function win(prize){
  playing = false;

  fetch("/finish_play",{
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({
      outcome:"WIN",
      prize:prize
    })
  })
  .then(r=>r.json())
  .then(data=>{
    document.getElementById("result").classList.remove("hidden");
    document.getElementById("resultText").innerText="🎉 Você ganhou: "+prize;
    document.getElementById("whatsapp").href=
      `https://wa.me/${data.whatsapp_number}?text=${encodeURIComponent(data.whatsapp_text)}`;
  });
}

document.getElementById("start").onclick = () => {
  fetch("/start_play",{method:"POST"})
  .then(r=>r.json())
  .then(data=>{
    if(!data.ok){
      alert("Sem jogadas disponíveis");
      return;
    }
    startGame();
  });
};
