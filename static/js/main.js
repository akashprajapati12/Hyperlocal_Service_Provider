// Star Rating UI
document.addEventListener('DOMContentLoaded', function() {
    const starInputs = document.querySelectorAll('.star-rating input');
    const ratingValue = document.getElementById('rating-value');
    starInputs.forEach(input => {
        input.addEventListener('change', function() {
            if (ratingValue) ratingValue.value = this.value;
        });
    });

    // Payment method selection
    document.querySelectorAll('.payment-method-card').forEach(card => {
        card.addEventListener('click', function() {
            document.querySelectorAll('.payment-method-card').forEach(c => c.classList.remove('selected'));
            this.classList.add('selected');
            const radio = this.querySelector('input[type="radio"]');
            if (radio) radio.checked = true;
        });
    });

    // Auto-dismiss alerts after 5 seconds
    document.querySelectorAll('.alert-dismissible').forEach(alert => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        }, 5000);
    });
});
