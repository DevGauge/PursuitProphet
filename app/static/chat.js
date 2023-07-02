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
    var userInput = document.getElementById('user-message-input')
    var userMessage = userInput.value;
    userInput.value = '';
    var chatArea = document.getElementById('chat-box');
    
    var loading = document.querySelector('.loading');
    loading.style.display = 'block';
    
    var userMessageElement = document.createElement('p');
    userMessageElement.className = 'user_message';
    userMessageElement.innerHTML = userMessage;
    chatArea.appendChild(userMessageElement);
    
    var xhr = new XMLHttpRequest();
    subtaskContainer = document.getElementById('subtask-container');
    var taskId = subtaskContainer.getAttribute('data-task-id');
    xhr.open('POST', '/chat_api/' + taskId, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onload = function() {
        if (this.status == 200) {
            loading.style.display = 'none';
            // Display the chatbot's response on the page
            var chatbotResponse = JSON.parse(this.responseText).response;  // TODO: Model after response from langchain
            chatbotResponse = chatbotResponse.replace(/\n/g, '<br>');
            
            var imgElement = document.createElement('img');
            imgElement.src = '/static/favicon-32x32.png';
            
            var botMessageElement = document.createElement('p');
            botMessageElement.className = 'bot_message';
            botMessageElement.innerHTML = chatbotResponse;
            
            chatArea.appendChild(imgElement);
            chatArea.appendChild(botMessageElement);
        }
    };
    xhr.send(JSON.stringify({'message': userMessage}));
}

document.getElementById('send-button').addEventListener('click', send_message);
document.getElementById('user-message-input').addEventListener('keyup', function(event) {
    if (event.key == 'Enter') {
        send_message();
    }
});