(function () {
    const cardTemplate = $('script[data-template="lc-card"]').text();
    const uploadProgress = $("#upload-progress");

    function createNewSubJob() {
        // create a copy of the template
        const el = $(cardTemplate);
        // register close button event listener
        el.find(".sub-job-close").click(() => el.remove());

        const selectMaterial = el.find(".lc-material");
        const selectVariation = el.find(".lc-variation");
        const cutGroup = el.find(".lc-cut-group");

        let selectedMaterial = null;

        function updateCutFields() {
            // updates length/width fields depending on selected material
            const isFixed = !selectedMaterial || selectedMaterial.is_fixed;
            if (isFixed) {
                cutGroup.addClass("d-none");
            } else {
                cutGroup.removeClass("d-none");
                const variationID = parseInt(selectVariation.val());  // this should always be set if a valid material is selected
                const selectedVariation = selectedMaterial.variationArray.find(va => va.variation_id === variationID);
                // update value and max for length/width fields based on selected variation
                for (const prop of ["length", "width"]) {
                    cutGroup.find(`.lc-cut-${prop}`).prop("value", selectedVariation[prop]).prop("max", selectedVariation[prop]);
                }
            }
        }

        // update other dropdowns if material dropdown changed
        selectMaterial.change((e) => {
            selectVariation.empty();
            if (["", "-1"].includes(e.target.value)) {
                selectVariation.prop("disabled", true);
                selectedMaterial = null;
            } else {
                selectVariation.prop("disabled", false);

                const materialID = parseInt(e.target.value);
                selectedMaterial = gMaterialInformation.find(ma => ma.material_id === materialID);
                const relevantVariations = selectedMaterial.variationArray.filter(va => va.is_lasercutable);

                for (const va of relevantVariations) {
                    selectVariation.append(
                        $("<option>")
                        .prop("value", va.variation_id)
                        .text(`${va.thickness.toFixed(1)} x ${va.length} x ${va.width}`)
                    );
                }
            }

            updateCutFields();
        });

        selectVariation.change((e) => {
            updateCutFields();
        });

        // append card to list of other cards
        $("#sub-jobs").append(el);
    }

    function setProgress(percentage) {
        uploadProgress.width(`${percentage}%`).text(`${Math.round(percentage)}%`);
    }


    $("#add-sub-job").click(createNewSubJob);


    function sendForm(url, config = undefined) {
        $("#lc-submit").prop("disabled", true);
        $("#lc-preview").prop("disabled", true);

        setProgress(0);
        uploadProgress.removeClass(["bg-success", "bg-danger"]).addClass("progress-bar-animated");

        return sendRequest(
            url,
            new FormData($("#main-form")[0]),
            {
                onUploadProgress: (progressEvent) => {
                    if (!progressEvent.lengthComputable)
                        return;
                    const percentage = progressEvent.loaded * 100 / progressEvent.total;
                    setProgress(percentage);
                },
                ...config,
            },
        ).then((response) => {
            uploadProgress.addClass("bg-success").removeClass("progress-bar-animated");
            return response;
        }).catch((err) => {
            uploadProgress.removeClass("progress-bar-animated");
            return err;
        });
    }

    $("#main-form").submit((e) => {
        e.preventDefault();

        sendForm(e.target.target)
            .then((response) => {
                if (response.data === "add_suborder:true") {
                    const cartCanvasElement = $("#cartCanvas");
                    const cartCanvas = new bootstrap.Offcanvas(cartCanvasElement);
                    cartCanvas.toggle();
                }
            })
            .catch((err) => {
                // TODO: this doesn't work if responseType is set to "blob"
                if (axios.isAxiosError(err) && !err.response) {
                    uploadProgress.addClass("bg-danger");
                }
            });
    });

    $("#lc-preview").click((e) => {
        $("#lc-submit").prop("disabled", true);
        $("#lc-preview").prop("disabled", true);

        sendForm(
            $("#lc-preview").data("url"),
            {responseType: "blob"},
        ).then((response) => {
            if (response.status === 200) {
                $("#lc-preview-img").attr("src", URL.createObjectURL(response.data));
            }
        }).finally(() => {
            $("#lc-submit").prop("disabled", false);
            $("#lc-preview").prop("disabled", false);
        });
    });


    // create initial
    createNewSubJob();
})();
