const askButton = document.getElementById("askButton");
const questionInput = document.getElementById("question");
const answerBox = document.getElementById("answer");

const API_URL = "https://ai-pocket-scientist.onrender.com/ask";

let isThinking = false;

askButton.addEventListener("click", askAI);

async function askAI() {

    if (isThinking) return;
    isThinking = true;

    const question = questionInput.value.trim();

    if (question === "") {
        answerBox.innerHTML = "⚠️ Please enter a question.";
        isThinking = false;
        return;
    }

    answerBox.innerHTML = "🧠 Thinking...";

    askButton.disabled = true;
    questionInput.disabled = true;

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

    } catch (error) {

        console.error(error);
        answerBox.innerHTML = "❌ Unable to connect to AI server.";

    } finally {

        isThinking = false;
        askButton.disabled = false;
        questionInput.disabled = false;
        questionInput.focus();

    }
}

// Press Enter to ask AI
questionInput.addEventListener("keydown", function(event) {
    if (event.key === "Enter") {
        event.preventDefault();
        askAI();
    }
});