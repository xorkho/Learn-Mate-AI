// ---------- Tabs ----------
function switchTab(name) {
    document.querySelectorAll(".tab-btn").forEach(t => {
        t.classList.remove("bg-blue-50", "text-blue-700");
        t.classList.add("text-gray-600");
    });
    document.querySelector(`.tab-btn[data-panel="${name}"]`).classList.add("bg-blue-50", "text-blue-700");
    document.querySelector(`.tab-btn[data-panel="${name}"]`).classList.remove("text-gray-600");

    document.querySelectorAll(".panel").forEach(p => p.classList.add("hidden"));
    document.getElementById(`panel-${name}`).classList.remove("hidden");
}
document.getElementById("panel-chat").classList.remove("hidden");

// ---------- Load document info ----------
async function loadDocInfo() {
    try {
        const res = await fetch("/documents", { headers: authHeaders() });
        const docs = await res.json();
        const doc = docs.find(d => d.id === documentId);
        if (doc) {
            document.getElementById("docName").textContent = doc.original_filename;
            document.getElementById("docMeta").textContent = `${(doc.file_size / 1024).toFixed(0)} KB`;
        } else {
            document.getElementById("docName").textContent = "Document not found";
        }
    } catch (e) {
        document.getElementById("docName").textContent = "Error loading document";
    }
}
loadDocInfo();

// ---------- Chat ----------
const chatLog = document.getElementById("chatLog");
const chatInput = document.getElementById("chatInput");
const sendBtn = document.getElementById("sendBtn");

chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendMessage();
});

function appendMessage(role, text, sources = null) {
    const div = document.createElement("div");
    if (role === "user") {
        div.className = "bg-blue-600 text-white rounded-lg px-4 py-3 text-sm max-w-[80%] self-end";
    } else {
        div.className = "bg-gray-100 text-gray-700 rounded-lg px-4 py-3 text-sm max-w-[80%]";
    }
    div.innerHTML = text;

    if (sources && sources.length) {
        const src = document.createElement("div");
        src.className = "mt-2 pt-2 border-t border-gray-200 text-xs text-gray-400";
        src.textContent = "Source: " + sources[0].slice(0, 140) + (sources[0].length > 140 ? "..." : "");
        div.appendChild(src);
    }

    chatLog.appendChild(div);
    chatLog.scrollTop = chatLog.scrollHeight;
}

// ---------- Load chat history (ab chatLog define ho chuka hai, isliye yahan call karo) ----------
async function loadChatHistory() {
    try {
        const res = await fetch(`/chat/history/${documentId}`, { headers: authHeaders() });
        if (!res.ok) return;

        const data = await res.json();

        if (data.messages.length === 0) return;

        chatLog.innerHTML = "";

        data.messages.forEach(msg => {
            appendMessage(msg.role, msg.message);
        });
    } catch (e) {
        console.error("Could not load chat history:", e);
    }
}
loadChatHistory();

async function sendMessage() {
    const query = chatInput.value.trim();
    if (!query) return;

    appendMessage("user", query);
    chatInput.value = "";
    sendBtn.disabled = true;

    const loadingId = "loading-" + Date.now();
    chatLog.insertAdjacentHTML("beforeend", `<div class="bg-gray-100 text-gray-500 rounded-lg px-4 py-3 text-sm max-w-[80%]" id="${loadingId}">Thinking...</div>`);
    chatLog.scrollTop = chatLog.scrollHeight;

    try {
        const res = await fetch("/chat/ask", {
            method: "POST",
            headers: { ...authHeaders(), "Content-Type": "application/json" },
            body: JSON.stringify({ document_id: documentId, query: query }),
        });

        document.getElementById(loadingId).remove();

        if (!res.ok) {
            const err = await res.json();
            appendMessage("assistant", `<span class="text-red-600">${err.detail || "Something went wrong."}</span>`);
            return;
        }

        const data = await res.json();
        appendMessage("assistant", data.answer, data.sources);
    } catch (e) {
        document.getElementById(loadingId)?.remove();
        appendMessage("assistant", `<span class="text-red-600">Network error: ${e.message}</span>`);
    } finally {
        sendBtn.disabled = false;
    }
}

