// CASS - User Registration JavaScript

document.addEventListener('DOMContentLoaded', () => {
    const registerForm = document.getElementById('registerForm');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirmPassword');

    if (registerForm) {
        registerForm.addEventListener('submit', (e) => {
            // Validate passwords match
            if (passwordInput.value !== confirmPasswordInput.value) {
                e.preventDefault();
                alert('Passwords do not match!');
                confirmPasswordInput.focus();
                return false;
            }

            // Validate password length
            if (passwordInput.value.length < 6) {
                e.preventDefault();
                alert('Password must be at least 6 characters long!');
                passwordInput.focus();
                return false;
            }

            // Validate email format
            const emailInput = document.getElementById('email');
            const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailPattern.test(emailInput.value)) {
                e.preventDefault();
                alert('Please enter a valid email address!');
                emailInput.focus();
                return false;
            }

            // Disable submit button to prevent double submission
            const submitBtn = registerForm.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Registering...';
            }
        });

        // Real-time password match indicator
        confirmPasswordInput.addEventListener('input', () => {
            if (confirmPasswordInput.value.length > 0) {
                if (passwordInput.value === confirmPasswordInput.value) {
                    confirmPasswordInput.style.borderColor = '#28a745';
                } else {
                    confirmPasswordInput.style.borderColor = '#dc3545';
                }
            } else {
                confirmPasswordInput.style.borderColor = '';
            }
        });
    }
});
