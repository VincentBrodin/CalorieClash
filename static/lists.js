
let name_field;
let save_name;
let start_value = "";

function main(){
    name_field = document.getElementById("name_field");
    name_field.addEventListener("input", name_field_update)
    start_value = name_field.value;
    save_name = document.getElementById("save_name");
    save_name.style.display = "None";
}

function add_new(){
    console.log(new_product_id.value);
    new_product_id.value = "";
    let newProduct = createElement();
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