// ---------- Summary ----------
async function generateSummary() {
    const btn = document.getElementById("summarizeBtn");
    const output = document.getElementById("summaryOutput");
    btn.disabled = true;
    output.innerHTML = `<p class="text-gray-500">Reading the document and writing a summary...</p>`;

    try {
        const res = await fetch("/chat/summary", {
            method: "POST",
            headers: { ...authHeaders(), "Content-Type": "application/json" },
            body: JSON.stringify({ document_id: documentId }),
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Could not generate summary");
        }

        const data = await res.json();
        output.innerHTML = data.summary;
    } catch (e) {
        output.innerHTML = `<p class="text-red-600">${e.message}</p>`;
    } finally {
        btn.disabled = false;
    }
}

// ---------- Quiz ----------
async function generateQuiz() {
    const btn = document.getElementById("quizBtn");
    const output = document.getElementById("quizOutput");
    const numQuestions = parseInt(document.getElementById("numQuestions").value) || 5;

    btn.disabled = true;
    output.innerHTML = `<p class="text-gray-500">Generating ${numQuestions} questions...</p>`;

    try {
        const res = await fetch("/chat/quiz", {
            method: "POST",
            headers: { ...authHeaders(), "Content-Type": "application/json" },
            body: JSON.stringify({ document_id: documentId, num_questions: numQuestions }),
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Could not generate quiz");
        }

        const data = await res.json();
        renderQuiz(data.questions);
    } catch (e) {
        output.innerHTML = `<p class="text-red-600">${e.message}</p>`;
    } finally {
        btn.disabled = false;
    }
}

function renderQuiz(questions) {
    const output = document.getElementById("quizOutput");
    output.innerHTML = questions.map((q, qi) => `
        <div class="quiz-question mb-5 pb-5 border-b border-gray-100" data-qi="${qi}" data-correct="${q.correct_answer}">
            <div class="font-medium text-gray-800 mb-2 text-sm">${qi + 1}. ${q.question}</div>
            <div class="flex flex-col gap-2">
                ${q.options.map(opt => `
                    <div class="quiz-option border border-gray-200 rounded-md px-3 py-2 text-sm cursor-pointer hover:border-blue-400 transition"
                         onclick="selectOption(${qi}, this)">${opt}</div>
                `).join("")}
            </div>
        </div>
    `).join("") + `
        <button onclick="scoreQuiz()"
                class="border border-gray-300 text-gray-700 hover:border-blue-400 hover:text-blue-600 text-sm font-medium px-4 py-2 rounded-md transition mt-2">
            Check Answers
        </button>
        <div id="quizScore" class="mt-3 font-semibold text-gray-800"></div>
    `;
}

function selectOption(qi, el) {
    const question = document.querySelector(`.quiz-question[data-qi="${qi}"]`);
    question.querySelectorAll(".quiz-option").forEach(o => {
        o.classList.remove("border-blue-500", "bg-blue-50");
    });
    el.classList.add("border-blue-500", "bg-blue-50");
}

function scoreQuiz() {
    const questions = document.querySelectorAll(".quiz-question");
    let correct = 0;

    questions.forEach(q => {
        const correctAnswer = q.dataset.correct.trim();
        const selected = q.querySelector(".border-blue-500");
        const options = q.querySelectorAll(".quiz-option");

        let actualCorrectText = correctAnswer;
        if (/^[A-D]$/i.test(correctAnswer)) {
            const index = correctAnswer.toUpperCase().charCodeAt(0) - 65;
            if (options[index]) {
                actualCorrectText = options[index].textContent.trim();
            }
        }

        options.forEach(opt => {
            const isCorrectOption = opt.textContent.trim() === actualCorrectText;
            const isSelected = opt === selected;

            if (isCorrectOption) {
                opt.classList.add("border-green-500", "bg-green-50");
            } else if (isSelected) {
                opt.classList.add("border-red-500", "bg-red-50");
            }
        });

        if (selected && selected.textContent.trim() === actualCorrectText) correct++;
    });

    document.getElementById("quizScore").textContent = `Score: ${correct} / ${questions.length}`;
}