const logoutButton = document.getElementById("logoutButton");
const cartCanvas = document.getElementById("cartCanvas");
const confirmOrderSubmitButton = document.getElementById("confirmOrderSubmitButton");


if (logoutButton) {
    logoutButton.addEventListener("click", logout);
    confirmOrderSubmitButton.addEventListener("click", cartSubmit)
    cartCanvas.addEventListener("show.bs.offcanvas", cartRefresh);
}


function cartRefresh() {
    const cartDiv = document.getElementById("cartDiv");

    // destroy old tooltips
    cartDiv.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(e => bootstrap.Tooltip.getInstance(e).dispose());

    sendRequest("/cart/table", {})
        .then((response) => {
            cartDiv.innerHTML = response.data;
            cartDiv.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(e => new bootstrap.Tooltip(e))
        })
        .catch((error) => {
            cartDiv.innerHTML = "Es gab ein Problem mit dem Warenkorb, versuchen sie die Seite neu zu laden"
            console.log("an error occured", error);
        });
}


function cartGetMaterialVariationInformation(variationId) {
    for (let material of gMaterialInformation) {
        for (let materialVariation of material.variationArray) {
            if (materialVariation.variation_id == variationId) {
                return [material, materialVariation];
            }
        }
    }
}


function cartChangeSuborder(element, id, type, change) {
    let data = {
        id: id,
        type: type,
        get_price_str: true,
        get_order_price_str: true,
    };

    let value = element.value;
    let material, materialVariation;

    if (type === "material") {
        const variationId = change === "variation_id" ? value : document.getElementById("materialDimensionSelect" + id).value;
        [material, materialVariation] = cartGetMaterialVariationInformation(variationId);

        if (change === "amount" || change === "length" || change === "width") {
            value = Number(element.value);

            let min = 1;
            let max = 99;
            if (change !== "amount") {
                if (change === "length") max = materialVariation.length;
                else max = materialVariation.width;
            }

            if (!Number.isInteger(value) || value < min) value = min;
            else if (value > max) value = max;

            element.value = value;
        } else if (change === "variation_id") {
            const lengthIn = document.getElementById("materialLengthInput" + id);
            const widthIn = document.getElementById("materialWidthInput" + id);

            if (lengthIn.value > materialVariation.length) {
                lengthIn.value = materialVariation.length;
            } else if (lengthIn.value < 1) {
                lengthIn.value = 1;
            }

            if (widthIn.value > materialVariation.width) {
                widthIn.value = materialVariation.width;
            } else if (widthIn.value < 1) {
                widthIn.value = 1;
            }

            data["length"] = lengthIn.value;
            data["width"] = widthIn.value;
        }
    }

    data[change] = value;

    sendRequest("/api/change_suborder/", data)
        .then((response) => {
            if (response.data.change_suborder) {
                if (type === "material") {
                    document.getElementById("cartFinalPrice").innerHTML = response.data.order_price_str;
                    document.getElementById("materialPrice" + id).innerHTML = response.data.price_str
                    if (change === "variation_id" && !material.is_fixed) {
                        const materialRow = document.getElementById("cartRowmaterial" + id)
                        const lengthIn = document.getElementById("materialLengthInput" + id);
                        const widthIn = document.getElementById("materialWidthInput" + id);

                        materialRow.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(e => bootstrap.Tooltip.getInstance(e).dispose());

                        lengthIn.setAttribute("title", "Wertebereich: 1 - " + materialVariation.length);
                        widthIn.setAttribute("title", "Wertebereich: 1 - " + materialVariation.width);

                        materialRow.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(e => new bootstrap.Tooltip(e))
                    }
                }
            } else console.log("there was a problem", response);
        })
        .catch((error) => {
            console.log("an error occured", error);
        });
}


function cartSubmit() {
    sendRequest("/api/submit_order/", {})
        .then((response) => {
            if (response.data == "submit_order:true") location.assign("/my-orders");
            else console.log("there was a problem", response);
        })
        .catch((error) => {
            console.log("an error occured", error);
        });
}


function cartRemove(id, type) {
    sendRequest("/api/remove_suborder/", {
            id: id,
            type: type
        })
        .then((response) => {
            if (response.data == "remove_suborder:true") cartRefresh();
            else console.log("there was a problem", response);
        })
        .catch((error) => {
            console.log("an error occured", error);
        });
}


function logout() {
    sendRequest("/api/unauth/", {})
        .then(function (response) {
            if (response.data == "unauth:true") location.assign("/login");
            else console.log("a problem occured", response);
        })
        .catch(function (error) {
            console.log("an error occured", error);
        });
}

function highlightCurrentPage() {
    [...document.querySelectorAll('a')].forEach((elem) => {
        if (elem.href === window.location.href) {
            elem.classList.add('active');
        }
    })
}

highlightCurrentPage();
