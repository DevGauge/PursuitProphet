function showAlert(type, message, action_url, action_text) {
    console.log('showAlert is called');
    const alertContainer = document.getElementById('alert-container'); // Container for alerts

    let alertHTML = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <div class="alert-btn-container">
    `;

    if (action_url) {
        alertHTML += `
                <a href="${action_url}" class="alert-btn btn-${type}">
                    ${action_text}
                </a>
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

    const closeButton = alertContainer.querySelector('.close-btn');
    closeButton.addEventListener('click', function() {
        // Remove alert from DOM
        alertContainer.removeChild(alertContainer.firstChild);
    });
}
window.showAlert = showAlert;