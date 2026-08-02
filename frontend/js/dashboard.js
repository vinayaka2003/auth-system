const guest =
    localStorage.getItem("guest");

if (guest === "true") {

    document.getElementById("welcome").innerText =
        "Welcome Guest";

    document.getElementById("email").innerText =
        "Guest User";

    document.getElementById("verified").innerText =
        "N/A";

} else {

    loadUser();
}

function logout() {

    localStorage.removeItem("token");
    localStorage.removeItem("guest");

    window.location.href =
        "login.html";
}