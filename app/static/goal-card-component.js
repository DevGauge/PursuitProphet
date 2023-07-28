window.onload = function () {
    var goalCards = document.querySelectorAll('.goal-card');
    goalCards.forEach(card => {
        // Stop propagation for buttons
        var chatButton = card.querySelector('.chat-button');
        var deleteButton = card.querySelector('.delete-button');
        [chatButton, deleteButton].forEach(btn => {
            btn.addEventListener('click', e => e.stopPropagation());
        });

        chatButton.addEventListener('click', e => {
            const clickedCard = e.currentTarget.parentElement.parentElement;
            const goalId = clickedCard.getAttribute('data-task-id');            
            sessionStorage.setItem('goalChatId', goalId);
            window.location.href = '/chat';
        });

        deleteButton.addEventListener('click', e => {
            // pop up this jinja alert {% include '_alert.html' with type='warning' message='This is a warning message.' action_url='/action' action_text='Do something' %}
            const clickedCard = e.currentTarget.parentElement.parentElement;
            const goalId = clickedCard.getAttribute('data-task-id');
            const goalTitle = clickedCard.querySelector('.goal-text').innerText;
            console.log(goalTitle);

            showAlert('warning', `Are you sure you want to delete the goal "${goalTitle}"?`, `/delete_goal/${goalId}`, 'Delete');
        });

        // Handle click on rest of card
        card.addEventListener('click', e => {
            const clickedCard = e.currentTarget;
            const goalId = clickedCard.getAttribute('data-task-id');
            window.location.href = `/goal/${goalId}`;
        });
    });
}