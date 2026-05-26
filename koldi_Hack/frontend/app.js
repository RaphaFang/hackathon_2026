// const API = "http://127.0.0.1:8000";

// /* -------------------- LOAD KPI -------------------- */

// async function loadOverview(){

//     const r =
//         await fetch(API + "/overview");

//     const data =
//         await r.json();

//     document.getElementById("movement").innerText =
//         Math.round(data.movement).toLocaleString();

//     document.getElementById("events").innerText =
//         data.events;

//     document.getElementById("stay").innerText =
//         data.avg_stay.toFixed(1) + " min";
// }

// /* -------------------- MOVEMENT CHART -------------------- */

// async function loadMovement(){

//     const r =
//         await fetch(API + "/movement");

//     const data =
//         await r.json();

//     const x =
//         data.map(d => d.timestamp);

//     const y =
//         data.map(d => d.amount);

//     Plotly.newPlot(
//         "movementChart",
//         [{
//             x,
//             y,
//             type:"scatter",
//             mode:"lines",
//             line:{
//                 color:"#17324d",
//                 width:3
//             }
//         }],
//         {
//             margin:{t:20},
//             paper_bgcolor:"white",
//             plot_bgcolor:"white"
//         }
//     );
// }

// /* -------------------- STAY CHART -------------------- */

// async function loadStay(){

//     const r =
//         await fetch(API + "/stay");

//     const data =
//         await r.json();

//     const y =
//         data.map(d => d.sensor);

//     const x =
//         data.map(d => d.avg_stay_min);

//     Plotly.newPlot(
//         "stayChart",
//         [{
//             x,
//             y,
//             type:"bar",
//             orientation:"h",
//             marker:{
//                 color:"#17324d"
//             }
//         }],
//         {
//             margin:{t:20},
//             paper_bgcolor:"white",
//             plot_bgcolor:"white"
//         }
//     );
// }

// /* -------------------- CHAT POPUP -------------------- */

// window.onload = function(){

//     loadOverview();
//     loadMovement();
//     loadStay();

//     const popup =
//         document.getElementById("chat-popup");

//     const toggle =
//         document.getElementById("chat-toggle");

//     toggle.onclick = function(){

//         if(
//             popup.style.display === "flex"
//         ){
//             popup.style.display =
//                 "none";
//         }
//         else{
//             popup.style.display =
//                 "flex";
//         }
//     };

//     const textarea =
//         document.getElementById("question");

//     textarea.addEventListener(
//         "input",
//         function(){
//             this.style.height = "auto";
//             this.style.height =
//                 Math.min(this.scrollHeight, 140) + "px";
//         }
//     );

//     textarea.addEventListener(
//         "keydown",
//         function(e){
//             if(e.key === "Enter" && !e.shiftKey){
//                 e.preventDefault();
//                 askAI();
//             }
//         }
//     );
// };

// /* -------------------- AI CHAT -------------------- */

// async function askAI(){

//     const questionEl =
//         document.getElementById("question");

//     const question =
//         questionEl.value.trim();

//     if(!question) return;

//     const chat =
//         document.getElementById("chat-messages");

//     /* USER MESSAGE */

//     const userBubble =
//         document.createElement("div");

//     userBubble.className = "user-msg";
//     userBubble.textContent = question;
//     chat.appendChild(userBubble);

//     /* THINKING */

//     const thinkingBubble =
//         document.createElement("div");

//     thinkingBubble.className = "ai-msg";
//     thinkingBubble.id = "thinking";
//     thinkingBubble.textContent = "🤖 Thinking...";
//     chat.appendChild(thinkingBubble);

//     chat.scrollTop =
//         chat.scrollHeight;

//     try{

//         const r =
//             await fetch(
//                 API + "/ask",
//                 {
//                     method:"POST",
//                     headers:{
//                         "Content-Type":
//                         "application/json"
//                     },
//                     body:JSON.stringify({
//                         question
//                     })
//                 }
//             );

//         const data =
//             await r.json();

//         document
//             .getElementById("thinking")
//             .remove();

//         /* AI ANSWER */

//         const aiBubble =
//             document.createElement("div");

//         aiBubble.className = "ai-msg";
//         aiBubble.textContent = "🤖 " + data.answer;
//         chat.appendChild(aiBubble);

//         chat.scrollTop =
//             chat.scrollHeight;

//         questionEl.value = "";
//         questionEl.style.height = "auto";

//     }
//     catch(error){

//         console.error(error);

//         document
//             .getElementById("thinking")
//             .textContent =
//             "⚠️ AI service unavailable.";
//     }
// }



const API = "http://127.0.0.1:8000";

/* =====================================================
LOAD DASHBOARD
===================================================== */

window.onload = function(){

    loadOverview();
    loadMovement();
    loadStay();
    loadInsight();

    initialiseChat();
};


/* =====================================================
OVERVIEW KPI
===================================================== */

async function loadOverview(){

    try{

        const r =
            await fetch(
                API + "/overview"
            );

        const data =
            await r.json();

        document.getElementById(
            "movement"
        ).innerText =
            Math.round(
                data.movement
            ).toLocaleString();

        document.getElementById(
            "events"
        ).innerText =
            data.events;

        document.getElementById(
            "stay"
        ).innerText =
            data.avg_stay.toFixed(1)
            + " min";

    }
    catch(error){
        console.error(
            error
        );
    }
}


