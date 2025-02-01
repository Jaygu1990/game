let positions = Array(20).fill(0); // 20 players, all starting at position 0
let countdown = 5; // Game timer (5 seconds)
let timer;
let raceFinished = false;
let username;
let playerId;

const firebaseConfig = {
  apiKey: "YOUR_FIREBASE_API_KEY",
  authDomain: "YOUR_FIREBASE_AUTH_DOMAIN",
  databaseURL: "YOUR_FIREBASE_DB_URL",
  projectId: "YOUR_FIREBASE_PROJECT_ID",
  storageBucket: "YOUR_FIREBASE_STORAGE_BUCKET",
  messagingSenderId: "YOUR_FIREBASE_MESSAGING_SENDER_ID",
  appId: "YOUR_FIREBASE_APP_ID"
};

firebase.initializeApp(firebaseConfig);
const db = firebase.database();

function login() {
  username = document.getElementById("username").value;
  if (username) {
    document.getElementById("login-container").style.display = 'none';
    document.getElementById("game-container").style.display = 'block';
    startGame();
  }
}

function startGame() {
  // Create 20 Pokémon in rows
  const track = document.querySelector('.track');
  for (let i = 0; i < 20; i++) {
    const pokemon = document.createElement('div');
    pokemon.classList.add('pokemon');
    pokemon.id = `pokemon${i + 1}`;
    track.appendChild(pokemon);
  }

  // Create buttons for each player
  const controls = document.getElementById('controls');
  for (let i = 0; i < 20; i++) {
    const btn = document.createElement('button');
    btn.classList.add('move-btn');
    btn.textContent = `Move Pokemon ${i + 1}`;
    btn.onclick = () => movePokemon(i);
    controls.appendChild(btn);
  }

  startTimer();
}

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

  // Update Firebase to synchronize the player's move
  db.ref('positions').child(player).set(positions[player]);
}

function declareWinner() {
  let winnerIndex = positions.indexOf(Math.max(...positions));
  document.getElementById("winner-text").textContent = `The winner is Pokemon ${winnerIndex + 1}!`;
  raceFinished = true;
}

// Firebase synchronization (to keep players' positions in sync)
db.ref('positions').on('value', snapshot => {
  const data = snapshot.val();
  for (let i = 0; i < 20; i++) {
    if (data && data[i] !== undefined) {
      positions[i] = data[i];
      document.getElementById(`pokemon${i + 1}`).style.left = `${positions[i] * 5}px`;
    }
  }
});


