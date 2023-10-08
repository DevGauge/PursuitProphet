window.onload = function () {
    var goalCards = document.querySelectorAll('.goal-card');
    var isTaskPage = window.location.href.includes('task');
    var isSubTaskPage = window.location.href.includes('subtask');    
    goalCards.forEach(card => {
        // Stop propagation for buttons
        var chatButton = card.querySelector('.chat-button');
        var deleteButton = card.querySelector('.delete-button');
        var completeButton = card.querySelector('.checkbox-container');
        [chatButton, deleteButton, completeButton].forEach(btn => {
            btn.addEventListener('click', e => e.stopPropagation());
        });

        chatButton.addEventListener('click', e => {
            const clickedCard = e.currentTarget.parentElement.parentElement;
            const goalId = clickedCard.getAttribute('data-task-id');            
            sessionStorage.setItem('goalChatId', goalId);
            window.location.href = '/chat';
        });

        deleteButton.addEventListener('click', e => {
            const clickedCard = e.currentTarget.parentElement.parentElement;
            const goalId = clickedCard.getAttribute('data-task-id');
            const goalTitle = clickedCard.querySelector('.goal-text').innerText;            
            if (!isTaskPage && !isSubTaskPage) {
                showAlert('warning', `Are you sure you want to delete the goal "${goalTitle}"? All tasks and subtasks will be deleted!`, `/delete_goal/${goalId}`, 'Delete');
            } else if (isTaskPage && !isSubTaskPage) {
                showAlert('warning', `Are you sure you want to delete the task "${goalTitle}"? All subtasks will be deleted!`, `/delete_task/${goalId}`, 'Delete');
            } else {
                showAlert('warning', `Are you sure you want to delete the subtask "${goalTitle}"?`, `/delete_subtask/${goalId}`, 'Delete');
            }            
        });

        completeButton.addEventListener('click', e => {
            const clickedCard = e.currentTarget.parentElement;            
            const goalId = clickedCard.getAttribute('data-task-id');
            const goalTitle = clickedCard.querySelector('.goal-text').innerText;
            if (!isTaskPage && !isSubTaskPage) { // is goal
                window.location.href = `/goal/complete/${goalId}`;
            } else {
                window.location.href = `/task/complete/${goalId}`;
            }
        });


        // Handle click on rest of card
        card.addEventListener('click', e => {
            const clickedCard = e.currentTarget;
            const goalId = clickedCard.getAttribute('data-task-id');
            if (isTaskPage) {
                window.location.href = `/task/${goalId}`
            } else {
                window.location.href = `/dream/${goalId}`;
            }
        });
    });
}