const socket = io();
let current_reciever = null;
let current_id = null;

socket.on('connect', function() {
    console.log('Connected to server');
    socket.emit('join', {});
});

function chat(username, id) {
    current_reciever = username;
    current_id = id;
    
    console.log('Opening chat with:', username, 'ID:', id);
    
    // Hide welcome screen
    document.getElementById("welcomeScreen").classList.add("d-none");

    // Show chat screen
    const chatScreen = document.getElementById("chatScreen");
    chatScreen.classList.remove("d-none");

    // Set chat header name
    document.getElementById("chatWith").innerText = username;

    // Clear chat box
    const chatBox = document.getElementById("chatMessage");
    chatBox.innerHTML = '';
    
    //TODO: Load old messages between these users
}

socket.on('message', (data) => {
    console.log('Message received:', data);
    appendMessage(data.sender, data.message, data.timestamp);
});

document.getElementById('messageForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const typemessage = document.getElementById('typeMessage');
    const message = typemessage.value.trim();
    
    console.log('Sending message:', message, 'to:', current_id);
    
    if (message && current_id) {
        socket.send({
            reciever: current_id,
            message: message
        });
        
        typemessage.value = '';
    }
});

