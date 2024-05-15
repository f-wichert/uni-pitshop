function setUpMaterialListModal(orderId, suborderId, fileName, userName) {
    let messageModal = new bootstrap.Modal(document.querySelector('#materialListModal'));
    let currentHeader = document.querySelector('#materialListModalHeader');
    let newHeaderText = `Materialliste | Datei: ${fileName} | Kunde: ${userName} | ID: ${orderId}`;
    if (currentHeader.innerText !== newHeaderText) {
        currentHeader.innerText = newHeaderText;
        updateMaterialList(orderId, suborderId);
    }
    messageModal.show();
}

function addNewMaterialListRow(orderId, lasercutId, save) {
    let relevantInputs = [...document.querySelectorAll(`#newMaterialListRow .newRowInput`)];
    let relevantInputsCut = [...document.querySelectorAll(`#newMaterialListRow .newRowInputCut`)];
    let addButton = document.querySelector(`#order_${orderId}_material_suborder_new_material_list_row_add`);
    let saveButton = document.querySelector(`#order_${orderId}_material_suborder_new_material_list_row_save`);
    if (save) {
        relevantInputs.forEach(el => el.disabled = true);
        relevantInputsCut.forEach(el => el.disabled = true);
        addButton.classList.remove('d-none');
        saveButton.classList.add('d-none');
        saveNewMaterialListRow(orderId, lasercutId);
    }
    // enable editing
    else {
        relevantInputs.forEach(el => el.disabled = false);
        addButton.classList.add('d-none');
        saveButton.classList.remove('d-none');
        updateNewMaterialListRow(orderId, true);
    }
}

function updateNewMaterialListRow(orderId, setup, materialId = null) {
    let selectMaterial = document.querySelector(`#order_${orderId}_material_suborder_new_material_list_row_material_select`);
    let inputAmount = document.querySelector(`#order_${orderId}_material_suborder_new_material_list_row_amount_input`);
    let selectDimensions = document.querySelector(`#order_${orderId}_material_suborder_new_material_list_row_variation_select`);
    let inputLength = document.querySelector(`#order_${orderId}_material_suborder_new_material_list_row_length_input`);
    let inputWidth = document.querySelector(`#order_${orderId}_material_suborder_new_material_list_row_width_input`);
    let selectedMaterial = null;
    // happens if add row was clicked
    if (setup) {
        let relevantMaterials = gMaterialInformation.filter(ma => ma.has_lasercutable_variation);
        selectedMaterial = relevantMaterials[0];
        // setup material options
        let html = '';
        relevantMaterials.forEach((ma, i) => {
            html += `<option value="${ma.material_id}" ${i === 0 ? 'selected' : ''}> ${ma.name} </option>`;
        });
        selectMaterial.innerHTML = html;
        inputAmount.value = 1;
    }
    // not setup => material was selected from material select
    else {
        selectedMaterial = gMaterialInformation.find(ma => ma.material_id === parseInt(materialId));
    }
    let relevantVariations = selectedMaterial.variationArray.filter(va => va.is_lasercutable);
    // setup variation options
    let html = '';
    relevantVariations.forEach((va, i) => {
        html += `<option value="${va.variation_id}" ${i === 0 ? 'selected' : ''}>
            ${va.thickness.toFixed(1)} x ${va.length} x ${va.width}</option>`.replace('.', ',');
    });
    selectedVariation = relevantVariations[0];
    selectDimensions.innerHTML = html;

    if (!selectedMaterial.is_fixed){
        inputLength.disabled = false;
        inputLength.value = selectedVariation.length;
        inputLength.max = selectedVariation.length;
        inputWidth.disabled = false;
        inputWidth.value = selectedVariation.width;
        inputWidth.max = selectedVariation.width;
    }
    else {
        inputLength.disabled = true;
        inputLength.value = '';
        inputWidth.disabled = true;
        inputWidth.value = '';
    }
    updatePriceNewMaterialListRow(orderId);
}

