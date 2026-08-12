const askButton = document.getElementById("askButton");
const questionInput = document.getElementById("question");
const answerBox = document.getElementById("answer");

// Replace this with your ngrok URL if it changes
const API_URL = "https://reclusive-undertow-unlit.ngrok-free.dev/ask";

askButton.addEventListener("click", askAI);

async function askAI() {

    const question = questionInput.value.trim();

    if (question === "") {
        answerBox.innerHTML = "⚠️ Please enter a question.";
        return;
    }

    answerBox.innerHTML = "🧠 Thinking...";

    try {

        const response = await fetch(API_URL, {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                question: question
            })

        });

        const data = await response.json();

        if (data.answer) {
            answerBox.innerHTML = data.answer;
        } else {
            answerBox.innerHTML = "⚠️ No answer received.";
        }

    }
    catch (error) {

        console.error(error);

        answerBox.innerHTML =
            "❌ Unable to connect to AI server.";

    }

}