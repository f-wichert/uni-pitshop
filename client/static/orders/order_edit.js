// only trigger filter if no input for delay ms
function debounceFilter(delay) {
    let timer;
    return () => {
        clearTimeout(timer);
        timer = setTimeout(() => {
            updateListOfOrders();
        }, delay);
    }
}

const onFinishTyping = debounceFilter(300);

function toggleStateFilter(event){
    event.preventDefault();
    event.stopPropagation();
    event.target.classList.toggle("selected");
    updateListOfOrders();
}

function grabFilterValues() {
    return filterValues = {
        "id": document.getElementById("id-field").value,
        "name": document.getElementById("name-field").value,
        "dateFrom": document.getElementById("date-field-1").value,
        "dateUntil": document.getElementById("date-field-2").value,
        "status": [...document.querySelectorAll('.stateFilterDropdownItem')].filter(el => el.classList.contains('selected')).map(el => el.value)
    };
}

function updateListOfOrders() {
    filterValues = grabFilterValues();

    sendRequest("/orders/filtered_orders", filterValues)
    .then((response) => {
        document.getElementById("orders_table_body").innerHTML = response.data;
    })
    .catch((error) => {
        console.log(error);
    })
}

// function handleSortStates(target, sortBy) {
//     target.tagName === 'IMG' ? span = target.parentElement : span = target;  // if the images are clicked and not the span
//     let [sortDesc, sortAsc] = [...span.children];
//     let [sortDescBool, sortAscBool] = [...span.children].map((elem) => !elem.classList.contains('inactiveFilter'));
//     console.log('sortDescBool: ' + sortDescBool)
//     console.log('sortAscBool: ' + sortAscBool)
//     if (sortDescBool) {
//         sortAsc.classList.toggle('inactiveFilter'); // toggle active
//         sortDesc.classList.toggle('inactiveFilter'); // toggle inactive
//         // Laurenz' Sort Stuff
//         if (sortBy === 'name') {
//             currentOrders.sort(function (a, b) {
//                 return a.name.localeCompare(b.name);
//             });
//         }
//         else {
//             currentOrders.sort(function (a, b) {
//                 return a[`${sortBy}`] - b[`${sortBy}`];
//             });
//         }
//         updateOrdersTable(currentOrders);
//         return;
//     }
//     if (sortAscBool) {
//         sortAsc.classList.toggle('inactiveFilter');
//         return;
//     }
//     sortDesc.classList.toggle('inactiveFilter');

//     // Laurenz' Sort Stuff
//     if (sortBy === 'name') {
//         currentOrders.sort(function (a, b) {
//             return b.name.localeCompare(a.name);
//         });
//     }
//     else {
//         currentOrders.sort(function (a, b) {
//             return b[`${sortBy}`] - a[`${sortBy}`];
//         });
//     }
//     updateOrdersTable(currentOrders);
// }

function saveStaffComment(orderId, staffComment){
    sendRequest('/api/save_staff_comment/', {
        'orderId': orderId,
        'staffComment': staffComment,
    })
    .then((response) => {
    })
    .catch((error) => {
        console.log(error);
    })
}

function changeSuborderStatus(orderId, suborderId, type, newState){
    sendRequest('/api/change_suborder/', {
        'order_id': orderId,
        'id': suborderId,
        'type': type,
        'newState': newState,
    })
    .then((response) => {
        // disable/enable states if everything is checked now
        let stateOptions = [...document.querySelectorAll('.onlyIfCompletedState')];
        if (checkIfAllSubordersAreCompleted(orderId)){
            stateOptions.forEach((elem) => elem.disabled = false)
        }
        else {
            stateOptions.forEach((elem) => elem.disabled = true)
        }

        // only run this if box was checked
        if (!newState) return;
        // change order from NEW to IN_PROGRESS if a box is checked
        stateSelect = document.querySelector(`#order_${orderId}_status_selector`);
        currentState = stateSelect.options[stateSelect.selectedIndex].value;
        if (currentState === '0') changeStatusOfOrder(orderId, 1);
    })
    .catch((error) => {
        console.log(error);
    })
}

function updateOrderPrice(orderId, price) {
    document.querySelector(`#order_${orderId}_price`).innerText = price + ' €';
}

function resetPriceOverride(orderId, suborderId, type) {
    sendRequest('/api/change_suborder/', {
        'order_id': orderId,
        'id': suborderId,
        'type': type,
        'reset_price_override': true,
        'get_price': true,
        'get_order_price_str': true,
    })
    .then((response) => {
        updatePriceFunctionObject[type](orderId, suborderId, convertIntToPrice(response.data.price));
        updateOrderPrice(orderId, response.data.order_price_str);
        document.querySelector(`#order_${orderId}_${type}_suborder_${suborderId}_price_reset_button`).disabled = true;
    })
    .catch((error) => {
        console.log(error);
    })
}

function overrideSuborderPrice(orderId, suborderId, type, price){
    if (price === '') return;
    sendRequest('/api/change_suborder/', {
        'order_id': orderId,
        'id': suborderId,
        'type': type,
        'price': `${Math.round(parseFloat(price) * 100)}`,
        'get_price': true,
        'get_order_price_str': true,
    })
    .then((response) => {
        updatePriceFunctionObject[type](orderId, suborderId, convertIntToPrice(response.data.price));
        updateOrderPrice(orderId, response.data.order_price_str);
        document.querySelector(`#order_${orderId}_${type}_suborder_${suborderId}_price_reset_button`).disabled = false;
    })
    .catch((error) => {
        console.log(error);
    })
}

function convertIntToPrice(price){
    return `${(price * 1.0/100).toFixed(2)}`;
}

function editSuborder(type, orderId, suborderId, edit) {
    let relevantInputs = [...document.querySelectorAll(`#order_${orderId}_${type}_suborder_${suborderId} .editInput`)];
    let editButton = document.querySelector(`#order_${orderId}_${type}_suborder_${suborderId}_edit_button`);
    let saveButton = document.querySelector(`#order_${orderId}_${type}_suborder_${suborderId}_edit_disable_button`);
    let resetButton = document.querySelector(`#order_${orderId}_${type}_suborder_${suborderId}_price_reset_button`);
    if (edit) {
        relevantInputs.forEach(el => el.disabled = false);
        editButton.classList.add('d-none');
        saveButton.classList.remove('d-none');
        resetButton.classList.remove('d-none');
    }
    // disable editing
    else {
        relevantInputs.forEach(el => el.disabled = true);
        editButton.classList.remove('d-none');
        saveButton.classList.add('d-none');
        resetButton.classList.add('d-none');
    }
}

function requestChangeSuborder(orderId, suborderId, type, dict) {
    return sendRequest('/api/change_suborder/', {
        'order_id': orderId,
        'id': suborderId,
        'type': type,
        'get_price': true,
        'get_order_price_str': true,
        ...dict,
    })
}