function updatePriceNewMaterialListRow(orderId) {
    let variation = getVariation(orderId);
    let amount = parseInt(document.querySelector(`#order_${orderId}_material_suborder_new_material_list_row_amount_input`).value);
    let length = document.querySelector(`#order_${orderId}_material_suborder_new_material_list_row_length_input`).value;
    let width = document.querySelector(`#order_${orderId}_material_suborder_new_material_list_row_width_input`).value;
    let price = document.querySelector(`#order_${orderId}_material_suborder_new_material_list_row_price`);
    let calc_price = (length === '' ? variation.length : parseInt(length))  * (width === '' ? variation.width : parseInt(width))
        * variation.price * amount;
    price.innerText = `${(parseFloat(calc_price)/1e8).toFixed(2)}`.replace('.', ',');
}

function saveNewMaterialListRow(orderId, lasercutId){
    let variation = getVariation(orderId);
    let amount = parseInt(document.querySelector(`#order_${orderId}_material_suborder_new_material_list_row_amount_input`).value);
    let length = document.querySelector(`#order_${orderId}_material_suborder_new_material_list_row_length_input`).value;
    let width = document.querySelector(`#order_${orderId}_material_suborder_new_material_list_row_width_input`).value;
    sendRequest('/api/add_suborder/', {
        'amount': amount,
        'type': 'material',
        'order_id': orderId,
        'lasercut_id': lasercutId,
        'variation_id': variation.variation_id,
        'length': (length === '' ? variation.length : parseInt(length)),
        'width': (width === '' ? variation.width : parseInt(width)),
    })
    .then((response) => {
        updateMaterialList(orderId, lasercutId);
    })
    .catch((error) => {
        console.log(error);
    })
}

function updateMaterialList(orderId, suborderId){
    axios.get('/orders/material_data_for_lasercut/', {
        params: {
            'orderId': orderId,
            'suborderId': suborderId,
        },
    })
    .then((response) => {
        document.querySelector('#materialListModalBody').innerHTML = response.data;
    })
    .catch((error) => {
        console.log(error);
    })
}
function deleteMaterialListRow(orderId, materialSuborderId, lasercutSuborderId, button){
    button.disabled = true;
    if (button.classList.contains('clickedOnce')){
        sendRequest('/api/remove_suborder/', {
            'type': 'material',
            'id': materialSuborderId,
            'order_id': orderId,
        })
        .then((response) => {
            updateMaterialList(orderId, lasercutSuborderId); // update billing table and order table
        })
        .catch((error) => {
            console.log(error);
        });
    }
    else {
        setTimeout(() => { // setTimeout to disable fast double clicking to delete
            button.classList.add('clickedOnce');
            button.classList.replace('btn-light', 'btn-danger');
            button.children[0].src = CONFIRM_DELETE;
            button.disabled = false;
        }, 200);
    }
}

function changeMaterialVariationNewMaterialListRow(orderId, variationId){
    let inputLength = document.querySelector(`#order_${orderId}_material_suborder_new_material_list_row_length_input`);
    let inputWidth = document.querySelector(`#order_${orderId}_material_suborder_new_material_list_row_width_input`);
    let variation = getVariation(orderId);

    inputLength.max = variation.length;
    validateMaterialInput(inputLength);
    inputWidth.max = variation.width;
    validateMaterialInput(inputWidth);
    updatePriceNewMaterialListRow(orderId, variationId, inputLength.value, inputWidth.value);
}

function getMaterial(orderId) {
    let selectMaterial = document.querySelector(`#order_${orderId}_material_suborder_new_material_list_row_material_select`);
    return gMaterialInformation.find(ma => ma.material_id === parseInt(selectMaterial.options[selectMaterial.selectedIndex].value));
}

function getVariation(orderId){
    let material = getMaterial(orderId);
    let selectVariation = document.querySelector(`#order_${orderId}_material_suborder_new_material_list_row_variation_select`);
    let variation = material.variationArray.find(va => va.variation_id === parseInt(selectVariation.options[selectVariation.selectedIndex].value));
    return variation;
}