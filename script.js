// ======================================================
// AI POCKET SCIENTIST
// script.js
// STEP 0: Convert uploaded image to Base64
// ======================================================


// ------------------------------------------------------
// 1. GET ELEMENTS FROM THE HTML PAGE
// ------------------------------------------------------

const askButton = document.getElementById("askButton");

const questionInput = document.getElementById("question");

const answerBox = document.getElementById("answer");

const imageButton = document.getElementById("imageButton");

const imageInput = document.getElementById("imageInput");

const previewImage = document.getElementById("previewImage");


// ------------------------------------------------------
// 2. BACKEND URL
// ------------------------------------------------------

const API_URL =
    "https://ai-pocket-scientist.onrender.com/ask";


// ------------------------------------------------------
// 3. VARIABLES
// ------------------------------------------------------

// Stops the user from sending many questions
// while the AI is already answering.
let isThinking = false;


// This variable will store the uploaded image
// after it has been converted to Base64.
let selectedImageBase64 = "";


// ------------------------------------------------------
// 4. ASK BUTTON
// ------------------------------------------------------

askButton.addEventListener("click", askAI);


// ------------------------------------------------------
// 5. IMAGE BUTTON
// ------------------------------------------------------

// When the user clicks "Add Image",
// open the hidden file selector.
imageButton.addEventListener("click", function () {

    imageInput.click();

});


// ------------------------------------------------------
// 6. WHEN USER SELECTS AN IMAGE
// ------------------------------------------------------

imageInput.addEventListener("change", function () {

    // Get the first image selected by the user.
    const file = imageInput.files[0];


    // If no file was selected,
    // clear the stored image.
    if (!file) {

        selectedImageBase64 = "";

        previewImage.src = "";

        previewImage.style.display = "none";

        return;
    }


    // Create a FileReader.
    // FileReader allows JavaScript to read a file
    // selected from the user's device.
    const reader = new FileReader();


    // This function runs AFTER
    // FileReader finishes reading the image.
    reader.onload = function (event) {

        // event.target.result contains the image
        // converted into a Base64 Data URL.
        selectedImageBase64 = event.target.result;


        // Show the image on the webpage.
        previewImage.src = selectedImageBase64;

        previewImage.style.display = "block";


        // Testing message in browser console.
        console.log(
            "Image converted to Base64 successfully."
        );


        // Don't print the entire Base64 because
        // it can contain thousands of characters.
        console.log(
            selectedImageBase64.substring(0, 100) + "..."
        );

    };


    // This function runs if reading the image fails.
    reader.onerror = function () {

        console.error(
            "Error converting image to Base64."
        );

        selectedImageBase64 = "";

    };


    // THIS is the command that actually
    // converts the image to Base64.
    reader.readAsDataURL(file);

});


// ------------------------------------------------------
// 7. ASK AI FUNCTION
// ------------------------------------------------------

async function askAI() {

    // If a request is already happening,
    // don't start another one.
    if (isThinking) {
        return;
    }


    // Read what the user typed.
    const question =
        questionInput.value.trim();


    // Check that the question is not empty.
    if (question === "") {

        answerBox.innerHTML =
            "⚠️ Please enter a question.";

        return;
    }


    // Tell the program that a request
    // is now happening.
    isThinking = true;


    // Change answer area while waiting.
    answerBox.innerHTML =
        "🧠 Thinking...";


    // Disable controls temporarily.
    askButton.disabled = true;

    questionInput.disabled = true;


    try {

        // ------------------------------------------------
        // CURRENT TEXT REQUEST
        // ------------------------------------------------
        //
        // For STEP 0 we are NOT sending the image yet.
        //
        // The image is only being converted to Base64
        // and stored in:
        //
        // selectedImageBase64
        //
        // Your existing Flask backend can therefore
        // continue receiving normal JSON.
        // ------------------------------------------------

        const response = await fetch(
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


        // Convert Flask's JSON response
        // into a JavaScript object.
        const data =
            await response.json();


        // Show answer.
        if (data.answer) {

            answerBox.innerHTML =
                data.answer;

        } else {

            answerBox.innerHTML =
                "⚠️ No answer received.";

        }


    } catch (error) {

        // This happens if Render/backend
        // cannot be reached.
        console.error(error);

        answerBox.innerHTML =
            "❌ Unable to connect to AI server.";


    } finally {

        // This ALWAYS runs,
        // whether the request succeeded or failed.

        isThinking = false;

        askButton.disabled = false;

        questionInput.disabled = false;

        questionInput.focus();

    }

}


// ------------------------------------------------------
// 8. PRESS ENTER TO ASK
// ------------------------------------------------------

questionInput.addEventListener(
    "keydown",
    function (event) {

        if (event.key === "Enter") {

            // Prevent default behaviour.
            event.preventDefault();

            // Same as clicking Ask AI.
            askAI();

        }

    }
);