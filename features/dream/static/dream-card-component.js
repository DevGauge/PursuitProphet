window.onload = function () {
    var goalCards = document.querySelectorAll('.goal-card');

    goalCards.forEach(card => {
        setupPropagationStopper(card);

        card.querySelector('.chat-button').addEventListener('click', () => navigateToChat(card));
        
        card.querySelector('.delete-button').addEventListener('click', () => {
            const goalTitle = card.querySelector('.goal-text').innerText;
            showAlertDelete(`"${goalTitle}"`, `This is permanent. All tasks and subtasks will be deleted!`, `/dream/delete/${card.getAttribute('data-task-id')}`);
        });

        card.querySelector('.checkbox-container').addEventListener('click', () => completeGoalOrTask(card, `/dream/complete/`));

        card.addEventListener('click', () => completeGoalOrTask(card, `/dream/`));
    });
}
