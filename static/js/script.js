document.addEventListener('DOMContentLoaded', function() {
    // Toggle mobile menu
    const mobileMenuBtn = document.createElement('div');
    mobileMenuBtn.className = 'mobile-menu-btn';
    mobileMenuBtn.innerHTML = '<i class="fas fa-bars"></i>';
    document.querySelector('header').prepend(mobileMenuBtn);
    
    mobileMenuBtn.addEventListener('click', function() {
        document.querySelector('.sidebar').classList.toggle('active');
    });
    
    // Close flash messages
    const flashMessages = document.querySelectorAll('.flash');
    flashMessages.forEach(msg => {
        setTimeout(() => {
            msg.style.opacity = '0';
            setTimeout(() => msg.remove(), 300);
        }, 5000);
        
        const closeBtn = document.createElement('span');
        closeBtn.className = 'flash-close';
        closeBtn.innerHTML = '&times;';
        closeBtn.addEventListener('click', () => msg.remove());
        msg.appendChild(closeBtn);
    });
    
    // Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    field.style.borderColor = 'red';
                    isValid = false;
                } else {
                    field.style.borderColor = '';
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                alert('Please fill all required fields');
            }
        });
    });
    
    // Tab functionality for multi-tab interfaces
    const tabs = document.querySelectorAll('.tab');
    if (tabs.length > 0) {
        tabs.forEach(tab => {
            tab.addEventListener('click', function() {
                const tabName = this.getAttribute('data-tab');
                document.querySelectorAll('.tab-content').forEach(content => {
                    content.style.display = 'none';
                });
                document.querySelector(`.tab-content[data-tab="${tabName}"]`).style.display = 'block';
                
                tabs.forEach(t => t.classList.remove('active'));
                this.classList.add('active');
            });
        });
        
        // Activate first tab by default
        tabs[0].click();
    }
});
// Add to your existing DOMContentLoaded function

// Toggle form visibility
const toggleFormBtn = document.getElementById('toggleFormBtn');
if (toggleFormBtn) {
    toggleFormBtn.addEventListener('click', function() {
        const form = document.getElementById('stakeholderForm');
        form.style.display = form.style.display === 'none' ? 'block' : 'none';
        this.innerHTML = form.style.display === 'none' 
            ? '<i class="fas fa-plus"></i> Add Stakeholder' 
            : '<i class="fas fa-times"></i> Cancel';
    });
}

// Make table rows clickable
document.querySelectorAll('.table tbody tr').forEach(row => {
    row.addEventListener('click', function(e) {
        if (!e.target.closest('a')) { // Don't trigger if clicking on links
            // Implement your view/edit logic here
            console.log('Viewing stakeholder ID:', this.cells[0].textContent);
        }
    });
});

// Add hover effects to table rows
document.querySelectorAll('.table tbody tr').forEach(row => {
    row.style.cursor = 'pointer';
    row.style.transition = 'background-color 0.2s';
    
    row.addEventListener('mouseenter', () => {
        row.style.backgroundColor = '#f8f9fa';
    });
    
    row.addEventListener('mouseleave', () => {
        row.style.backgroundColor = '';
    });
});
// Meeting-specific functionality
document.addEventListener('DOMContentLoaded', function() {
    // Toggle meeting form
    const toggleMeetingFormBtn = document.getElementById('toggleMeetingFormBtn');
    if (toggleMeetingFormBtn) {
        toggleMeetingFormBtn.addEventListener('click', function() {
            const form = document.getElementById('meetingForm');
            form.style.display = form.style.display === 'none' ? 'block' : 'none';
            this.innerHTML = form.style.display === 'none' 
                ? '<i class="fas fa-plus"></i> Schedule Meeting' 
                : '<i class="fas fa-times"></i> Cancel';
        });
    }

    // Filter meetings
    const timeFilter = document.getElementById('timeFilter');
    if (timeFilter) {
        timeFilter.addEventListener('change', function() {
            const rows = document.querySelectorAll('#meetingsTable tbody tr');
            rows.forEach(row => {
                if (this.value === 'all') {
                    row.style.display = '';
                } else if (this.value === 'upcoming') {
                    row.style.display = row.classList.contains('upcoming') ? '' : 'none';
                } else {
                    row.style.display = row.classList.contains('past') ? '' : 'none';
                }
            });
        });
    }

    // Search meetings
    const meetingSearch = document.getElementById('meetingSearch');
    if (meetingSearch) {
        meetingSearch.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const rows = document.querySelectorAll('#meetingsTable tbody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        });
    }

    // Enhanced row clicking
    document.querySelectorAll('#meetingsTable tbody tr').forEach(row => {
        row.addEventListener('click', function(e) {
            if (!e.target.closest('.actions a')) {
                const id = this.cells[0].textContent;
                // Implement modal or redirect to detailed view
                window.location.href = `/meeting/${id}`;
            }
        });
    });
});
// Dashboard specific functionality
document.addEventListener('DOMContentLoaded', function() {
    // Make table rows clickable
    document.querySelectorAll('.clickable-row').forEach(row => {
        row.addEventListener('click', function() {
            const link = this.dataset.href;
            if (link) window.location.href = link;
        });
    });

    // Animate stat cards on load
    const statCards = document.querySelectorAll('.stat-card');
    statCards.forEach((card, index) => {
        setTimeout(() => {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });

    // Initialize tooltips
    tippy('[data-tippy-content]', {
        arrow: true,
        animation: 'shift-away'
    });
});
// Confirm before edit (optional)
document.querySelectorAll('.btn-edit').forEach(btn => {
    btn.addEventListener('click', function(e) {
        if (!confirm('Are you sure you want to edit this stakeholder?')) {
            e.preventDefault();
        }
    });
});