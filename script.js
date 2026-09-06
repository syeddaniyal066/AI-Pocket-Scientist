// ======================================================
// AI POCKET SCIENTIST
// STEP 0:
// Camera / Upload / Drag & Drop → Base64
// ======================================================


// ------------------------------------------------------
// HTML ELEMENTS
// ------------------------------------------------------

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



// ------------------------------------------------------
// BACKEND
// ------------------------------------------------------

const API_URL =
    "https://ai-pocket-scientist.onrender.com/ask";



// ------------------------------------------------------
// VARIABLES
// ------------------------------------------------------

let isThinking = false;


// This stores the Base64 image.
// Empty string = no image selected.
let selectedImageBase64 = "";


// Stores the live camera connection.
let cameraStream = null;



// ======================================================
// ASK AI
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

        answerBox.innerHTML =
            "⚠️ Please enter a question.";

        return;

    }


    isThinking = true;


    answerBox.innerHTML =
        "🧠 Thinking...";


    askButton.disabled = true;

    questionInput.disabled = true;


    try {

        // IMPORTANT:
        //
        // STEP 0 ONLY
        //
        // We are NOT sending the image yet.
        //
        // selectedImageBase64 contains the image
        // ready for the next step.

        const response =
            await fetch(
                API_URL,
                {

                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        question: question

                    })

                }
            );


        const data =
            await response.json();


        if (data.answer) {

            answerBox.innerHTML =
                data.answer;

        }

        else {

            answerBox.innerHTML =
                "⚠️ No answer received.";

        }

    }

    catch (error) {

        console.error(error);

        answerBox.innerHTML =
            "❌ Unable to connect to AI server.";

    }

    finally {

        isThinking = false;

        askButton.disabled = false;

        questionInput.disabled = false;

        questionInput.focus();

    }

}



// ======================================================
// PRESS ENTER
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

        // Ask browser for camera permission.
        cameraStream =
            await navigator.mediaDevices.getUserMedia({

                video: {

                    facingMode: {
                        ideal: "environment"
                    }

                },

                audio: false

            });


        // Connect live camera to video element.
        cameraVideo.srcObject =
            cameraStream;


        // Hide old image.
        previewImage.style.display =
            "none";


        placeholder.style.display =
            "none";


        removeImageButton.style.display =
            "none";


        // Show camera.
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


    // Match canvas size to camera image.
    cameraCanvas.width =
        cameraVideo.videoWidth;

    cameraCanvas.height =
        cameraVideo.videoHeight;


    const context =
        cameraCanvas.getContext("2d");


    // Draw current camera frame onto canvas.
    context.drawImage(

        cameraVideo,

        0,
        0,

        cameraCanvas.width,
        cameraCanvas.height

    );


    // Convert captured image to Base64.
    selectedImageBase64 =
        cameraCanvas.toDataURL(
            "image/jpeg",
            0.9
        );


    console.log(
        "Camera image converted to Base64 successfully."
    );


    console.log(
        selectedImageBase64.substring(
            0,
            100
        ) + "..."
    );


    // Stop camera.
    stopCamera();


    // Show captured image.
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

        showPlaceholder();

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
                track => track.stop()
            );


        cameraStream = null;

    }


    cameraVideo.srcObject =
        null;


    cameraVideo.style.display =
        "none";


    cameraControls.style.display =
        "none";

}



// ======================================================
// CLICK PREVIEW AREA → FILE PICKER
// ======================================================

dropZone.addEventListener(
    "click",
    function () {

        // Don't open file selector
        // while camera is running.

        if (cameraStream) {
            return;
        }


        imageInput.click();

    }
);



// ======================================================
// NORMAL IMAGE SELECTION
// ======================================================

imageInput.addEventListener(
    "change",
    function () {

        const file =
            imageInput.files[0];


        if (!file) {
            return;
        }


        convertFileToBase64(file);

    }
);



// ======================================================
// DRAG IMAGE OVER DROP ZONE
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



// ======================================================
// DRAG LEAVES AREA
// ======================================================

dropZone.addEventListener(
    "dragleave",
    function () {

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


        convertFileToBase64(file);

    }
);



// ======================================================
// CONVERT FILE TO BASE64
// ======================================================

function convertFileToBase64(file) {

    // Make sure it is actually an image.
    if (!file.type.startsWith("image/")) {

        alert(
            "Please choose an image file."
        );

        return;

    }


    const reader =
        new FileReader();


    reader.onload =
        function (event) {


            // Store complete Base64 image.
            selectedImageBase64 =
                event.target.result;


            console.log(
                "Image converted to Base64 successfully."
            );


            console.log(
                selectedImageBase64.substring(
                    0,
                    100
                ) + "..."
            );


            showImagePreview(
                selectedImageBase64
            );

        };


    reader.onerror =
        function () {

            console.error(
                "Error reading image."
            );


            alert(
                "Could not read this image."
            );

        };


    reader.readAsDataURL(file);

}



// ======================================================
// SHOW IMAGE PREVIEW
// ======================================================

function showImagePreview(base64Image) {

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
// SHOW EMPTY PLACEHOLDER
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
    function () {

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