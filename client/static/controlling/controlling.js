// FUNCTIONS
function filter (){
    axios.get('filter', {
        params: grabFilterValues(),
    })
    .then((response) => {
        document.querySelector('#entryBody').innerHTML = response.data
    })
    .catch((error) => {
        console.log(error)
    });
}

function grabFilterValues() {
    const filterElements = [...document.querySelectorAll('#entryHeader .relevantFilter')];
    const filterObject = {};
    for (let filter of filterElements) {
        filterObject[filter.id] = filter.value;
    }
    filterObject.sort = grabSortValues(); // addSortString
    return filterObject;
}

function grabSortValues() {
    const sortSpans = [...document.querySelectorAll('#entryHeader .sort-span')];
    let sortString = '';
    for (let span of sortSpans){
        let [sortDesc, sortAsc] = [...span.children].map((elem) => !elem.classList.contains('inactiveFilter'));
        sortString += ((sortDesc ? '-' : '') + (sortAsc || sortDesc ? span.id.split('-')[1] : '') + ';');
    }
    return sortString.slice(0, -1); // remove last ; for easier splitting in backend
}

function handleSortStates(target) {
    target.tagName === 'IMG' ? span = target.parentElement : span = target;  // if the images are clicked and not the span
    let [sortDesc, sortAsc] = [...span.children];
    let [sortDescBool, sortAscBool] = [...span.children].map((elem) => !elem.classList.contains('inactiveFilter'));
    console.log('sortDescBool: ' + sortDescBool)
    console.log('sortAscBool: ' + sortAscBool)
    if (sortDescBool) {
        sortAsc.classList.toggle('inactiveFilter'); // toggle active
        sortDesc.classList.toggle('inactiveFilter'); // toggle inactive
        filter();
        return;
    }
    if (sortAscBool) {
        sortAsc.classList.toggle('inactiveFilter');
        filter();
        return;
    }
    sortDesc.classList.toggle('inactiveFilter');
    filter();
}

function checkAllNonBilledEntries(checked) {
    for (let row of document.querySelector('#entryBody').children){
        let rowBilled = row.children[5];
        let rowCheckBox = row.children[0].children[0];
        if (rowBilled.innerText === 'Noch nicht abgerechnet' && rowCheckBox.checked !== checked) rowCheckBox.click();
    }
}

function billCurrentSelection(btn) {
    btn.disabled = true;
    btnOldText = btn.innerText;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Abrechnen...';
    // collect orderIds of selected rows
    let orderIdsToBill = '';
    for (let row of document.querySelector('#entryBody').children){
        let rowCheckBox = row.children[0].children[0];
        let rowOrderId = row.children[1].innerText;
        if (rowCheckBox.checked) orderIdsToBill += `${rowOrderId};`
    }
    sendRequest('/api/controlling/create_new_billing', {'orderIdsToBill': orderIdsToBill,})
    .then((response) => {
        btn.disabled = false;
        btn.innerText = btnOldText;
        // call filter because event propagation is off
        filter();
    })
    .catch((error) => {
        console.log(error);
    });
}

function getAlreadyBilledModal() {
    axios.get('billing_modal')
    .then((response) => {
        document.querySelector('#modalTableBody').innerHTML = response.data;
    })
    .catch((error) => {
        console.log(error)
    });
}

function deleteBilling(button) {
    // get id from button and disable button
    id = button.parentElement.id.split('_')[1]
    button.disabled = true;
    if (button.classList.contains('clickedOnce')){
        sendRequest('/api/controlling/delete_billing', {'billingIdToDelete': id,})
        .then((response) => {
            button.disabled = false; // Restore Button State
            getAlreadyBilledModal(); // update billing table and order table
            filter();
        })
        .catch((error) => {
            console.log(error);
        });
    }
    else {
        setTimeout(() => { // setTimeout to disable fast double clicking to delete
            button.classList.add('clickedOnce');
            button.classList.replace('btn-warning', 'btn-danger');
            button.innerHTML = document.querySelector('#imgConfirmDelete').innerHTML;
            button.disabled = false;
        }, 200);
    }
}

function autoBilling() {
    maxAmount = parseFloat(document.querySelector('#maxAmountInputAutoBilling').value.replace(',', '.'));
    dateToBillFrom = document.querySelector('#dateInputAutoBilling').value;
    if (!maxAmount || !dateToBillFrom) return; 
    axios.get('auto_billing', {
        params: {
            'maxAmount': maxAmount,
            'dateToBillFrom': dateToBillFrom,
        },
    })
    .then((response) => {
        if (response.data === "no_orders_found") {
            document.querySelector('#automaticBillingModalTableRow').classList.add('d-none');
            document.querySelector('#automaticBillingModalSumRow').classList.add('d-none');
            document.querySelector('#noOrdersFoundError').classList.remove('d-none');
        }
        else {
            document.querySelector('#noOrdersFoundError').classList.add('d-none');
            document.querySelector('#automaticBillingModalTableRow').classList.remove('d-none');
            document.querySelector('#automaticBillingModalSumRow').classList.remove('d-none');
            document.querySelector('#automaticBillingModalTableBody').innerHTML = response.data;
            let [sumOrders, sumAmount] = autoBillingSum('automaticBillingModalTableBody');
            document.querySelector('#automaticBillingModalSumOrders').innerText = sumOrders;
            document.querySelector('#automaticBillingModalSumAmount').innerText = sumAmount + ' €';
            autoBillingConfirmBtnSetDisabled(false);
        }
    })
    .catch((error) => {
        console.log(error);
    });
}

