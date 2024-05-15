function setUpMessageModalStaffSide(orderId, orderName, img) {
    let messageModal = new bootstrap.Modal(document.querySelector('#messageModal'));
    messageModal.show();
    document.querySelector('#messageModalLabel').innerText = `Kontakt mit ${orderName}  (BestellungsID: ${orderId})`;
    document.querySelector('.messageModalBody').id = `messageModalBody_${orderId}`;
    img.src = MESSAGE_ICON;
    getMessages(orderId);
}

function saveMessage(btn) {
    let orderId = document.querySelector('.messageModalBody').id.split('_')[1];
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
    axios.get('/messenger/get_messages/', {
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

document.querySelector('#messageModalSendButton').addEventListener('click', (evt) => saveMessage(evt.target));