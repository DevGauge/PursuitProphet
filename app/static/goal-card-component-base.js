function setupPropagationStopper(card) {
    var chatButton = card.querySelector('.chat-button');
    var deleteButton = card.querySelector('.delete-button');
    var completeButton = card.querySelector('.checkbox-container');
    [chatButton, deleteButton, completeButton].forEach(btn => {
        btn.addEventListener('click', e => e.stopPropagation());
    });
}

function navigateToChat(card) {
    const goalId = card.getAttribute('data-task-id');            
    sessionStorage.setItem('goalChatId', goalId);
    window.location.href = '/chat';
}

function showAlertDelete(goalTitle, message, url) {
    showAlert('warning', `Are you sure you want to delete ${goalTitle}? <br><br><b>${message}<b>`, url, 'Delete');
}

function completeGoalOrTask(card, url) {
    const goalId = card.getAttribute('data-task-id');
    window.location.href = url + goalId;
}