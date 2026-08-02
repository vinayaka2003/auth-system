async function resetPassword() {

    const params =
        new URLSearchParams(window.location.search);

    const token =
        params.get("token");

    const password =
        document.getElementById("password").value;

    const response = await fetch(
        `http://127.0.0.1:8000/reset-password/${token}`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                password: password
            })
        }
    );

    const result = await response.json();

    if (response.ok) {

        alert("Password reset successful");

        window.location.href =
            "login.html";
    }
    else {

        alert(
            result.detail || "Reset failed"
        );
    }
}