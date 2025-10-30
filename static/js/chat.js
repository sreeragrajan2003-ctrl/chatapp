const socket = io();
let current_id = null;
let current_user_id = null;

socket.on('connect', () => {
    console.log('Connected');
    socket.emit('join', {});
});

async function chat(username, id) {
    current_id = id;
    console.log('Chat opened with:', username, 'ID:', id);
    
    document.getElementById("welcomeScreen").classList.add("d-none");
    document.getElementById("chatScreen").classList.remove("d-none");
    document.getElementById("chatWith").innerText = username;
    document.getElementById("chatMessage").innerHTML = '';
    
    // Load old messages
    const res = await fetch(`/get_messages/${id}`);
    const data = await res.json();
    console.log('Loaded messages:', data);
    current_user_id = data.current_user;
    
    data.messages.forEach(m => showMessage(m.sender, m.message, m.timestamp));
}

socket.on('message', (data) => {
    showMessage(data.sender, data.message, data.timestamp);
});

document.getElementById('messageForm').onsubmit = (e) => {
    e.preventDefault();
    const input = document.getElementById('typeMessage');
    const msg = input.value.trim();
    
    if (msg && current_id) {
        socket.send({reciever: current_id, message: msg});
        input.value = '';
    }
};

function showMessage(sender, message, time) {
    const isMe = (sender == current_user_id);
    const div = document.createElement('div');
    div.className = `d-flex ${isMe ? 'justify-content-end' : 'justify-content-start'} mb-3`;
    div.innerHTML = `
        <div class="${isMe ? 'bg-primary text-white' : 'bg-white'} rounded-4 px-3 py-2 shadow-sm" style="max-width: 70%;">
            <p class="mb-1">${message}</p>
            <small class="opacity-75">${time}</small>
        </div>
    `;
    document.getElementById('chatMessage').appendChild(div);
    document.getElementById('chatMessage').scrollTop = 999999;
}