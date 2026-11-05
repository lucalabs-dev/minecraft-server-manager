
const modal = document.getElementById("add-server-modal");
const addServerButton = document.getElementById("add-server-button");
const closeModalButton = document.getElementById("close-modal-button");

const serverChoice = document.getElementById("server-choice");
const newServerForm = document.getElementById("new-server-form");
const existingServerForm = document.getElementById("existing-server-form");

const newServerButton = document.getElementById("new-server-button");
const existingServerButton = document.getElementById("existing-server-button");

const newServerBackButton = document.getElementById("new-server-back-button");
const existingServerBackButton = document.getElementById("existing-server-back-button");

const createServerButton = document.getElementById("create-server-button");
const addExistingServerButton = document.getElementById("add-existing-server-button");
const selectFolderButton = document.getElementById("select-folder-button");

const newServerNameInput = document.getElementById("new-server-name");
const minecraftVersion = document.getElementById("minecraft-version");
const serverList = document.getElementById("server-list");
const messageBox = document.getElementById("server-manager-message");

function showMessage(message, type = "error") {
    messageBox.textContent = message;
    messageBox.className = "server-manager-message " + type;
}

function clearMessage() {
    messageBox.textContent = "";
    messageBox.className = "server-manager-message";
}

async function apiFetch(
    url,
    options = {},
    fallbackMessage = "Request failed"
) {
    const response = await fetch(url, options);

    const data = await response.json().catch(() => null);

    if (!response.ok) {
        throw new Error(
            data?.detail ||
            data?.error ||
            data?.WARNING ||
            fallbackMessage
        );
    }

    return data;
}

function showChoice() {
    serverChoice.style.display = "flex";
    newServerForm.style.display = "none";
    existingServerForm.style.display = "none";
}

addServerButton.addEventListener("click", function () {
    clearMessage();
    modal.style.display = "flex";
    showChoice();
});

closeModalButton.addEventListener("click", function () {
    modal.style.display = "none";
});

modal.addEventListener("click", function (event) {
    if (event.target === modal) {
        modal.style.display = "none";
    }
});

newServerButton.addEventListener("click", function () {
    clearMessage();
    serverChoice.style.display = "none";
    newServerForm.style.display = "flex";
});

existingServerButton.addEventListener("click", function () {
    clearMessage();
    serverChoice.style.display = "none";
    existingServerForm.style.display = "flex";
});

newServerBackButton.addEventListener("click", showChoice);
existingServerBackButton.addEventListener("click", showChoice);

minecraftVersion.addEventListener("focus", loadVersions);
minecraftVersion.addEventListener("click", loadVersions);

async function loadVersions() {
    if (minecraftVersion.dataset.loaded === "true") {
        return;
    }

    try {
        minecraftVersion.disabled = true;

        const versions = await apiFetch(
            "/api/versions",
            {},
            "Minecraft versions could not be loaded."
        );

        minecraftVersion.replaceChildren();

        const placeholder = document.createElement("option");
        placeholder.value = "";
        placeholder.textContent = "Select version";
        placeholder.disabled = true;
        placeholder.selected = true;

        minecraftVersion.appendChild(placeholder);

        versions.forEach(function (version) {
            const option = document.createElement("option");
            option.value = version;
            option.textContent = version;

            minecraftVersion.appendChild(option);
        });

        minecraftVersion.dataset.loaded = "true";

    } catch (error) {
        console.error(error);

        showMessage(
            error.message || "Minecraft versions could not be loaded."
        );

    } finally {
        minecraftVersion.disabled = false;
    }
}

createServerButton.addEventListener("click", async function () {
    clearMessage();

    const serverName = newServerNameInput.value.trim();
    const version = minecraftVersion.value;

    if (!serverName) {
        showMessage("Server name cannot be empty.");
        newServerNameInput.focus();
        return;
    }

    if (serverName.length > 32) {
        showMessage("Server name must not exceed 32 characters.");
        newServerNameInput.focus();
        return;
    }

    if (!/^[a-zA-Z0-9 _.-]+$/.test(serverName)) {
        showMessage(
            "Server name contains invalid characters. Allowed: letters, numbers, spaces, '.', '_' and '-'."
        );

        newServerNameInput.focus();
        return;
    }

    if (!version) {
        showMessage("Please select a Minecraft version.");
        minecraftVersion.focus();
        return;
    }

    createServerButton.disabled = true;

    const loadingCard = document.createElement("div");
    loadingCard.className = "server-card-loading";

    const spinner = document.createElement("div");
    spinner.className = "loading-spinner";

    const loadingText = document.createElement("div");
    loadingText.textContent = "Creating server: " + serverName;

    loadingCard.appendChild(spinner);
    loadingCard.appendChild(loadingText);
    serverList.appendChild(loadingCard);

    modal.style.display = "none";

    try {
        await apiFetch(
            "/api/servers",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    name: serverName,
                    version: version
                })
            },
            "Server could not be created."
        );

        newServerNameInput.value = "";
        minecraftVersion.selectedIndex = 0;

        await loadServers();

        showMessage("Server created successfully.", "success");

    } catch (error) {
        console.error(error);

        showMessage(
            error.message || "Error creating server."
        );

        modal.style.display = "flex";
        showChoice();
        newServerForm.style.display = "flex";
        serverChoice.style.display = "none";

    } finally {
        createServerButton.disabled = false;
        loadingCard.remove();
    }
});

