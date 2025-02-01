let positions = Array(20).fill(0); // 20 players, all starting at position 0
let countdown = 5; // Game timer (5 seconds)
let timer;
let raceFinished = false;

function startTimer() {
  timer = setInterval(() => {
    countdown--;
    document.getElementById("countdown").textContent = countdown;

    if (countdown <= 0) {
      clearInterval(timer);
      declareWinner();
    }
  }, 1000);
}

function movePokemon(player) {
  if (raceFinished) return; // Disable clicking after the race is finished
  positions[player]++;
  document.getElementById(`pokemon${player + 1}`).style.left = `${positions[player] * 5}px`; // Move the pokemon by 5px each click
}

function declareWinner() {
  let winnerIndex = positions.indexOf(Math.max(...positions));
  document.getElementById("winner-text").textContent = `The winner is Pokemon ${winnerIndex + 1}!`;
  raceFinished = true;
}

document.getElementById("btn1").onclick = () => movePokemon(0);
document.getElementById("btn2").onclick = () => movePokemon(1);
document.getElementById("btn3").onclick = () => movePokemon(2);
// Add more event listeners for buttons up to 20

startTimer(); // Start the countdown timer