/* =====================================================
AI INSIGHT CARD
===================================================== */

async function loadInsight(){

    try{

        const r =
            await fetch(
                API + "/insight"
            );

        const data =
            await r.json();

        document.getElementById(
            "insight"
        ).innerText =
            data.insight;

    }
    catch(error){

        console.error(
            error
        );

        document.getElementById(
            "insight"
        ).innerText =
            "AI insight unavailable.";
    }
}


/* =====================================================
MOVEMENT CHART
===================================================== */

async function loadMovement(){

    try{

        const r =
            await fetch(
                API + "/movement"
            );

        const data =
            await r.json();

        const x =
            data.map(
                d => d.timestamp
            );

        const y =
            data.map(
                d => d.amount
            );

        Plotly.newPlot(
            "movementChart",
            [
                {
                    x,
                    y,
                    type:"scatter",
                    mode:"lines",
                    line:{
                        color:"#17324d",
                        width:3
                    },
                    fill:"tozeroy"
                }
            ],
            {
                margin:{
                    t:20
                },
                paper_bgcolor:
                    "white",
                plot_bgcolor:
                    "white",
                xaxis:{
                    showgrid:false
                },
                yaxis:{
                    gridcolor:
                    "#e5e7eb"
                }
            }
        );

    }
    catch(error){
        console.error(error);
    }
}


/* =====================================================
STAY CHART
===================================================== */

async function loadStay(){

    try{

        const r =
            await fetch(
                API + "/stay"
            );

        const data =
            await r.json();

        const y =
            data.map(
                d => d.sensor
            );

        const x =
            data.map(
                d => d.avg_stay_min
            );

        Plotly.newPlot(
            "stayChart",
            [
                {
                    x,
                    y,
                    type:"bar",
                    orientation:"h",
                    marker:{
                        color:"#17324d"
                    }
                }
            ],
            {
                margin:{
                    t:20
                },
                paper_bgcolor:
                    "white",
                plot_bgcolor:
                    "white"
            }
        );

    }
    catch(error){
        console.error(error);
    }
}


/* =====================================================
CHAT INITIALISE
===================================================== */

function initialiseChat(){

    const popup =
        document.getElementById(
            "chat-popup"
        );

    const toggle =
        document.getElementById(
            "chat-toggle"
        );

    const textarea =
        document.getElementById(
            "question"
        );

    toggle.onclick =
        function(){

        if(
            popup.style.display
            === "flex"
        ){

            popup.style.display =
                "none";

        }
        else{

            popup.style.display =
                "flex";

            textarea.focus();
        }
    };

    textarea.addEventListener(
        "input",
        function(){

            this.style.height =
                "auto";

            this.style.height =
                Math.min(
                    this.scrollHeight,
                    120
                ) + "px";
        }
    );

    textarea.addEventListener(
        "keydown",
        function(e){

            if(
                e.key === "Enter"
                &&
                !e.shiftKey
            ){

                e.preventDefault();

                askAI();
            }
        }
    );

    setTimeout(
        function(){

            toggle.classList.add(
                "pulse"
            );

        },
        1500
    );

    setTimeout(
        function(){

            toggle.classList.remove(
                "pulse"
            );

        },
        7000
    );
}


/* =====================================================
QUICK ASK BUTTONS
===================================================== */

function quickAsk(btn){

    document.getElementById(
        "question"
    ).value =
        btn.innerText;

    askAI();
}


/* =====================================================
CHAT MESSAGE HELPER
===================================================== */

function addMessage(
    text,
    type
){

    const chat =
        document.getElementById(
            "chat-messages"
        );

    const bubble =
        document.createElement(
            "div"
        );

    bubble.className =
        type === "user"
        ? "user-msg"
        : "ai-msg";

    bubble.textContent =
        text;

    chat.appendChild(
        bubble
    );

    chat.scrollTo({
        top:
        chat.scrollHeight,
        behavior:
        "smooth"
    });
}


/* =====================================================
TYPING INDICATOR
===================================================== */

function showTyping(){

    const chat =
        document.getElementById(
            "chat-messages"
        );

    const typing =
        document.createElement(
            "div"
        );

    typing.className =
        "typing-indicator";

    typing.id =
        "typing";

    typing.innerHTML =
    `
    <span></span>
    <span></span>
    <span></span>
    `;

    chat.appendChild(
        typing
    );

    chat.scrollTo({
        top:
        chat.scrollHeight,
        behavior:
        "smooth"
    });
}

function removeTyping(){

    const t =
        document.getElementById(
            "typing"
        );

    if(t){
        t.remove();
    }
}


/* =====================================================
ASK AI
===================================================== */

async function askAI(){

    const questionEl =
        document.getElementById(
            "question"
        );

    const question =
        questionEl.value.trim();

    if(!question)
        return;

    addMessage(
        question,
        "user"
    );

    questionEl.value =
        "";

    questionEl.style.height =
        "auto";

    showTyping();

    try{

        const r =
            await fetch(
                API + "/ask",
                {
                    method:"POST",
                    headers:{
                        "Content-Type":
                        "application/json"
                    },
                    body:
                    JSON.stringify({
                        question
                    })
                }
            );

        const data =
            await r.json();

        removeTyping();

        addMessage(
            data.answer,
            "ai"
        );

    }
    catch(error){

        console.error(
            error
        );

        removeTyping();

        addMessage(
            "AI service unavailable.",
            "ai"
        );
    }
}