const serverId = window.location.pathname.split("/").pop();

const startButton = document.getElementById("start-button");
const stopButton = document.getElementById("stop-button");
const restartButton = document.getElementById("restart-button");
const consoleOutput = document.getElementById("console-output");
const errorMessage = document.getElementById("error-message");

const commandInput = document.getElementById("command-input");
const sendCommandButton = document.getElementById("send-command-button");
const commandError = document.getElementById("command-error");

const logStream = new EventSource(
    "/api/servers/" + serverId + "/logs"
);

async function apiFetch(url, options = {}, fallback = "Request failed") {
    const response = await fetch(url, options);

    const data = await response.json().catch(() => null);

    if (!response.ok) {
        throw new Error(data?.detail || fallback);
    }

    return data;
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.style.display = "block";
}

function clearError() {
    errorMessage.textContent = "";
    errorMessage.style.display = "none";
}

logStream.onmessage = function (event) {
    const wasAtBottom =
        consoleOutput.scrollHeight -
        consoleOutput.scrollTop -
        consoleOutput.clientHeight < 30;

    if (
        consoleOutput.textContent === "Warte auf Serverausgabe..." ||
        consoleOutput.textContent === "Noch keine Serverausgabe vorhanden."
    ) {
        consoleOutput.textContent = "";
    }

    consoleOutput.textContent += event.data + "\n";

    if (wasAtBottom) {
        consoleOutput.scrollTop = consoleOutput.scrollHeight;
    }
};

logStream.onopen = function () {
    console.log("SSE-Verbindung hergestellt.");
};

logStream.onerror = function () {
    console.error(
        "SSE-Verbindung unterbrochen. Verbindung wird erneut versucht."
    );
};

async function loadServer() {
    try {
        const server = await apiFetch(
            "/api/servers/" + serverId,
            {},
            "Failed to load server"
        );

        document.getElementById("server-name").textContent =
            server.name;

        document.getElementById("server-version").textContent =
            "Minecraft-Version: " + (server.version || "Unknown");
            
    } catch (error) {
        console.error(error);

        document.getElementById("server-name").textContent =
            "Server not found";

        showError(error.message);
    }
}

async function loadServerStatus() {
    try {
        const data = await apiFetch(
            "/api/servers/" + serverId + "/status",
            {},
            "Failed to load server status"
        );

        document.getElementById("server-status").textContent =
            data.status;

        const isOnline = data.status.toLowerCase() === "online";

        startButton.disabled = isOnline;
        stopButton.disabled = !isOnline;
        restartButton.disabled = !isOnline;

        commandInput.disabled = !isOnline;
        sendCommandButton.disabled = !isOnline;

    } catch (error) {
        console.error(error);
        showError(error.message);
    }
}

async function checkEula() {
    try {
        const eulaAccepted = await apiFetch(
            "/api/servers/" + serverId + "/eula",
            {},
            "Failed to load EULA status"
        );

        document.getElementById("eula-section").style.display =
            eulaAccepted === false ? "block" : "none";

    } catch (error) {
        console.error(error);
        showError(error.message);
    }
}

document
    .getElementById("accept-eula-button")
    .addEventListener("click", async function () {
        clearError();

        try {
            await apiFetch(
                "/api/servers/" + serverId + "/eula",
                { method: "POST" },
                "Failed to accept EULA"
            );

            document.getElementById("eula-section").style.display =
                "none";

        } catch (error) {
            console.error(error);
            showError(error.message);
        }
    });

startButton.addEventListener("click", async function () {
    clearError();

    startButton.disabled = true;
    stopButton.disabled = true;
    restartButton.disabled = true;

    try {
        const data = await apiFetch(
            "/api/servers/" + serverId + "/start",
            { method: "POST" },
            "Failed to start server"
        );

        console.log(data);

    } catch (error) {
        console.error(error);
        showError(error.message);

    } finally {
        await loadServerStatus();
    }
});

stopButton.addEventListener("click", async function () {
    clearError();

    startButton.disabled = true;
    stopButton.disabled = true;
    restartButton.disabled = true;

    try {
        const data = await apiFetch(
            "/api/servers/" + serverId + "/stop",
            { method: "POST" },
            "Failed to stop server"
        );

        console.log(data);

    } catch (error) {
        console.error(error);
        showError(error.message);

    } finally {
        await loadServerStatus();
    }
});

restartButton.addEventListener("click", async function () {
    clearError();

    startButton.disabled = true;
    stopButton.disabled = true;
    restartButton.disabled = true;

    try {
        const data = await apiFetch(
            "/api/servers/" + serverId + "/restart",
            { method: "POST" },
            "Failed to restart server"
        );

        console.log(data);

    } catch (error) {
        console.error(error);
        showError(error.message);

    } finally {
        await loadServerStatus();
    }
});

async function sendCommand() {
    const command = commandInput.value.trim();

    commandError.textContent = "";

    if (!command) {
        return;
    }

    sendCommandButton.disabled = true;

    try {
        await apiFetch(
            "/api/servers/" + serverId + "/command",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    command: command
                })
            },
            "Failed to send command"
        );

        commandInput.value = "";

    } catch (error) {
        console.error(error);
        commandError.textContent = error.message;

    } finally {
        await loadServerStatus();
        commandInput.focus();
    }
}

sendCommandButton.addEventListener("click", sendCommand);

commandInput.addEventListener("keydown", function (event) {
    if (event.key === "Enter") {
        sendCommand();
    }
});

loadServer();
loadServerStatus();
checkEula();

setInterval(loadServerStatus, 10000);