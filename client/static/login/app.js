const loginButton = document.getElementById("loginButton");
const usernameField = document.getElementById("usernameField");
const passwordField = document.getElementById("passwordField");


loginButton.addEventListener("click", login);
usernameField.addEventListener("keyup", (event) => {
    if (event.keyCode === 13) {
        loginButton.click();
    }
});
passwordField.addEventListener("keyup", (event) => {
    if (event.keyCode === 13) {
        loginButton.click();
    }
});


function login() {
    const username = usernameField.value;
    const password = passwordField.value;

    sendRequest("/api/auth/", {
        username: username,
        password: password,
    })
        .then(function (response) {
            if (response.data == "auth:true") location.reload();
            else console.log("wrong credentials");
        })
        .catch(function (error) {
            console.log("an error occured");
            console.log(error);
        });
}
