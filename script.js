// ======================================================
// AI POCKET SCIENTIST
// WEB SEARCH MODE + AI MODE
// ======================================================


// ======================================================
// ELEMENTS
// ======================================================

const webModeButton =
    document.getElementById("webModeButton");

const aiModeButton =
    document.getElementById("aiModeButton");


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
// BACKEND
// ======================================================

const API_URL =
    "https://ai-pocket-scientist.onrender.com/ask";


// ======================================================
// VARIABLES
// ======================================================

// Default mode
let currentMode = "web";

let isThinking = false;

let selectedImageBase64 = "";

let cameraStream = null;

let visionModel = null;


// ======================================================
// MODE BUTTONS
// ======================================================

webModeButton.addEventListener(
    "click",
    function () {

        currentMode = "web";

        webModeButton.classList.add(
            "active"
        );

        aiModeButton.classList.remove(
            "active"
        );

        console.log(
            "Mode: WEB SEARCH"
        );
    }
);


aiModeButton.addEventListener(
    "click",
    function () {

        currentMode = "ai";

        aiModeButton.classList.add(
            "active"
        );

        webModeButton.classList.remove(
            "active"
        );

        console.log(
            "Mode: AI"
        );
    }
);


// ======================================================
// LOAD VISION
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
// WAIT FOR IMAGE
// ======================================================

function waitForImage(image) {

    return new Promise(
        function (resolve, reject) {

            if (
                image.complete &&
                image.naturalWidth > 0
            ) {

                resolve();
                return;
            }


            image.onload = resolve;


            image.onerror =
                function () {

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

    if (!selectedImageBase64) {

        return "";
    }


    answerBox.textContent =
        "👁️ Analyzing image...";


    await waitForImage(
        previewImage
    );


    await loadVisionModel();


    const predictions =
        await visionModel.classify(
            previewImage
        );


    console.log(
        "All vision predictions:",
        predictions
    );


    if (
        !predictions ||
        predictions.length === 0
    ) {

        return "";
    }


    // Highest-confidence prediction
    const bestPrediction =
        predictions[0];


    // Example:
    // "lycaenid, lycaenid butterfly"

    const names =
        bestPrediction.className
            .split(",")
            .map(
                name =>
                    name.trim()
            );


    // Pick most descriptive name
    names.sort(
        (a, b) =>
            b.length - a.length
    );


    const bestLabel =
        names[0];


    console.log(
        "Image contains:",
        bestLabel
    );


    return bestLabel;
}


// ======================================================
// ASK
// ======================================================

askButton.addEventListener(
    "click",
    askAI
);


async function askAI() {

    if (isThinking) {
        return;
    }


    const question =
        questionInput.value.trim();


    if (question === "") {

        answerBox.textContent =
            "⚠️ Please enter a question.";

        return;
    }


    isThinking = true;

    askButton.disabled = true;

    questionInput.disabled = true;


    try {

        let visionDescription = "";


        // ----------------------------------------------
        // SAME VISION SYSTEM FOR BOTH MODES
        // ----------------------------------------------

        if (selectedImageBase64) {

            visionDescription =
                await analyzeImage();
        }


        if (currentMode === "web") {

            answerBox.textContent =
                "🔎 Researching websites...";
        }

        else {

            answerBox.textContent =
                "🤖 Asking AI...";
        }


        // ----------------------------------------------
        // SEND MODE + QUESTION + VISION
        // ----------------------------------------------

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
                                visionDescription,

                            mode:
                                currentMode

                        })
                }
            );


        const data =
            await response.json();


        if (data.answer) {

            answerBox.textContent =
                data.answer;
        }

        else {

            answerBox.textContent =
                "⚠️ No answer received.";
        }


        console.log(
            "Mode sent:",
            currentMode
        );


        console.log(
            "Vision sent:",
            visionDescription
        );


        if (data.sources) {

            console.log(
                "Sources:",
                data.sources
            );
        }


        if (data.model) {

            console.log(
                "AI model:",
                data.model
            );
        }

    }

    catch (error) {

        console.error(
            error
        );


        answerBox.textContent =
            "❌ Something went wrong.";
    }

    finally {

        isThinking = false;

        askButton.disabled = false;

        questionInput.disabled = false;

        questionInput.focus();
    }
}


// ======================================================
// ENTER
// ======================================================

questionInput.addEventListener(
    "keydown",
    function (event) {

        if (event.key === "Enter") {

            event.preventDefault();

            askAI();
        }
    }
);


// ======================================================
// CAMERA
// ======================================================

cameraButton.addEventListener(
    "click",
    openCamera
);


async function openCamera() {

    try {

        cameraStream =
            await navigator.mediaDevices
                .getUserMedia({

                    video: {

                        facingMode: {
                            ideal: "environment"
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
            error
        );


        alert(
            "Camera could not be opened."
        );
    }
}


// ======================================================
// TAKE PHOTO
// ======================================================

takePhotoButton.addEventListener(
    "click",
    takePhoto
);


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


    selectedImageBase64 =
        cameraCanvas.toDataURL(
            "image/jpeg",
            0.9
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
    function () {

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


        cameraStream = null;
    }


    cameraVideo.srcObject = null;

    cameraVideo.style.display =
        "none";

    cameraControls.style.display =
        "none";
}


// ======================================================
// CLICK IMAGE AREA
// ======================================================

dropZone.addEventListener(
    "click",
    function () {

        if (cameraStream) {
            return;
        }


        imageInput.click();
    }
);


// ======================================================
// FILE PICKER
// ======================================================

imageInput.addEventListener(
    "change",
    function () {

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
// DRAG
// ======================================================

dropZone.addEventListener(
    "dragover",
    function (event) {

        event.preventDefault();

        dropZone.classList.add(
            "dragging"
        );
    }
);


dropZone.addEventListener(
    "dragleave",
    function () {

        dropZone.classList.remove(
            "dragging"
        );
    }
);


// ======================================================
// DROP
// ======================================================

dropZone.addEventListener(
    "drop",
    function (event) {

        event.preventDefault();


        dropZone.classList.remove(
            "dragging"
        );


        const file =
            event.dataTransfer.files[0];


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
        function (event) {

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
        function () {

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
// EMPTY IMAGE AREA
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
    function (event) {

        event.stopPropagation();


        selectedImageBase64 = "";

        imageInput.value = "";


        showPlaceholder();
    }
);