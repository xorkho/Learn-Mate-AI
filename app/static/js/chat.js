const renderer = new marked.Renderer();
renderer.link = (href, title, text) => {
    return `<a href="${href}" target="_blank" rel="noopener noreferrer" class="text-brand-600 underline">${text}</a>`;
};
marked.setOptions({ renderer });

// ---------- Tabs ----------
function switchTab(name) {
    document.querySelectorAll(".tab-btn").forEach(t => {
        t.classList.remove("bg-brand-50", "text-brand-700");
        t.classList.add("text-gray-600");
    });
    document.querySelector(`.tab-btn[data-panel="${name}"]`).classList.add("bg-brand-50", "text-brand-700");
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
        div.className = "bg-brand-600 text-white rounded-lg px-4 py-3 text-sm max-w-[80%] self-end";
        div.textContent = text;   // user ka apna text, plain rakhna hai
    } else {
        div.className = "bg-slate-100 text-slate-700 rounded-lg px-4 py-3 text-sm max-w-[80%] prose prose-sm max-w-none";
        div.innerHTML = marked.parse(text);   // ← markdown render karo
    }

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
    chatLog.insertAdjacentHTML("beforeend", `<div class="bg-slate-100 text-slate-500 rounded-lg px-4 py-3 text-sm max-w-[80%]" id="${loadingId}">Thinking...</div>`);
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
        output.innerHTML = marked.parse(data.summary);
    } catch (e) {
        output.innerHTML = `<p class="text-red-600">${e.message}</p>`;
    } finally {
        btn.disabled = false;
    }
}

// ---------- Quiz ----------
let currentQuizData = [];   // taake submit ke waqt correct answers/topics yaad rahein

async function generateQuiz() {
    const btn = document.getElementById("quizBtn");
    const output = document.getElementById("quizOutput");
    const results = document.getElementById("quizResults");
    const numQuestions = parseInt(document.getElementById("numQuestions").value) || 5;
    const difficulty = document.getElementById("quizDifficulty").value;

    results.classList.add("hidden");
    btn.disabled = true;
    output.innerHTML = `<p class="text-gray-500">Generating ${numQuestions} ${difficulty} questions...</p>`;

    try {
        const res = await fetch("/chat/quiz", {
            method: "POST",
            headers: { ...authHeaders(), "Content-Type": "application/json" },
            body: JSON.stringify({ document_id: documentId, num_questions: numQuestions, difficulty }),
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Could not generate quiz");
        }

        const data = await res.json();
        currentQuizData = data.questions;
        renderQuiz(currentQuizData, difficulty);
    } catch (e) {
        output.innerHTML = `<p class="text-red-600">${e.message}</p>`;
    } finally {
        btn.disabled = false;
    }
}

function renderQuiz(questions, difficulty) {
    const output = document.getElementById("quizOutput");
    output.innerHTML = questions.map((q, qi) => `
        <div class="quiz-question mb-5 pb-5 border-b border-gray-100" data-qi="${qi}">
            <div class="font-medium text-gray-800 mb-2 text-sm">${qi + 1}. ${q.question}
                <span class="text-xs text-gray-400 font-normal">(${q.topic})</span>
            </div>
            <div class="flex flex-col gap-2">
                ${q.options.map(opt => `
                    <div class="quiz-option border border-gray-200 rounded-md px-3 py-2 text-sm cursor-pointer hover:border-brand-400 transition"
                         onclick="selectOption(${qi}, this)">${opt}</div>
                `).join("")}
            </div>
        </div>
    `).join("") + `
        <button onclick="submitQuiz('${difficulty}')"
                class="bg-brand-600 hover:bg-brand-700 text-white text-sm font-medium px-4 py-2 rounded-md transition mt-2">
            Submit Quiz
        </button>
    `;
}

function selectOption(qi, el) {
    const question = document.querySelector(`.quiz-question[data-qi="${qi}"]`);
    question.querySelectorAll(".quiz-option").forEach(o => {
        o.classList.remove("border-brand-500", "bg-brand-50");
    });
    el.classList.add("border-brand-500", "bg-brand-50");
}

async function submitQuiz(difficulty) {
    const questionEls = document.querySelectorAll(".quiz-question");
    const answers = [];

    questionEls.forEach((qEl, i) => {
        const selected = qEl.querySelector(".border-brand-500");
        answers.push({
            question: currentQuizData[i].question,
            topic: currentQuizData[i].topic,
            selected_answer: selected ? selected.textContent.trim() : "",
            correct_answer: currentQuizData[i].correct_answer,
        });
    });

    try {
        const res = await fetch("/chat/quiz/submit", {
            method: "POST",
            headers: { ...authHeaders(), "Content-Type": "application/json" },
            body: JSON.stringify({ document_id: documentId, difficulty, answers }),
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Could not submit quiz");
        }

        const data = await res.json();
        showQuizResults(data);
    } catch (e) {
        alert(e.message);
    }
}

function showQuizResults(data) {
    document.getElementById("quizOutput").innerHTML = "";
    const results = document.getElementById("quizResults");
    results.classList.remove("hidden");

    results.innerHTML = `
        <div class="text-center mb-4">
            <p class="text-3xl font-bold text-brand-600">${data.score_percentage}%</p>
            <p class="text-gray-500 text-sm">${data.correct_answers} / ${data.total_questions} correct</p>
        </div>
        <div style="max-width: 360px; margin: 0 auto;">
            <canvas id="topicChart"></canvas>
        </div>
    `;

    const topics = Object.keys(data.topic_breakdown);
    const correctData = topics.map(t => data.topic_breakdown[t].correct);
    const totalData = topics.map(t => data.topic_breakdown[t].total);
    const percentages = topics.map((t, i) => Math.round((correctData[i] / totalData[i]) * 100));

    const ctx = document.getElementById("topicChart").getContext("2d");
    new Chart(ctx, {
        type: "pie",
        data: {
            labels: topics.map((t, i) => `${t} (${correctData[i]}/${totalData[i]})`),
            datasets: [{
                data: percentages,
                backgroundColor: [
                    "#5546db", "#10B981", "#F59E0B", "#EF4444",
                    "#8B5CF6", "#EC4899", "#14B8A6", "#F97316"
                ],
            }],
        },
        options: {
            plugins: {
                legend: { position: "bottom", labels: { font: { size: 11 } } },
            },
        },
    });
}