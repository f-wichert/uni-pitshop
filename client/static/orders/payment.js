Date.prototype.toDateInputValue = (function() {
    var local = new Date(this);
    local.setMinutes(this.getMinutes() - this.getTimezoneOffset());
    return local.toJSON().slice(0,10);
});

function setUpPaymentModalStaffSide(orderId, orderName) {
    let messageModal = new bootstrap.Modal(document.querySelector('#paymentModal'));
    messageModal.show();
    document.querySelector('#paymentModalLabel').innerText = `Bezahlung von ${orderName}  (BestellungsID: ${orderId})`;
    document.querySelector('.paymentModalBody').id = `paymentModalBody_${orderId}`;
    document.querySelector('#nav-quittung').innerHTML = '';
    document.querySelector('#nav-rechnung').innerHTML = '';
    loadQuittungData();
    loadInvoiceData();
}

function printQuittung(){
    let orderId = document.querySelector('.paymentModalBody').id.split('_')[1];
    let alternateDate = document.querySelector('#receiptAlternateDate').value;
    axios.get('/orders/quittung/', {
        params: {
            'orderId': orderId,
            'alternateDate': alternateDate,
        },
    })
    .then((response) => {
        document.querySelector('#paymentPrintDiv').innerHTML = response.data;
        setTimeout(print, 100);
    })
    .catch((error) => {
        console.log(error);
    })
}

function loadQuittungData(){
    let orderId = document.querySelector('.paymentModalBody').id.split('_')[1];
    axios.get('/orders/quittung_data/', {
        params: {
            'orderId': orderId,
        },
    })
    .then((response) => {
        document.querySelector('#nav-quittung').innerHTML = response.data;
        document.querySelector('#receiptAlternateDate').value = new Date().toDateInputValue();
    })
    .catch((error) => {
        console.log(error);
    })
}

function loadInvoiceData(){
    let orderId = document.querySelector('.paymentModalBody').id.split('_')[1];
    axios.get('/orders/invoice_data/', {
        params: {
            'orderId': orderId,
        },
    })
    .then((response) => {
        document.querySelector('#nav-rechnung').innerHTML = response.data;
        document.querySelector('#inputRechnungsDatum').value = new Date().toDateInputValue();
    })
    .catch((error) => {
        console.log(error);
    })
}

function setStateToQuittung(btn) {
    let orderId = document.querySelector('.paymentModalBody').id.split('_')[1];
    axios.get('/orders/payment_state/', {
        params: {
            'orderId': orderId,
            'isRechnung': false,
        },
    })
    .then((response) => {
        loadQuittungData();
    })
    .catch((error) => {
        console.log(error);
    })
}

function setStateToInvoice(btn) {
    let orderId = document.querySelector('.paymentModalBody').id.split('_')[1];
    axios.get('/orders/payment_state/', {
        params: {
            'orderId': orderId,
            'isRechnung': true,
        },
    })
    .then((response) => {
        loadInvoiceData();
    })
    .catch((error) => {
        console.log(error);
    })
}

function rechnungAddRow(btn){
    let tableBody = document.querySelector('#rechnungTableBody');
    let tr = document.createElement('tr');
    tr.innerHTML =`
    <td><input type="checkbox" checked></td>
    <td class="text-center align-middle"><input required class="textbox-n form-control" type="text"/></td>
    <td class="text-center align-middle"><input required class="textbox-n form-control" type="number"/></td>
    <td class="text-center align-middle"><input required class="textbox-n form-control" type="number"/></td>
    <td class="text-center align-middle"><input required class="textbox-n form-control" type="number"/></td>
    <td class="text-center align-middle" id="billing_{{billing.id}}_delete">
        <button type="button" class="btn btn-danger" onclick="deletePaymentRow(event.target);">
            <img src="/static/global_svg/trash_can.svg" alt="trashcan_svg" class="img-fluid">
        </button>
    </td>   
    `
    tableBody.append(tr);
}

function deletePaymentRow(target) {
    let btn = target.nodeName === 'IMG' ? target.parentElement : target;
    btn.parentElement.parentElement.remove();
}

function printRechnung() {
    let serviceArray = [];
    [...document.querySelector('#rechnungTableBody').children].forEach((row) => {
        let rowChildren = row.children;
        if (rowChildren[0].children[0].checked) { // checked checkbox
            serviceArray.push({
                'descr': rowChildren[1].children[0].value,
                'amount': rowChildren[2].children[0].value,
                'price': rowChildren[3].children[0].value,
                'total_price': rowChildren[4].children[0].value,
            });
        }
    });

    axios.get('/orders/invoice/', {
        params: {
            'invoiceNr': document.querySelector('#inputRechnungsnummer').value,
            'invoiceDate': document.querySelector('#inputRechnungsDatum').value,
            'invoiceAdress': document.querySelector('#inputRechnungsadresse').value,
            'invoiceIntro': document.querySelector('#inputRechnungsanschreiben').value,
            'serviceArray': JSON.stringify(serviceArray),
        },
    })
    .then((response) => {
        document.querySelector('#paymentPrintDiv').innerHTML = response.data;
        setTimeout(print, 100);
    })
    .catch((error) => {
        console.log(error);
    })
}

document.querySelector('#nav-rechnung-tab').addEventListener('click', loadInvoiceData);
document.querySelector('#nav-quittung-tab').addEventListener('click', loadQuittungData);