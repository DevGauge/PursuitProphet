function showAlert(type, message, action_url, action_text) {
    console.log('showAlert is called');
    const alertContainer = document.getElementById('alert-container'); // Container for alerts

    let alertHTML = `
        <div class="dialogue alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <div class="alert-btn-container">
    `;

    if (action_url) {
        alertHTML += `
                <button class="btn-${type}">
                    <a href="${action_url}">
                        ${action_text}
                    </a>
                </button>
        `;
    }

    alertHTML += `
                <button type="button" class="alert-btn close-btn" data-dismiss="alert" aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
            </div>
        </div>
    `;

    alertContainer.innerHTML = alertHTML;
    console.log('alert container innerHTML: ', alertContainer.innerHTML)
}

const alertContainer = document.getElementById('alert-container');
alertContainer.addEventListener('click', function(event) {
    const closeButton = event.target.closest('.close-btn');
    if (closeButton) {
        const alert = closeButton.closest('.dialogue');
        alert.remove();
    }
});

window.showAlert = showAlert;