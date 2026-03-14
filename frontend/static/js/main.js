// Предпросмотр стоимости в форме заказа 
function calculatePreview() {
    const weight = parseFloat(document.querySelector('input[name="weight"]').value) || 0;
    const tariffEl = document.querySelector('input[name="tariff"]:checked');
    if (!tariffEl || weight === 0) return;

    const rateText = tariffEl.parentElement.querySelector('small').textContent;
    const rate = parseFloat(rateText.match(/\d+/)[0]);
    const daysText = tariffEl.parentElement.querySelector('strong').nextSibling.textContent;
    const days = parseFloat(daysText.match(/\d+/)[0]);

    const approxCost = Math.round(weight * rate * 1.2);
    document.getElementById('cost').textContent = approxCost;
    document.getElementById('days').textContent = days;
}

// Добавление статуса в админке
function addStatus(orderId) {
    const status = prompt("Новый статус (например: В пути, Доставлен, На складе):");
    const locationText = prompt("Местоположение (город/склад):");
    
    if (!status || !locationText) return;

    fetch('/api/add_status', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            order_id: orderId,
            status: status,
            location: locationText
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
                        window.location.reload();
        } else {
            alert("Ошибка: " + (data.error || "Неизвестная ошибка"));
        }
    })
    .catch(err => {
        console.error("Fetch error:", err);
        alert("Ошибка соединения: " + err.message);
    });
}

// Автоматически запускаем предпросмотр на странице заказа
document.addEventListener('DOMContentLoaded', () => {
    const orderForm = document.getElementById('orderForm');
    if (orderForm) {
        const inputs = orderForm.querySelectorAll('input[name="tariff"], input[name="weight"], select');
        inputs.forEach(input => {
            input.addEventListener('change', calculatePreview);
        });
        calculatePreview();
    }
});