document.addEventListener("DOMContentLoaded", function () {
    // 🔁 Calcula precio y subtotal al cambiar producto o cantidad
    function updateCalculations(row) {
        const select = row.querySelector('.producto-select');
        const priceInput = row.querySelector('.precio-unitario');
        const quantityInput = row.querySelector('.cantidad-input');
        const subtotalInput = row.querySelector('.subtotal');

        // Obtiene precio desde atributo data-precio del producto seleccionado
        const price = parseFloat(select.selectedOptions[0]?.dataset.precio) || 0;
        const quantity = parseInt(quantityInput.value) || 0;

        priceInput.value = price.toFixed(2);
        subtotalInput.value = (price * quantity).toFixed(2);

        updateTotal();
    }

    // 🔁 Suma todos los subtotales y muestra el total general
    function updateTotal() {
        let total = 0;
        document.querySelectorAll('.subtotal').forEach(input => {
            total += parseFloat(input.value) || 0;
        });
        document.getElementById('total').textContent = total.toFixed(2);
    }

    // 🆕 Agrega una nueva fila de producto (clonando la primera fila)
    function addProductRow() {
        const container = document.getElementById('productos-container');
        const firstRow = container.querySelector('.producto-row');
        const newRow = firstRow.cloneNode(true); // Clona estructura completa

        // Limpia valores de la fila clonada
        newRow.querySelector('.producto-select').selectedIndex = 0;
        newRow.querySelector('.precio-unitario').value = '0.00';
        newRow.querySelector('.cantidad-input').value = 1;
        newRow.querySelector('.subtotal').value = '0.00';

        // 🔁 Asigna eventos a la nueva fila
        assignEventsToRow(newRow);

        container.appendChild(newRow);
    }

    // 📌 Asigna eventos de cambio a cada fila de producto
    function assignEventsToRow(row) {
        const select = row.querySelector('.producto-select');
        const cantidad = row.querySelector('.cantidad-input');
        const eliminar = row.querySelector('.eliminar-producto');

        select.addEventListener('change', () => updateCalculations(row));
        cantidad.addEventListener('input', () => updateCalculations(row));
        eliminar.addEventListener('click', () => {
            if (document.querySelectorAll('.producto-row').length > 1) {
                row.remove();
                updateTotal();
            } else {
                alert('Debe haber al menos un producto');
            }
        });
    }

    // ✅ Inicializa la primera fila con eventos
    document.querySelectorAll('.producto-row').forEach(row => {
        assignEventsToRow(row);
    });

    // 🧠 Agrega nueva fila cuando se presiona el botón
    document.getElementById('agregar-producto').addEventListener('click', addProductRow);

    // ✅ Validación al enviar el formulario
    document.getElementById('orden-form').addEventListener('submit', function (e) {
        let isValid = true;

        if (!document.getElementById('cliente').value.trim()) {
            alert('Ingrese el nombre del cliente');
            isValid = false;
        }

        document.querySelectorAll('.producto-select').forEach(select => {
            if (!select.value) {
                alert('Seleccione un producto en todas las filas');
                isValid = false;
            }
        });

        if (!isValid) e.preventDefault();
    });
});
