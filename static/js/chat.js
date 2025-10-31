const socket = io();
let current_id = null;
let current_user_id = null;

socket.on('connect', () => {
    console.log('Connected');
    socket.emit('join', {});
});

// Listen for user status updates
socket.on('user_status', (data) => {
    updateUserStatus(data.user_id, data.is_online);
});

// Listen for unread message updates
socket.on('unread_update', async (data) => {
    console.log('Unread update received:', data);
    // Update unread count for the sender
    await updateUnreadBadge(data.sender_id);
});

async function chat(username, id, isOnline) {
    current_id = id;
    console.log('Chat opened with:', username, 'ID:', id, 'Online:', isOnline);
    
    document.getElementById("welcomeScreen").classList.add("d-none");
    document.getElementById("chatScreen").classList.remove("d-none");
    document.getElementById("chatWith").innerText = username;
    document.getElementById("chatMessage").innerHTML = '';
    
    // Display status in chat header
    const chatStatusElement = document.getElementById('chatStatus');
    if (isOnline) {
        chatStatusElement.innerHTML = '<i class="fa-solid fa-circle" style="font-size: 8px;"></i> Online';
        chatStatusElement.className = 'opacity-75 text-success';
    } else {
        chatStatusElement.innerHTML = '<i class="fa-solid fa-circle" style="font-size: 8px;"></i> Offline';
        chatStatusElement.className = 'opacity-75 text-secondary';
    }
    
    // Load old messages
    const res = await fetch(`/get_messages/${id}`);
    const data = await res.json();
    console.log('Loaded messages:', data);
    current_user_id = data.current_user;
    
    data.messages.forEach(m => showMessage(m.sender, m.message, m.timestamp));
    
    // Clear unread badge for this user
    clearUnreadBadge(id);
    
    // Notify server that messages are read
    socket.emit('mark_read', { sender_id: id });
}

function updateUserStatus(userId, isOnline) {
    // Update status in user list
    const statusElement = document.getElementById(`status-${userId}`);
    if (statusElement) {
        if (isOnline) {
            statusElement.innerHTML = '<span class="text-success"><i class="fa-solid fa-circle" style="font-size: 8px;"></i> Online</span>';
        } else {
            statusElement.innerHTML = '<span class="text-secondary"><i class="fa-solid fa-circle" style="font-size: 8px;"></i> Offline</span>';
        }
    }
    
    // Update status in chat header if this is the current chat
    if (current_id == userId) {
        const chatStatusElement = document.getElementById('chatStatus');
        if (chatStatusElement) {
            if (isOnline) {
                chatStatusElement.innerHTML = '<i class="fa-solid fa-circle" style="font-size: 8px;"></i> Online';
                chatStatusElement.className = 'opacity-75 text-success';
            } else {
                chatStatusElement.innerHTML = '<i class="fa-solid fa-circle" style="font-size: 8px;"></i> Offline';
                chatStatusElement.className = 'opacity-75 text-secondary';
            }
        }
    }
}

async function updateUnreadBadge(senderId) {
    // Don't update if currently chatting with this user
    if (current_id == senderId) {
        return;
    }
    
    try {
        const res = await fetch(`/get_unread_count/${senderId}`);
        const data = await res.json();
        const badge = document.getElementById(`unread-badge-${senderId}`);
        
        if (badge) {
            if (data.unread_count > 0) {
                badge.textContent = data.unread_count;
                badge.classList.remove('d-none');
            } else {
                badge.classList.add('d-none');
            }
        }
    } catch (error) {
        console.error('Error updating unread badge:', error);
    }
}

function clearUnreadBadge(userId) {
    const badge = document.getElementById(`unread-badge-${userId}`);
    if (badge) {
        badge.classList.add('d-none');
        badge.textContent = '0';
    }
}

socket.on('message', (data) => {
    showMessage(data.sender, data.message, data.timestamp);
    
    // If message is from someone else and not in current chat, update badge
    if (data.sender != current_user_id && data.sender != current_id) {
        updateUnreadBadge(data.sender);
    }
    
    // If message is from current chat partner, mark as read
    if (data.sender == current_id) {
        socket.emit('mark_read', { sender_id: current_id });
    }
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
        <div class="${isMe ? 'bg-primary text-white' : 'bg-white'} rounded-4 px-3 py-2 shadow-sm fade-in" style="max-width: 70%;">
            <p class="mb-1">${message}</p>
            <small class="opacity-75">${time}</small>
        </div>
    `;
    document.getElementById('chatMessage').appendChild(div);
    document.getElementById('chatMessage').scrollTop = 999999;
}