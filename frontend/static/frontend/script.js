const apiEndpointInput = document.getElementById("api-endpoint")
const httpMethodInput = document.getElementById("http-method")
const userDataInput = document.getElementById("user-data")
const fileInput = document.getElementById("file-upload-input")
const fileNameElement = document.getElementById("file-name")
const makeRequestButton = document.getElementById("make-request")
const responseDataElement = document.getElementById("response-data")
const cancelFileButton = document.getElementById("cancel-file")

const scheme = apiEndpointInput.dataset.scheme
const host = apiEndpointInput.dataset.host

let accessToken = null

cancelFileButton.style.display = 'none'

// change file upload label text to file name
fileInput.addEventListener("change", () => {

    // show or hide button for file upload cancelation
    if (fileInput.value) {
        cancelFileButton.style.display = 'initial'
    }
    else {
        cancelFileButton.style.display = 'none'
    }

    // show file name. Strip file name if its too long
    let fileName = fileInput.files[0].name
    if (fileName.length > 17) {
        fileName = fileName.slice(0, 14) + "..."
    }
    fileNameElement.innerText = fileName
})

// delete file and hide
cancelFileButton.addEventListener("click", () => {
    fileInput.value = ""
    fileNameElement.innerText = 'File'
    cancelFileButton.style.display = 'none'
})



function buildUrl() {
    let url = `${scheme}://${host}${apiEndpointInput.value}`
    return url
}

function determineContentType() {
    if (fileInput.files.length === 0) {
        return "application/json"
    }
    return null
}

function setRequestBody(method, contentType) {
    // don't search for data when HTTP method is 'GET' or 'DELETE'
    if (method === "GET" || method === "DELETE") return null

    // set request body as form data if file is present
    // otherwise, as JSON string
    let userData = JSON.parse(userDataInput.value)
    if (contentType !== "application/json") {
        let body = new FormData()
        body.append("image", fileInput.files[0])
        for (const key in userData) {
            body.append(key, userData[key])
        }
        return body
    } else {
        return JSON.stringify(userData)
    }
}

async function makeRequest() {
    let url = buildUrl()
    let method = httpMethodInput.value
    let contentType = determineContentType()

    let headers = {
        "Content-Type": contentType,
        "Authorization": accessToken,
    }
    let body = setRequestBody(method, contentType)

    let options = {
        method: method,
        headers: headers,
        body: body,
    }

    // don't send any data when HTTP method is 'GET' or 'DELETE'
    if (method === "GET" || method === "DELETE") {
        delete options.body
    }

    // allow fetch to set 'multipart/form-data'
    if (contentType !== "application/json") {
        delete headers["Content-Type"]
    }

    const request = new Request(url, options)
    const response = await fetch(request)
    const data = await response.json()

    // print results on the page
    // responseDataElement.textContent = JSON.stringify(data, null, 2)
    responseDataElement.textContent = `STATUS CODE: ${response.status}\n\n${JSON.stringify(data, null, 2)}` 

    // set auth header value
    if (url.slice(-6) === "token/") {
        accessToken = `Bearer ${data.access}`
    }
}

makeRequestButton.addEventListener("click", () => {
    makeRequest()
})