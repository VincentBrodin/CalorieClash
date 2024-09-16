

function main() {
    const listItems = document.querySelectorAll('#product_list li');

    listItems.forEach((item) => {
        const numberInput = item.querySelector('input[type="number"]');
        if (numberInput) {
            numberInput.addEventListener("input", () => {
                console.log(item.id + " / " + numberInput.value)
                if(numberInput.value == ""){
                    numberInput.value = "0";
                }
                fetch("/update_list_count", {
                    method: 'POST',
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        "count": numberInput.value,
                        "list_id": list_id,
                        "product_id": item.id
                    })
                })
                    .then((response) => {
                        console.log(response)
                        if (parseInt(numberInput.value) <= 0) {
                            item.remove();
                        }
                    })
            });
        }
    });
}
document.addEventListener("DOMContentLoaded", main);
