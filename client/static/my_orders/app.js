console.log('My order detailed view script started!');

const lasercutTable = document.getElementById('lasercut-table-body');

const materialTable = document.getElementById('material-table-body');

// // Show orders
// getOrders().then(orders => {
//     // Show lasercut orders
//     orders[0].forEach(order => {
//         addLasercutRow(order);
//     });
//     // Show material orders
//     orders[1].forEach(order => {
//         addMaterialRow(order);
//     });
// });

// async function getOrders() {
//     const url = '/api/get_suborders';
    
//     result = await sendRequest(url, {'ID': ID});
//     return await result.data;
// }



function test() {
    console.log('mock orders');
    let testLasercut = {
        material: 'Baum',
        status: 'fast fertig',
        price: '13.99',
        date: '01.01.2020',
        comment: 'Was ein Müll ist das bitte!',
        orderNumber: '69420',
    };
    
    let testMaterialOrder = {
        materialName: 'Baum',
        status: 'fast fertig',
        price: '13.99',
        date: '01.01.2020',
        size: '20x20',
        quantity: '5',
        comment: 'Was ein Müll ist das bitte!',
        orderNumber: '69421',
    };
    
    
    addLasercutRow(testLasercut);
    addLasercutRow(testLasercut);
    addLasercutRow(testLasercut);
    addLasercutRow(testLasercut);
    
    
    addMaterialRow(testMaterialOrder);
    addMaterialRow(testMaterialOrder);
    addMaterialRow(testMaterialOrder);
    addMaterialRow(testMaterialOrder);    
}

function addLasercutRow(lasercut) {
    let row = document.createElement('tr');
    row.classList.add('lasercut-row');
    
    let material = document.createElement('td');
    material.innerHTML = lasercut['material'];
    row.appendChild(material);

    let status = document.createElement('td');
    status.innerHTML = lasercut['status'];
    row.appendChild(status);

    let price = document.createElement('td');
    price.innerHTML = lasercut['price-estimate'];
    row.appendChild(price);

    let date = document.createElement('td');
    date.innerHTML = lasercut['date'];
    row.appendChild(date);

    let comment = document.createElement('td');
    comment.innerHTML = lasercut['comment'];
    row.appendChild(comment);

    let messages = document.createElement('td');
        let messageIcon = document.createElement('img');
        messageIcon.src = MESSAGE_ICON;
        messageIcon.classList.add('icon');
        messages.appendChild(messageIcon);
    row.appendChild(messages);

    let orderNumber = document.createElement('td');
    orderNumber.innerHTML = lasercut['id'];
    row.appendChild(orderNumber);

    let deleteButton = document.createElement('td');
        let deleteIcon = document.createElement('img');
        deleteIcon.src = TRASHCAN_ICON;
        deleteIcon.classList.add('icon');
        deleteButton.appendChild(deleteIcon);
    row.appendChild(deleteButton);

    lasercutTable.appendChild(row);

    deleteButton.addEventListener('click', () => {
        sendRequest('/api/remove_suborder/', {'type': "lasercut", 'id': lasercut['id']});
        row.remove();
    });
    
}


function addMaterialRow(material) {
    let row = document.createElement('tr');
    row.classList.add('material-row');
    
    let materialName = document.createElement('td');
    materialName.innerHTML = material.material;
    row.appendChild(materialName);

    let status = document.createElement('td');
    status.innerHTML = material.status;
    row.appendChild(status);

    let price = document.createElement('td');
    price.innerHTML = material.price;
    row.appendChild(price);

    let date = document.createElement('td');
    date.innerHTML = material.date;
    row.appendChild(date);

    let size = document.createElement('td');
    size.innerHTML = material.size_width + 'x' + material.size_height;
    row.appendChild(size);

    let quantity = document.createElement('td');
    quantity.innerHTML = material.quantity;
    row.appendChild(quantity);

    let comment = document.createElement('td');
    comment.innerHTML = material.comment;
    row.appendChild(comment);

    let messages = document.createElement('td');
        let messageIcon = document.createElement('img');
        messageIcon.src = MESSAGE_ICON;
        messageIcon.classList.add('icon');
        messages.appendChild(messageIcon);
    row.appendChild(messages);

    let orderNumber = document.createElement('td');
    orderNumber.innerHTML = material.id;
    row.appendChild(orderNumber);

    let deleteButton = document.createElement('td');
        let deleteIcon = document.createElement('img');
        deleteIcon.src = TRASHCAN_ICON;
        deleteIcon.classList.add('icon');
        deleteButton.appendChild(deleteIcon);
    row.appendChild(deleteButton);

    materialTable.appendChild(row);

    deleteButton.addEventListener('click', () => {
        sendRequest('/api/remove_suborder/', {'type': "material", 'id': material.id});
        row.remove();
    });
}