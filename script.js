// ======================================================
// AI POCKET SCIENTIST
//
// STEP 0:
// Camera / Upload / Drag & Drop
// Image → Base64
//
// STEP 0.5:
// Local MobileNet Vision
//
// STEP 1:
// Backend researches websites
//
// STEP 2:
// Python summarizer
//
// STEP 3:
// Show answer
// ======================================================


// ======================================================
// HTML ELEMENTS
// ======================================================

const askButton =
    document.getElementById("askButton");

const questionInput =
    document.getElementById("question");

const answerBox =
    document.getElementById("answer");

const cameraButton =
    document.getElementById("cameraButton");

const imageInput =
    document.getElementById("imageInput");

const dropZone =
    document.getElementById("dropZone");

const placeholder =
    document.getElementById("placeholder");

const previewImage =
    document.getElementById("previewImage");

const cameraVideo =
    document.getElementById("cameraVideo");

const cameraControls =
    document.getElementById("cameraControls");

const takePhotoButton =
    document.getElementById("takePhotoButton");

const cancelCameraButton =
    document.getElementById("cancelCameraButton");

const removeImageButton =
    document.getElementById("removeImageButton");

const cameraCanvas =
    document.getElementById("cameraCanvas");


// ======================================================
// RENDER BACKEND
// ======================================================

const API_URL =
    "https://ai-pocket-scientist.onrender.com/ask";


// ======================================================
// VARIABLES
// ======================================================

let isThinking = false;

let selectedImageBase64 = "";

let cameraStream = null;

let visionModel = null;


// ======================================================
// LOAD MOBILENET
// ======================================================

async function loadVisionModel() {

    if (visionModel) {
        return visionModel;
    }

    console.log(
        "Loading vision model..."
    );

    visionModel =
        await mobilenet.load();

    console.log(
        "Vision model ready."
    );

    return visionModel;
}


// ======================================================
// WAIT UNTIL IMAGE IS READY
// ======================================================

function waitForImage(image) {

    return new Promise(
        function(resolve, reject) {

            if (
                image.complete &&
                image.naturalWidth > 0
            ) {

                resolve();
                return;
            }

            image.onload =
                function() {

                    resolve();
                };

            image.onerror =
                function() {

                    reject(
                        new Error(
                            "Image could not be loaded."
                        )
                    );
                };
        }
    );
}


// ======================================================
// ANALYZE IMAGE
// ======================================================

async function analyzeImage() {

    // No image = skip vision
    if (!selectedImageBase64) {
        return "";
    }

    answerBox.innerHTML =
        "👁️ Analyzing image...";

    // Make sure image preview is ready
    await waitForImage(
        previewImage
    );

    // Load MobileNet if needed
    await loadVisionModel();

    // Analyze the image
    const predictions =
        await visionModel.classify(
            previewImage
        );

    console.log(
        "All vision predictions:"
    );

    console.log(
        predictions
    );


    // ==================================================
    // USE ONLY THE BEST PREDICTION
    // ==================================================

    if (
        !predictions ||
        predictions.length === 0
    ) {

        console.log(
            "No vision result."
        );

        return "";
    }


    // First prediction has highest confidence
    const bestPrediction =
        predictions[0];


    console.log(
        "Best prediction:"
    );

    console.log(
        bestPrediction
    );


    // MobileNet may return:
    //
    // "lycaenid, lycaenid butterfly"
    //
    // Split into:
    //
    // lycaenid
    // lycaenid butterfly

    const names =
        bestPrediction.className
            .split(",")
            .map(
                name =>
                    name.trim()
            );


    // Prefer the more descriptive name
    // by choosing the longest one

    names.sort(
        (a, b) =>
            b.length - a.length
    );


    const bestLabel =
        names[0];


    console.log(
        "Image contains:"
    );

    console.log(
        bestLabel
    );


    return bestLabel;
}


// ======================================================
// ASK BUTTON
// ======================================================

askButton.addEventListener(
    "click",
    askAI
);


// ======================================================
// MAIN ASK FUNCTION
// ======================================================

async function askAI() {

    if (isThinking) {
        return;
    }


    const question =
        questionInput.value.trim();


    if (question === "") {

        answerBox.innerHTML =
            "⚠️ Please enter a question.";

        return;
    }


    isThinking = true;

    askButton.disabled = true;

    questionInput.disabled = true;


    try {

        let visionDescription = "";


        // ==============================================
        // OPTIONAL IMAGE ANALYSIS
        // ==============================================

        if (selectedImageBase64) {

            visionDescription =
                await analyzeImage();
        }


        // ==============================================
        // SEND TO BACKEND
        // ==============================================

        answerBox.innerHTML =
            "🔎 Researching websites...";


        const response =
            await fetch(
                API_URL,
                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({

                            question:
                                question,

                            vision:
                                visionDescription

                        })
                }
            );


        const data =
            await response.json();


        // ==============================================
        // SHOW ANSWER
        // ==============================================

        if (data.answer) {

            answerBox.innerHTML =
                data.answer.replace(
                    /\n/g,
                    "<br><br>"
                );
        }

        else {

            answerBox.innerHTML =
                "⚠️ No answer received.";
        }


        // ==============================================
        // DEBUG INFORMATION
        // ==============================================

        console.log(
            "Vision sent to research:"
        );

        console.log(
            visionDescription
        );


        if (data.sources) {

            console.log(
                "Research sources:"
            );

            console.log(
                data.sources
            );
        }

    }

    catch (error) {

        console.error(
            "ERROR:",
            error
        );

        answerBox.innerHTML =
            "❌ Something went wrong.";
    }

    finally {

        isThinking = false;

        askButton.disabled =
            false;

        questionInput.disabled =
            false;

        questionInput.focus();
    }
}


