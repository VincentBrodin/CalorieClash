

function main(){
    let button = document.getElementById("add-new");
    button.addEventListener("click", add_new)
}

function add_new(){
    console.log("Adding new")
}

document.addEventListener("DOMContentLoaded", main);
