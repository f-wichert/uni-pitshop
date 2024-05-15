
materialCards = document.querySelectorAll('.material-card');
materials = [];

for (let card of [...materialCards]) {
    materials.push(card.classList[1].slice(5));
};

errorMessage = document.querySelectorAll('#order-error-message');

var resolvedFlag = true;
let blinkAlert = function functionOne(i) {
    errorMessage[i].classList.add('alert-active');
    return new Promise((resolve, reject) => {
        setTimeout(
            () => {
                // TODO: This needs to be fixed, currently it is spammable
                errorMessage[i].classList.remove('alert-active');
                if (resolvedFlag == true) {
                    resolve("Resolved");
                } else {
                    reject("Rejected")
                }
            }, 2000
        );
    });
};

// Adding Eventlisteners to all neccessary
for (const [i, material] of [...materials].entries()) {

    // Length input constraint
    try {
        document.querySelector(`#${material}-length`).addEventListener('input', (event) => {
            if (parseInt(event.target.value) > parseInt(event.target.max)) {
                event.target.value = event.target.max;
            };
            event.preventDefault();
        });
    }
    catch (exception_var) {
        console.log('Error when adding event listener to length input!');
        console.log(exception_var);
    }
    
    // Width input constraint
    try {
        document.querySelector(`#${material}-width`).addEventListener('input', (event) => {
            if (parseInt(event.target.value) > parseInt(event.target.max)) {
                event.target.value = event.target.max;
            };
            event.preventDefault();
        });
    }
    catch (exception_var) {
        console.log('Error when adding event listener to width input!');
        console.log(exception_var);
    }

    // Submit Butttons
    document.querySelector(`#${material}-submit`).addEventListener('click', (event) => {

        material_name = material.replaceAll('_', ' ')
        console.log('Submit button was pressed');
        console.log(`Material ${material} - ${material_name}`);
        try {
            height = parseInt(document.querySelector(`#${material}-length`).value);
            width = parseInt(document.querySelector(`#${material}-width`).value);
        }
        catch (exception_var) {
            select = document.querySelector(`#${material}-dimension`)
            dimensions = select.options[select.selectedIndex].value.split(';')
            console.log(dimensions);

            height = dimensions[0]
            width = dimensions[1]

            console.log(exception_var);
            console.log('Fixed size');
        }
        console.log('---');

        amount = parseInt(document.querySelector(`#${material}-amount`).value);
        console.log(`Menge: ${amount}`);

        variation_id = document.querySelector(`#${material}-dimension`).value;
        console.log(`ID: ${variation_id}`);

        console.log(`Material: ${material_name}`);
        console.log(`Länge: ${length}`);
        console.log(`Breite: ${width}`);
        console.log('---');


        sendRequest('/api/add_suborder/', {
                type: 'material',
                comment: '',
                amount: amount,
                material_name: material_name,
                width: width,
                length: height,
                variation_id: variation_id,
            }).then((response) => {
                console.log(response.data);
                if (response.data == "add_suborder:true") {
                    let cartCanvasElement = document.getElementById("cartCanvas")
                    let cartCanvas = new bootstrap.Offcanvas(cartCanvasElement)
                    cartCanvas.toggle()
                } else {
                    blinkAlert(i)
                };
            })
            .catch((error) => {
                console.log("an error occured", error);
                blinkAlert(i)
            });
    });
};