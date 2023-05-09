// 成功提醒
function msg_ok(message, callback) {
    layer.msg(message, {icon: 1, time: 1500}, callback)
}

// 失败提醒
function msg_fail(message, callback) {
    layer.msg(message, {icon: 2, time: 1500}, callback)
}

function closeWin() {
    if (navigator.userAgent.indexOf("Firefox") != -1 || navigator.userAgent.indexOf("Chrome") != -1) {
        window.location.href = "about:blank";
        window.close();
    } else {
        window.opener = null;
        window.open("", "_self");
        window.close();
    }
}

// 在接口请求的同时  在每个接口之前加上tbkt_token  用于跨域
var Token = localStorage.getItem('Token');
$.ajaxSetup({
    beforeSend: function (xhr) {
        xhr.setRequestHeader('token', Token)
    },
    complete: function (xhr, status) {
        // if(xhr.responseJSON.response == 'ok' && xhr.responseJSON.error == 'token失效') {
        //     localStorage.removeItem('Tbkt-Token')
        //     location.href = '/login'
        // }
    }
});