function autoBillingConfirm() {
    let orderIdsToBill = '';
    for (let row of document.querySelector('#automaticBillingModalTableBody').children){
        let rowOrderId = row.children[0].innerText;
        orderIdsToBill += `${rowOrderId};`
    }
    sendRequest('/api/controlling/create_new_billing', {'orderIdsToBill': orderIdsToBill,})
    .then((response) => {
        document.querySelector('#automaticBillingModalTableRow').classList.add('d-none');
        document.querySelector('#automaticBillingModalSumRow').classList.add('d-none');
        autoBillingConfirmBtnSetDisabled(true);
        filter();
    })
    .catch((error) => {
        console.log(error);
    });
}

function autoBillingSum(tableBody){
    let sumAmount = 0.0;
    modalRows = [...document.querySelector(`#${tableBody}`).children];
    for (let row of modalRows) {
        sumAmount += parseFloat(row.children[3].innerText.replace(',', '.'));
    }
    return [modalRows.length, sumAmount.toFixed(2).toString().replace('.', ',')];
}

// deactive confirm button after inputs have been changed (e.g. after searching)
function autoBillingConfirmBtnSetDisabled(disabledState = true) {
    document.querySelector('#modalBtnAutoBillingConfirm').disabled = disabledState;
}

function printBilling(button){
    // get id from button
    id = button.parentElement.id.split('_')[1]
    axios.get('print', {
        params: {
            'billingId': id,
        },
    })
    .then((response) => {
        document.querySelector('#controllingPrintBilling').innerHTML = response.data;
        
        let [sumOrders, sumAmount] = autoBillingSum('printTableBody');
        document.querySelector('#printAmountOfOrders').innerText = sumOrders;
        document.querySelector('#printSumOfOrders').innerText = sumAmount + ' €';

        // grab already existing html from frontend
        let infoTableBody = document.querySelector('#printInfoTableBody');
        let infoTableRow = document.createElement('tr');
        
        let dateBilled = document.createElement('td');
        dateBilled.classList.add('text-center');
        dateBilled.innerText = document.querySelector(`#billing_${id}_date`).innerText;

        let datePeriod = document.createElement('td');
        datePeriod.classList.add('text-center');
        datePeriod.innerText = document.querySelector(`#billing_${id}_period`).innerText;

        let amountOfOrders = document.createElement('td');
        amountOfOrders.classList.add('text-center');
        amountOfOrders.innerText = sumOrders;

        let sumOfOrders = document.createElement('td');
        sumOfOrders.classList.add('text-center');
        sumOfOrders.innerText = sumAmount + ' €';

        infoTableRow.append(dateBilled);
        infoTableRow.append(datePeriod);
        infoTableRow.append(amountOfOrders);
        infoTableRow.append(sumOfOrders);
        infoTableBody.innerHTML = '';
        infoTableBody.append(infoTableRow);
        setTimeout(print, 100);
    })
    .catch((error) => {
        console.log(error);
    });
}

// only trigger filter if no input for delay ms
function debounceFilter(delay) {
    let timer;
    return () => {
        clearTimeout(timer);
        timer = setTimeout(() => {
            filter();
        }, delay);
    }
}

// EVENT LISTENERS

const onFinishTyping = debounceFilter(300);
document.querySelector('#entryHeader').addEventListener('keyup', (evt) => evt.keyCode === 13 && filter());
document.querySelector('#entryHeader').addEventListener('input', onFinishTyping);
document.querySelector('#billNowButton').addEventListener('click', (evt) => billCurrentSelection(evt.target));
document.querySelector('#alreadyBilledButton').addEventListener('click', getAlreadyBilledModal);
document.querySelector('#modalBtnAutoBillingSearch').addEventListener('click', autoBilling);
document.querySelector('#modalBtnAutoBillingConfirm').addEventListener('click', autoBillingConfirm);
document.querySelector('#maxAmountInputAutoBilling').addEventListener('input', autoBillingConfirmBtnSetDisabled);
document.querySelector('#dateInputAutoBilling').addEventListener('input', autoBillingConfirmBtnSetDisabled);
document.querySelector('#headCheckbox').addEventListener('input', (evt) => {
    evt.stopPropagation();
    checkAllNonBilledEntries(evt.target.checked);
});
[...document.querySelectorAll('.sort-span')].forEach((elem) => {
    elem.addEventListener('click', (evt) => {
        evt.stopPropagation();
        handleSortStates(evt.target);
    });
});

// RUNTIME 

filter();