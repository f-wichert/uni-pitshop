// from Django docs
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === name + "=") {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}


function sendRequest(url, data, config = undefined) {
    const csrftoken = getCookie("csrftoken");

    return axios({
        method: "post",
        url: url,
        xstfCookieName: "csrftoken",
        xsrfHeaderName: "X-CSRFToken",
        data: data,
        headers: {
            "X-CSRFToken": csrftoken,
        },
        ...config,
    });
}
