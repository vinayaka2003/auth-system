async function verifyEmail() {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");
    const statusMsg = document.getElementById("statusMessage");

    if (!token) {
        statusMsg.innerText = "Error: Verification token is missing.";
        statusMsg.style.color = "red";
        return;
    }

    try {
        const response = await fetch(`http://127.0.0.1:8000/verify/${token}`);
        const result = await response.json();

        if (response.ok) {
            statusMsg.innerText = "Success! Your email has been verified.";
            statusMsg.style.color = "green";
        } else {
            statusMsg.innerText = result.detail || "Verification failed.";
            statusMsg.style.color = "red";
        }
    } catch (error) {
        statusMsg.innerText = "Server error. Please try again later.";
        statusMsg.style.color = "red";
    }
}

window.onload = verifyEmail;