// ======================================================
// ENTER KEY
// ======================================================

questionInput.addEventListener(
    "keydown",
    function(event) {

        if (
            event.key === "Enter"
        ) {

            event.preventDefault();

            askAI();
        }
    }
);


// ======================================================
// CAMERA BUTTON
// ======================================================

cameraButton.addEventListener(
    "click",
    openCamera
);


// ======================================================
// OPEN CAMERA
// ======================================================

async function openCamera() {

    try {

        cameraStream =
            await navigator.mediaDevices
                .getUserMedia({

                    video: {

                        facingMode: {
                            ideal:
                                "environment"
                        }
                    },

                    audio: false
                });


        cameraVideo.srcObject =
            cameraStream;


        previewImage.style.display =
            "none";

        placeholder.style.display =
            "none";

        removeImageButton.style.display =
            "none";


        cameraVideo.style.display =
            "block";

        cameraControls.style.display =
            "flex";
    }

    catch (error) {

        console.error(
            "Camera error:",
            error
        );

        alert(
            "Camera could not be opened. Please allow camera permission or choose an image instead."
        );
    }
}


// ======================================================
// TAKE PHOTO BUTTON
// ======================================================

takePhotoButton.addEventListener(
    "click",
    takePhoto
);


// ======================================================
// TAKE PHOTO
// ======================================================

function takePhoto() {

    if (!cameraStream) {
        return;
    }


    cameraCanvas.width =
        cameraVideo.videoWidth;

    cameraCanvas.height =
        cameraVideo.videoHeight;


    const context =
        cameraCanvas.getContext(
            "2d"
        );


    context.drawImage(

        cameraVideo,

        0,
        0,

        cameraCanvas.width,
        cameraCanvas.height
    );


    // ==============================================
    // CAMERA IMAGE → BASE64
    // ==============================================

    selectedImageBase64 =
        cameraCanvas.toDataURL(

            "image/jpeg",

            0.9
        );


    console.log(
        "Camera image converted to Base64."
    );


    stopCamera();


    showImagePreview(
        selectedImageBase64
    );
}


// ======================================================
// CANCEL CAMERA
// ======================================================

cancelCameraButton.addEventListener(
    "click",
    function() {

        stopCamera();

        if (selectedImageBase64) {

            showImagePreview(
                selectedImageBase64
            );
        }

        else {

            showPlaceholder();
        }
    }
);


// ======================================================
// STOP CAMERA
// ======================================================

function stopCamera() {

    if (cameraStream) {

        cameraStream
            .getTracks()
            .forEach(
                track =>
                    track.stop()
            );

        cameraStream =
            null;
    }


    cameraVideo.srcObject =
        null;

    cameraVideo.style.display =
        "none";

    cameraControls.style.display =
        "none";
}


// ======================================================
// CLICK DROP AREA → FILE PICKER
// ======================================================

dropZone.addEventListener(
    "click",
    function() {

        if (cameraStream) {
            return;
        }

        imageInput.click();
    }
);


// ======================================================
// FILE SELECTED
// ======================================================

imageInput.addEventListener(
    "change",
    function() {

        const file =
            imageInput.files[0];

        if (!file) {
            return;
        }

        convertFileToBase64(
            file
        );
    }
);


// ======================================================
// DRAG OVER
// ======================================================

dropZone.addEventListener(
    "dragover",
    function(event) {

        event.preventDefault();

        dropZone.classList.add(
            "dragging"
        );
    }
);


// ======================================================
// DRAG LEAVE
// ======================================================

dropZone.addEventListener(
    "dragleave",
    function() {

        dropZone.classList.remove(
            "dragging"
        );
    }
);


// ======================================================
// DROP IMAGE
// ======================================================

dropZone.addEventListener(
    "drop",
    function(event) {

        event.preventDefault();

        dropZone.classList.remove(
            "dragging"
        );


        const file =
            event.dataTransfer
                .files[0];


        if (!file) {
            return;
        }


        convertFileToBase64(
            file
        );
    }
);


// ======================================================
// FILE → BASE64
// ======================================================

function convertFileToBase64(file) {

    if (
        !file.type.startsWith(
            "image/"
        )
    ) {

        alert(
            "Please choose an image file."
        );

        return;
    }


    const reader =
        new FileReader();


    reader.onload =
        function(event) {

            selectedImageBase64 =
                event.target.result;


            console.log(
                "Image converted to Base64."
            );


            showImagePreview(
                selectedImageBase64
            );
        };


    reader.onerror =
        function() {

            console.error(
                "Could not read image."
            );

            alert(
                "Could not read this image."
            );
        };


    reader.readAsDataURL(
        file
    );
}


// ======================================================
// SHOW IMAGE
// ======================================================

function showImagePreview(
    base64Image
) {

    placeholder.style.display =
        "none";

    cameraVideo.style.display =
        "none";

    previewImage.src =
        base64Image;

    previewImage.style.display =
        "block";

    removeImageButton.style.display =
        "block";
}


// ======================================================
// SHOW PLACEHOLDER
// ======================================================

function showPlaceholder() {

    previewImage.style.display =
        "none";

    previewImage.src =
        "";

    cameraVideo.style.display =
        "none";

    placeholder.style.display =
        "block";

    removeImageButton.style.display =
        "none";
}


// ======================================================
// REMOVE IMAGE
// ======================================================

removeImageButton.addEventListener(
    "click",
    function(event) {

        event.stopPropagation();

        selectedImageBase64 =
            "";

        imageInput.value =
            "";

        showPlaceholder();

        console.log(
            "Image removed."
        );
    }
);