async function deleteServer(serverId, serverName, button) {
    const confirmed = window.confirm(
        'Do you really want to delete "' + serverName +
        '"?\n\nThe server files will also be deleted. This cannot be undone.'
    );

    if (!confirmed) {
        return;
    }

    clearMessage();

    button.disabled = true;
    button.textContent = "Deleting...";

    try {
        const data = await apiFetch(
            "/api/servers/" + encodeURIComponent(serverId),
            {
                method: "DELETE"
            },
            "Server could not be deleted."
        );

        if (data?.error || data?.WARNING) {
            throw new Error(data.error || data.WARNING);
        }

        await loadServers();

        showMessage(
            'Server "' + serverName + '" was deleted.',
            "success"
        );

    } catch (error) {
        console.error(error);

        showMessage(
            error.message || "Error deleting server."
        );

        button.disabled = false;
        button.textContent = "Delete";
    }
}

async function loadServers() {
    try {
        const servers = await apiFetch(
            "/api/servers",
            {},
            "Failed to load servers."
        );

        serverList.replaceChildren();

        servers.forEach(function (server) {
            const serverCard = document.createElement("div");
            serverCard.className = "server-card";

            const serverLink = document.createElement("a");
            serverLink.className = "server-card-link";
            serverLink.href =
                "/server/" + encodeURIComponent(server.id);

            const serverInfo = document.createElement("div");
            serverInfo.className = "server-info";

            const serverName = document.createElement("h3");
            serverName.textContent = server.name;

            const serverVersion = document.createElement("p");
            serverVersion.className = "server-version";
            serverVersion.textContent =
                "Minecraft " + (server.version || "Unknown");

            const serverStatus = document.createElement("p");
            serverStatus.textContent = "Loading status...";

            const serverArrow = document.createElement("span");
            serverArrow.className = "server-arrow";
            serverArrow.textContent = "→";

            serverInfo.appendChild(serverName);
            serverInfo.appendChild(serverVersion);
            serverInfo.appendChild(serverStatus);

            serverLink.appendChild(serverInfo);
            serverLink.appendChild(serverArrow);

            const actions = document.createElement("div");
            actions.className = "server-card-actions";

            const deleteButton = document.createElement("button");
            deleteButton.type = "button";
            deleteButton.className = "delete-server-button";
            deleteButton.textContent = "Delete";

            deleteButton.addEventListener("click", function () {
                deleteServer(
                    server.id,
                    server.name,
                    deleteButton
                );
            });

            actions.appendChild(deleteButton);

            serverCard.appendChild(serverLink);
            serverCard.appendChild(actions);

            serverList.appendChild(serverCard);

            apiFetch(
                "/api/servers/" +
                encodeURIComponent(server.id) +
                "/status",
                {},
                "Failed to load server status."
            )
                .then(function (data) {
                    const isOnline =
                        String(data.status).toLowerCase() === "online";

                    serverStatus.textContent =
                        isOnline ? "Online" : "Offline";

                    serverStatus.classList.toggle(
                        "status-online",
                        isOnline
                    );

                    serverStatus.classList.toggle(
                        "status-offline",
                        !isOnline
                    );
                })
                .catch(function (error) {
                    console.error(error);

                    serverStatus.textContent =
                        error.message || "Status unavailable";
                });
        });

    } catch (error) {
        console.error(error);

        showMessage(
            error.message || "The server list could not be loaded."
        );
    }
}

selectFolderButton.addEventListener("click", function () {
    alert("Folder selection will be implemented next.");
});

addExistingServerButton.addEventListener("click", function () {
    alert("Adding existing servers will be implemented next.");
});

loadServers();

window.addEventListener("pageshow", function (event) {
    if (event.persisted) {
        loadServers();
    }
});