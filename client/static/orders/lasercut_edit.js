function setLaserCutMinutes(orderId, suborderId, minutes) {
    if (minutes === '') return;
    sendRequest('/api/change_suborder/', {
        'order_id': orderId,
        'id': suborderId,
        'type': 'lasercut',
        'minutes': minutes,
        'get_price': true,
        'get_order_price_str': true,
    })
    .then((response) => {
        updatePriceFunctionObject['lasercut'](orderId, suborderId, convertIntToPrice(response.data.price));
        updateOrderPrice(orderId, response.data.order_price_str);
    })
    .catch((error) => {
        console.log(error);
    })
}

function updateLasercutPrice(orderId, suborderId, price){
    document.querySelector(`#order_${orderId}_lasercut_suborder_${suborderId}_price_input`).value = price;
}

