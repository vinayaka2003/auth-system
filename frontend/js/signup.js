async function signup() {

    const btn =
        document.getElementById("signupBtn");

    btn.disabled = true;
    btn.innerText = "Signing up...";

    try {

        const data = {
            name:
                document.getElementById("name").value,

            email:
                document.getElementById("email").value,

            password:
                document.getElementById("password").value
        };

        const response = await fetch(
            "http://127.0.0.1:8000/signup",
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

        if (response.ok) {

            alert(
                "Account created. Check your email for verification."
            );

            window.location.href =
                "login.html";

        } else {

            alert(
                result.detail ||
                "Signup failed"
            );
        }

    } catch (error) {

        alert(
            "Server error. Please try again."
        );

    } finally {

        btn.disabled = false;
        btn.innerText = "Signup";
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


/* GOOGLE SIGNUP */

async function handleGoogleSignup(
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
                "Google signup failed"
            );
        }

    } catch (error) {

        alert(
            "Google signup failed"
        );
    }
}