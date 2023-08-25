function getUserFeatureValue(featureKey, successCallback, errorCallback) {
  fetch('/feature/' + featureKey)
  .then(response => {
    if (!response.ok) {
      throw new Error('Request failed with status ' + response.status);
    }
    return response.json();
  })
  .then(successCallback)
  .catch(errorCallback);
}

function updateUserFeatureValue(featureKey, successCallback, errorCallback) {
  fetch('/feature/' + featureKey, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json'
    }
  })
    .then(response => {
      if (!response.ok) {
        throw new Error('Request failed with status ' + response.status);
      }
      return response.json();
    })
    .then(successCallback)
    .catch(errorCallback);
}

function handleFirstTimeFeatureRequest(featureKey, htmlDescription, actionButtonURL, actionButtonText) {
  getUserFeatureValue(featureKey, function(response) {
    if (response.hasOwnProperty('error')) {
      console.error(response.error);
    } else {
      var featureValue = response[featureKey];
      if (featureValue) {
        updateUserFeatureValue(featureKey, false, function(response) {                
          console.log('Feature value updated successfully');
        }, function(error) {
          console.error(error);
        });
        
        showAlert(featureKey, htmlDescription, actionButtonURL, actionButtonText);
      } else {
        console.log('Feature has already been shown');
      }
    }
  }, function(error) {
    console.error(error);
  });
}