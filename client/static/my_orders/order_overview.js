console.log('Hi');

function setUpMessageModalUserSide(img) {
    new bootstrap.Modal(document.querySelector('#messageModal')).show();
    img.src = MESSAGE_ICON;
    let tableRow = img.parentElement.parentElement;
    let orderId = tableRow.children[0].innerText;
    document.querySelector('#messageModalLabel').innerText = `Kontakt mit Pitshop  (BestellungsID: ${orderId})`;
    document.querySelector('.messageModalTextAreaRow').id = `messageModalTextAreaRow_${orderId}`;
    getMessages(orderId);
}

function saveMessage(btn) {
    let orderId = btn.parentElement.parentElement.id.split('_')[1];
    let textField = document.querySelector('#sendMessageTextField');

    textField.disabled = true;
    btn.disabled = true;
    sendRequest('/api/messenger/save_message/', {
        'orderId': orderId,
        'message': textField.value,
    })
    .then((response) => {
        btn.disabled = false;
        textField.disabled = false;
        textField.value = '';
        getMessages(orderId); // refresh messages
    })
    .catch((error) => {
        console.log(error);
    })
}

function getMessages(orderId) {
    axios.get('/messenger/get_messages_user/', {
        params: {
            'orderId': orderId,
        }
    })
    .then((response) => {
        document.querySelector('#messageModalTableBody').innerHTML = response.data;
    })
    .catch((error) => {
        console.log(error);
    })
}

function backendStateToFrontendState(backendState) {
    switch (backendState) {
        case 0: return "Eingereicht";
        case 1: return "In Bearbeitung";
        case 2: return "Abgeschlossen";
        case 3: return "In Bearbeitung";
    }
}

function filter() {
    axios.get('../my-orders-entries/', {
        // params: grabFilterValues(),
    })
    .then((response) => {
        document.querySelector('#entryBody').innerHTML = response.data

        // rows = document.querySelectorAll('tr')
        // for (let i = 1; i < rows.length; i++) {
        //     rows[i].children[3].innerHTML = backendStateToFrontendState(rows[i].children[3].innerHTML)
        // };
    })
    .catch((error) => {
        console.log(error)
    });
}


document.querySelector('#messageModalSendButton').addEventListener('click', (evt) => saveMessage(evt.target));
[...document.querySelectorAll('.messageIcon')].forEach((elem) => {
    elem.addEventListener('click', (evt) => {
        evt.stopPropagation();
        setUpMessageModalUserSide();
    });
});

filter();