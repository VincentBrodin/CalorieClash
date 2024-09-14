
let name_field;
let save_name;
let start_value = "";

function main(){
    //let button = document.getElementById("add-new");
    //button.addEventListener("click", add_new)
    name_field = document.getElementById("name_field");
    name_field.addEventListener("input", name_field_update)
    start_value = name_field.value;
    save_name = document.getElementById("save_name");
    save_name.style.display = "None";
}

function add_new(){
    console.log("Adding new")
}

function name_field_update(){
    if(name_field.value != start_value){
        save_name.style.display = "Block";
    }
    else{
        save_name.style.display = "None";
    }
}

document.addEventListener("DOMContentLoaded", main);
