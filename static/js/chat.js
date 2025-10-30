const socket=io();
let current_reciever=null
let current_id=null
socket.on('connect',function(){
  console.log('Connected to server')
  
});
socket.emit('join',{});
function chat(username,id) {
  current_reciever=username;
  current_id=id;
  // Hide welcome screen
  document.getElementById("welcomeScreen").classList.add("d-none");


  // Show chat screen
  const chatScreen = document.getElementById("chatScreen");
  chatScreen.classList.remove("d-none");

  // Set chat header name
  document.getElementById("chatWith").innerText = username;

  // Default messages
  const chatBox = document.getElementById("chatMessage");
  chatBox.innerHTML = '';
  //TODO:to be implemented old messages between this users

  

}
socket.on('message',(data)=>{
  console.log(data)
})
document.getElementById('messageForm').addEventListener('submit',function(e){
  e.preventDefault();
  const typemessage= document.getElementById('typeMessage');
  console.log(typemessage)
  const message=typemessage.value.trim();
  if (message&&current_id){
    socket.send({
      reciever:current_id,message:message
    });
  }


});