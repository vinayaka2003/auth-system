async function login() {

    const btn =
        document.getElementById("loginBtn");

    const container =
        document.querySelector(".container");

    btn.disabled = true;
    btn.innerText = "Logging in...";

    container.classList.add("loading");

    try {

        const data = {
            email:
                document.getElementById("email").value,

            password:
                document.getElementById("password").value
        };

        const response = await fetch(
            "http://127.0.0.1:8000/login",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify(data)
            }
        );

        const result =
            await response.json();

        if (result.access_token) {

            localStorage.setItem(
                "token",
                result.access_token
            );

            window.location.href =
                "dashboard.html";

        } else {

            alert(
                result.detail ||
                "Something went wrong"
            );
        }

    } catch (error) {

        alert(
            "Server error. Please try again."
        );

    } finally {

        container.classList.remove(
            "loading"
        );

        btn.disabled = false;

        btn.innerText = "Login";
    }
}


/* PASSWORD TOGGLE */

function togglePassword() {

    const passwordInput =
        document.getElementById(
            "password"
        );

    const eyeIcon =
        document.getElementById(
            "eyeIcon"
        );

    if (
        passwordInput.type ===
        "password"
    ) {

        passwordInput.type =
            "text";

        eyeIcon.setAttribute(
            "data-lucide",
            "eye-off"
        );

    } else {

        passwordInput.type =
            "password";

        eyeIcon.setAttribute(
            "data-lucide",
            "eye"
        );
    }

    lucide.createIcons();
}


/* GOOGLE LOGIN */

async function handleGoogleLogin(
    response
) {

    const googleToken =
        response.credential;

    try {

        const backendResponse =
            await fetch(
                "http://127.0.0.1:8000/google-login",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        token:
                            googleToken
                    })
                }
            );

        const result =
            await backendResponse.json();

        if (result.access_token) {

            localStorage.setItem(
                "token",
                result.access_token
            );

            window.location.href =
                "dashboard.html";

        } else {

            alert(
                result.detail ||
                "Google login failed"
            );
        }

    } catch (error) {

        alert(
            "Google login failed"
        );
    }
}


/* GUEST LOGIN */

function guestLogin() {

    localStorage.removeItem(
        "token"
    );

    localStorage.setItem(
        "guest",
        "true"
    );

    window.location.href =
        "dashboard.html";
}