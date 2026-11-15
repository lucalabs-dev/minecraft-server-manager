const pathParts = window.location.pathname.split("/");
const serverId = pathParts[2];

function getPropertyFields() {
    return document.querySelectorAll(
        ".property-group input[id], .property-group select[id]"
    );
}


async function loadProperties() {
    if (!serverId) {
        document.getElementById("save-message").textContent =
            "Server ID is missing!";
        return;
    }

    try {
        const response = await fetch(
            `/api/servers/${encodeURIComponent(serverId)}/properties`
        );

        if (!response.ok) {
            throw new Error("Could not load properties.");
        }

        const properties = await response.json();

        getPropertyFields().forEach(input => {
            const property = input.id;

            if (properties[property] !== undefined) {
                input.value = properties[property];
            }
        });

    } catch (error) {
        document.getElementById("save-message").textContent =
            error.message;
    }
}


async function saveProperties() {
    if (!serverId) {
        document.getElementById("save-message").textContent =
            "Server ID is missing!";
        return;
    }

    const newProperties = {};

    getPropertyFields().forEach(input => {
        newProperties[input.id] = input.value;
    });

    try {
        const response = await fetch(
            `/api/servers/${encodeURIComponent(serverId)}/properties`,
            {
                method: "PATCH",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    property: newProperties
                })
            }
        );

        if (!response.ok) {
            const error = await response.text();
            console.error("Status:", response.status);
            console.error("Backend response:", error);

            throw new Error("Could not save properties.");
        }

        document.getElementById("save-message").textContent =
            "Properties saved successfully!";

    } catch (error) {
        document.getElementById("save-message").textContent =
            error.message;
    }
}


document.getElementById("save-properties").addEventListener(
    "click",
    saveProperties
);


loadProperties();