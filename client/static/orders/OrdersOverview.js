// FUNCTIONS

function changeStatusOfOrder(orderId, newState) {
    suborderCheckboxes = [...document.querySelectorAll(`.order_${orderId}_suborder_checkbox`)];
    suborderEditButtons = [...document.querySelectorAll(`.order_${orderId}_suborder_edit_button`)];
    // disable checkboxes if newState in finishedStates
    if (finishedStates.includes(newState)){
        suborderCheckboxes.forEach((elem) => elem.disabled = true);
        suborderEditButtons.forEach((elem) => elem.disabled = true);
        // cancel ongoing edits
        let suborderIdTypeArray = [...document.querySelectorAll(`.order_${orderId}_suborder_row`)].map((so) => {
            let splitId = so.id.split('_');
            return {
                'type': splitId[2],
                'suborderId': splitId[4],
            }
        });
        suborderIdTypeArray.forEach((so) => editSuborder(so.type, orderId, so.suborderId, false));
    }
    else {
        suborderCheckboxes.forEach((elem) => elem.disabled = false);
        suborderEditButtons.forEach((elem) => elem.disabled = false);
    }

    sendRequest('/api/change_state_of_order/',{
        'orderId': orderId,
        'newState': newState,
    })
    .then((response) => {
        // Update State Button Color
        updateStateSelect(orderId, newState);
        updateStateButton(orderId, newState);
    })
    .catch((error) => {
        console.log(error);
    })
}

function updateStateSelect(orderId, newState){
    stateSelect = document.querySelector(`#order_${orderId}_status_selector`);
    stateSelect.selectedIndex = newState;
}

function updateStateButton(orderId, newState){
    stateButton = document.querySelector(`#order_${orderId}_status_button`);
    stateButton.classList.remove(...stateColorsArray);
    stateButton.classList.add(stateColors[newState]);
}

function checkIfAllSubordersAreCompleted(orderId){
    suborderCheckboxes = [...document.querySelectorAll(`.order_${orderId}_suborder_checkbox`)];
    return suborderCheckboxes.filter(el => !el.checked).length === 0;
}

function selectNewOrderStatus(orderId, newState) {
    changeStatusOfOrder(orderId, newState);
}

function cycleStates(orderId) {
    stateSelect = document.querySelector(`#order_${orderId}_status_selector`);
    currentState = stateSelect.options[stateSelect.selectedIndex].value;
    if (currentState === '4') return;
    // can't go to FINISHED if state is READY_FOR_PICKUP and some suborders aren't finished
    if (currentState === '2' &&  !checkIfAllSubordersAreCompleted(orderId)) {
        alert('Alle Teile des Aufrags müssen abgeschlossen sein, bevor die Bestellung abgeschlossen werden kann.')
        return;
    };
    let newState = `${parseInt(currentState) + 1}`;
    changeStatusOfOrder(orderId, newState);
}