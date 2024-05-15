function updateMaterialPrice(orderId, suborderId, price){
    document.querySelector(`#order_${orderId}_material_suborder_${suborderId}_price_input`).value = price;
}

function setMaterialAmount(orderId, suborderId, amount, input){
    if (amount === '') return;
    amount = parseInt(amount);
    if (amount < materialAmountMin) amount = materialAmountMin;
    else if (amount > materialAmountMax) amount = materialAmountMax;
    input.value = amount;
    sendRequest('/api/change_suborder/', {
        'order_id': orderId,
        'id': suborderId,
        'type': 'material',
        'amount': amount,
        'get_price': true,
        'get_order_price_str': true,
    })
    .then((response) => {
        updatePriceFunctionObject['material'](orderId, suborderId, convertIntToPrice(response.data.price));
        updateOrderPrice(orderId, response.data.order_price_str);
    })
    .catch((error) => {
        console.log(error);
    })
}


function changeMaterialVariation(orderId, suborderId, materialId, variationId){
    let material = gMaterialInformation.find(ma => ma.material_id === materialId);
    if (material.is_fixed) {
        requestChangeSuborder(orderId, suborderId, 'material', {'variation_id': variationId},)
        .then((response) => {
            if (!response.data.change_suborder) return;
            updatePriceFunctionObject['material'](orderId, suborderId, convertIntToPrice(response.data.price));
            updateOrderPrice(orderId, response.data.order_price_str);
        })
        .catch((error) => {
            console.log(error);
        })
    }
    else {
        let length_input = document.querySelector(`#order_${orderId}_material_suborder_${suborderId}_length_input`);
        let width_input = document.querySelector(`#order_${orderId}_material_suborder_${suborderId}_width_input`);
        length_input.disabled = true;
        width_input.disabled = true;
        let variation = material.variationArray.find(va => va.variation_id === parseInt(variationId));
        length_input.max = variation.length;
        validateMaterialInput(length_input);
        width_input.max = variation.width;
        validateMaterialInput(width_input);

        requestChangeSuborder(orderId, suborderId, 'material',
            {'variation_id': variationId, 'length': length_input.value, 'width': width_input.value},)
        .then((response) => {
            if (!response.data.change_suborder) return;
            updatePriceFunctionObject['material'](orderId, suborderId, convertIntToPrice(response.data.price));
            updateOrderPrice(orderId, response.data.order_price_str);
            length_input.disabled = false;
            width_input.disabled = false;
        })
        .catch((error) => {
            console.log(error);
        })
    }
}

function changeMaterialDimension(orderId, suborderId, dimensionType, input){
    validateMaterialInput(input);
    input.disabled = true;

    requestChangeSuborder(orderId, suborderId, 'material', {[dimensionType]: input.value,},)
    .then((response) => {
        if (!response.data.change_suborder) return;
        updatePriceFunctionObject['material'](orderId, suborderId, convertIntToPrice(response.data.price));
        updateOrderPrice(orderId, response.data.order_price_str);
        input.disabled = false;
    })
    .catch((error) => {
        console.log(error);
    })
}

function validateMaterialInput(input) {
    let value = parseInt(input.value);
    let max = parseInt(input.max);
    if (value < 1) input.value = 1;
    else if (value > max) input.value = max;
}