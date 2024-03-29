window.onload = function () {
    var goalCards = document.querySelectorAll('.goal-card');

    goalCards.forEach(card => {
        setupPropagationStopper(card);

        card.querySelector('.chat-button').addEventListener('click', () => navigateToChat(card));
        
        card.querySelector('.delete-button').addEventListener('click', () => {
            const goalTitle = card.querySelector('.goal-text').innerText;
            showAlertDelete(`"${goalTitle}"`, `It will be deleted permanently.`, `/subtask/delete/${card.getAttribute('data-task-id')}`);
        });

        card.querySelector('.checkbox-container').addEventListener('click', () => completeGoalOrTask(card, `/subtask/complete/`));

        card.addEventListener('click', () => completeGoalOrTask(card, `/subtask/`));
    });
}