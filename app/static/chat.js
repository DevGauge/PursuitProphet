// TODO: UWSGI socket implementation
// var socket = io.connect('http://localhost:5000/chat/{{ task.id }}');

// document.getElementById('send-button').addEventListener('click', function() {
//     var userMessage = document.getElementById('message-input').value;
//     chatArea.innerHTML += "<p class='user_message'>" + userMessage + '</p>';
//     socket.emit('message', userMessage);
// });

// socket.on('message', function(data) {
//     var chatArea = document.getElementById('chat-box');
//     chatArea.innerHTML += "<p class='bot_message'>" + data + '</p>';
// });

function send_message() {
    var userMessage = document.getElementById('message-input').value;
    var chatArea = document.getElementById('chat-box');
    chatArea.innerHTML += "<p class='user_message'>" + userMessage + '</p>';
    var xhr = new XMLHttpRequest();
    subtaskContainer = document.getElementById('subtask-container');
    var taskId = subtaskContainer.getAttribute('data-task-id');
    xhr.open('POST', '/chat_api/' + taskId, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onload = function() {
        if (this.status == 200) {
            // Display the chatbot's response on the page
            var chatbotResponse = JSON.parse(this.responseText).response;  // TODO: Model after response from langchain
            chatArea.innerHTML += "<img src='/static/favicon-32x32.png'></img>" + " <p class='bot_message'>" + chatbotResponse.replace(/\n/g, '<br>') + '</p>';
        }
    };
    xhr.send(JSON.stringify({'message': userMessage}));
}

document.getElementById('send-button').addEventListener('click', send_message);
document.getElementById('message-input').addEventListener('keyup', function(event) {
    if (event.key == 'Enter') {
        send_message();
    }
});