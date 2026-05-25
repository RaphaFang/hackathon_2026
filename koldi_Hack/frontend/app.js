const API = "http://127.0.0.1:8000";

/* -------------------- LOAD KPI -------------------- */

async function loadOverview(){

    const r =
        await fetch(API + "/overview");

    const data =
        await r.json();

    document.getElementById("movement").innerText =
        Math.round(data.movement).toLocaleString();

    document.getElementById("events").innerText =
        data.events;

    document.getElementById("stay").innerText =
        data.avg_stay.toFixed(1) + " min";
}

/* -------------------- MOVEMENT CHART -------------------- */

async function loadMovement(){

    const r =
        await fetch(API + "/movement");

    const data =
        await r.json();

    const x =
        data.map(d => d.timestamp);

    const y =
        data.map(d => d.amount);

    Plotly.newPlot(
        "movementChart",
        [{
            x,
            y,
            type:"scatter",
            mode:"lines",
            line:{
                color:"#17324d",
                width:3
            }
        }],
        {
            margin:{t:20},
            paper_bgcolor:"white",
            plot_bgcolor:"white"
        }
    );
}

/* -------------------- STAY CHART -------------------- */

async function loadStay(){

    const r =
        await fetch(API + "/stay");

    const data =
        await r.json();

    const y =
        data.map(d => d.sensor);

    const x =
        data.map(d => d.avg_stay_min);

    Plotly.newPlot(
        "stayChart",
        [{
            x,
            y,
            type:"bar",
            orientation:"h",
            marker:{
                color:"#17324d"
            }
        }],
        {
            margin:{t:20},
            paper_bgcolor:"white",
            plot_bgcolor:"white"
        }
    );
}

/* -------------------- CHAT POPUP -------------------- */

window.onload = function(){

    loadOverview();
    loadMovement();
    loadStay();

    const popup =
        document.getElementById("chat-popup");

    const toggle =
        document.getElementById("chat-toggle");

    toggle.onclick = function(){

        if(
            popup.style.display === "flex"
        ){
            popup.style.display =
                "none";
        }
        else{
            popup.style.display =
                "flex";
        }
    };
};

/* -------------------- AI CHAT -------------------- */

// async function askAI(){

//     const question =
//         document.getElementById("question").value;

//     if(!question) return;

//     const chat =
//         document.getElementById("chat-messages");

//         chat.innerHTML += `
//             <div class="ai-msg user-msg">
//                 ${question}
//             </div>
//         `;

//     chat.innerHTML += `
//         <div class="ai-msg" id="thinking">
//             🤖 Thinking...
//         </div>
//     `;

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

//         chat.innerHTML += `
//             // <div class="ai-msg">
//             //     <b>AI:</b><br>
//             <div class="ai-msg">
//                 🤖 ${data.answer}
//                 ${data.answer}
//             </div>
//         `;

//         chat.scrollTop =
//             chat.scrollHeight;

//         document
//             .getElementById("question")
//             .value = "";

//     }
//     catch(error){

//         console.error(error);

//         document
//             .getElementById("thinking")
//             .innerHTML =
//             "AI service unavailable.";
//     }
// }

// const textarea =
// document.getElementById("question");

// textarea.addEventListener(
// "input",
// function(){

// this.style.height =
// "auto";

// this.style.height =
// this.scrollHeight + "px";

// });

// textarea.addEventListener(
// "keydown",
// function(e){

// if(
// e.key==="Enter" &&
// !e.shiftKey
// ){
// e.preventDefault();
// askAI();
// }

// });



/* -------------------- AI CHAT -------------------- */

async function askAI(){

    const question =
        document.getElementById("question").value.trim();

    if(!question) return;

    const chat =
        document.getElementById("chat-messages");

    /* USER MESSAGE */

    chat.innerHTML += `
        <div class="user-msg">
            ${question}
        </div>
    `;

    /* THINKING */

    chat.innerHTML += `
        <div class="ai-msg" id="thinking">
            🤖 Thinking...
        </div>
    `;

    chat.scrollTop =
        chat.scrollHeight;

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
                    body:JSON.stringify({
                        question
                    })
                }
            );

        const data =
            await r.json();

        document
            .getElementById("thinking")
            .remove();

        /* AI ANSWER */

        chat.innerHTML += `
            <div class="ai-msg">
                🤖 ${data.answer}
            </div>
        `;

        chat.scrollTop =
            chat.scrollHeight;

        document
            .getElementById("question")
            .value = "";

        textarea.style.height =
            "auto";

    }
    catch(error){

        console.error(error);

        document
            .getElementById("thinking")
            .innerHTML =
            "⚠️ AI service unavailable.";
    }
}