function getUserFeatureValue(featureKey, successCallback, errorCallback, userId) {  
  var url = '/feature/' + featureKey;
  if (userId) {
    url += '?user_id=' + userId;
  }
  fetch(url)
  .then(response => {
    if (!response.ok) {
      console.log('error resolving featureKey: ' + featureKey);
      throw new Error('Request failed with status ' + response.status);
    }
    return response.json();
  })
  .then(successCallback)
  .catch(errorCallback);
}

function updateUserFeatureValue(featureKey, successCallback, errorCallback, userId) {
  var url = '/feature/' + featureKey;
  if (userId) {
    url += '?user_id=' + userId;
  }
  console.log("PUT request URL: ", url);
  fetch(url, {
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

function handleFirstTimeFeatureRequest(featureKey, htmlDescription, actionButtonURL, actionButtonText, userId) {
  getUserFeatureValue(featureKey, function(response) {    
    if (response.hasOwnProperty('error')) {
      console.error(response.error);
    } else {
      var featureValue = response[featureKey];
      if (featureValue) {        
        updateUserFeatureValue(featureKey, function(response) {                
          console.log('Feature key value updated successfully');
        }, function(error) {
          console.error(error);
        }, userId);
        
        showAlert(featureKey, htmlDescription, actionButtonURL, actionButtonText);
      } else {
        console.log('Feature has already been shown');
      }
    }
  }, function(error) {
    console.error(error);
  }, userId);
}