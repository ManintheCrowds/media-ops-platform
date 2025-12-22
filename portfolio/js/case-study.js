// Case Study Interactive Features

document.addEventListener('DOMContentLoaded', function() {
    // Animate counter numbers on scroll
    const animateCounters = () => {
        const counters = document.querySelectorAll('.quick-stat-number');
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && !entry.target.classList.contains('animated')) {
                    const target = parseInt(entry.target.getAttribute('data-target'));
                    const duration = 2000; // 2 seconds
                    const increment = target / (duration / 16); // 60fps
                    let current = 0;
                    
                    entry.target.classList.add('animated');
                    
                    const updateCounter = () => {
                        current += increment;
                        if (current < target) {
                            entry.target.textContent = Math.floor(current);
                            requestAnimationFrame(updateCounter);
                        } else {
                            entry.target.textContent = target;
                        }
                    };
                    
                    updateCounter();
                }
            });
        }, { threshold: 0.5 });
        
        counters.forEach(counter => observer.observe(counter));
    };

    // Smooth scroll for anchor links
    const smoothScroll = () => {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function(e) {
                const href = this.getAttribute('href');
                if (href !== '#' && href.length > 1) {
                    const target = document.querySelector(href);
                    if (target) {
                        e.preventDefault();
                        const headerOffset = 90;
                        const elementPosition = target.getBoundingClientRect().top;
                        const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

                        window.scrollTo({
                            top: offsetPosition,
                            behavior: 'smooth'
                        });
                    }
                }
            });
        });
    };

    // Make table of contents sticky
    const stickyTOC = () => {
        const toc = document.querySelector('.table-of-contents');
        if (toc) {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (!entry.isIntersecting) {
                        toc.style.position = 'fixed';
                        toc.style.top = '90px';
                        toc.style.width = toc.offsetWidth + 'px';
                    } else {
                        toc.style.position = 'sticky';
                        toc.style.width = 'auto';
                    }
                });
            }, { threshold: 0 });
            
            const sentinel = document.createElement('div');
            sentinel.style.height = '1px';
            toc.parentNode.insertBefore(sentinel, toc);
            observer.observe(sentinel);
        }
    };

    // Tab functionality for diagrams
    const initTabs = () => {
        const tabButtons = document.querySelectorAll('.tab-btn');
        const tabContents = document.querySelectorAll('.tab-content');
        
        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const targetTab = button.getAttribute('data-tab');
                
                // Remove active class from all buttons and contents
                tabButtons.forEach(btn => btn.classList.remove('active'));
                tabContents.forEach(content => content.classList.remove('active'));
                
                // Add active class to clicked button and corresponding content
                button.classList.add('active');
                const targetContent = document.getElementById(targetTab);
                if (targetContent) {
                    targetContent.classList.add('active');
                }
            });
        });
    };

    // Initialize
    animateCounters();
    smoothScroll();
    stickyTOC();
    initTabs();

    // Add view full diagram functionality
    const diagramImages = document.querySelectorAll('.diagram-image');
    diagramImages.forEach(img => {
        img.style.cursor = 'pointer';
        img.addEventListener('click', function() {
            const modal = document.createElement('div');
            modal.className = 'diagram-modal';
            modal.innerHTML = `
                <div class="diagram-modal-content">
                    <span class="diagram-modal-close">&times;</span>
                    <img src="${this.src}" alt="${this.alt}">
                </div>
            `;
            document.body.appendChild(modal);
            document.body.style.overflow = 'hidden';
            
            const closeModal = () => {
                document.body.removeChild(modal);
                document.body.style.overflow = '';
            };
            
            modal.querySelector('.diagram-modal-close').addEventListener('click', closeModal);
            modal.addEventListener('click', function(e) {
                if (e.target === modal) closeModal();
            });
            
            document.addEventListener('keydown', function(e) {
                if (e.key === 'Escape') closeModal();
            });
        });
    });
});

