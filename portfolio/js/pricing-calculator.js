// Pricing Calculator Logic
document.addEventListener('DOMContentLoaded', function() {
    const serviceType = document.getElementById('service-type');
    const complexity = document.getElementById('complexity');
    const scope = document.getElementById('scope');
    const calculateBtn = document.getElementById('calculate-btn');
    const results = document.getElementById('results');
    
    // Pricing configuration
    const pricingConfig = {
        'api-integration': {
            hourly: { min: 150, max: 250 },
            baseHours: { simple: 20, medium: 40, complex: 80 },
            scopeMultiplier: { small: 1, medium: 2, large: 4, enterprise: 8 }
        },
        'infrastructure': {
            hourly: { min: 200, max: 300 },
            baseHours: { simple: 30, medium: 60, complex: 120 },
            scopeMultiplier: { small: 1, medium: 2, large: 4, enterprise: 8 }
        },
        'ai-development': {
            hourly: { min: 100, max: 200 },
            baseHours: { simple: 15, medium: 30, complex: 60 },
            scopeMultiplier: { small: 1, medium: 2, large: 4, enterprise: 8 }
        },
        'maintenance': {
            monthly: { essential: 500, professional: 1200, enterprise: 2000 }
        }
    };
    
    // Timeline estimates (in weeks)
    const timelineConfig = {
        small: '1-2 weeks',
        medium: '3-6 weeks',
        large: '2-3 months',
        enterprise: '3+ months'
    };
    
    // Show/hide steps based on selections
    serviceType.addEventListener('change', function() {
        if (this.value && this.value !== 'maintenance') {
            document.getElementById('complexity-step').style.display = 'block';
            document.getElementById('scope-step').style.display = 'block';
            document.getElementById('additional-step').style.display = 'block';
        } else if (this.value === 'maintenance') {
            document.getElementById('complexity-step').style.display = 'none';
            document.getElementById('scope-step').style.display = 'none';
            document.getElementById('additional-step').style.display = 'none';
            showMaintenancePricing();
        } else {
            document.getElementById('complexity-step').style.display = 'none';
            document.getElementById('scope-step').style.display = 'none';
            document.getElementById('additional-step').style.display = 'none';
            calculateBtn.style.display = 'none';
            results.style.display = 'none';
        }
    });
    
    complexity.addEventListener('change', checkReady);
    scope.addEventListener('change', checkReady);
    
    function checkReady() {
        if (serviceType.value && serviceType.value !== 'maintenance' && 
            complexity.value && scope.value) {
            calculateBtn.style.display = 'block';
        } else {
            calculateBtn.style.display = 'none';
        }
    }
    
    calculateBtn.addEventListener('click', function() {
        calculateEstimate();
    });
    
    function calculateEstimate() {
        const selectedService = serviceType.value;
        const selectedComplexity = complexity.value;
        const selectedScope = scope.value;
        const additionalRequirements = Array.from(document.querySelectorAll('input[name="requirements"]:checked')).map(cb => cb.value);
        
        if (selectedService === 'maintenance') {
            return; // Handled separately
        }
        
        const config = pricingConfig[selectedService];
        if (!config) return;
        
        // Calculate base hours
        const baseHours = config.baseHours[selectedComplexity];
        const scopeMultiplier = config.scopeMultiplier[selectedScope];
        let totalHours = baseHours * scopeMultiplier;
        
        // Add hours for additional requirements
        additionalRequirements.forEach(req => {
            switch(req) {
                case 'testing':
                    totalHours += totalHours * 0.2; // 20% more for testing
                    break;
                case 'documentation':
                    totalHours += totalHours * 0.15; // 15% more for documentation
                    break;
                case 'deployment':
                    totalHours += 10; // Fixed hours for deployment
                    break;
                case 'training':
                    totalHours += 5; // Fixed hours for training
                    break;
            }
        });
        
        totalHours = Math.round(totalHours);
        
        // Calculate pricing
        const avgHourly = (config.hourly.min + config.hourly.max) / 2;
        const minTotal = totalHours * config.hourly.min;
        const maxTotal = totalHours * config.hourly.max;
        const avgTotal = totalHours * avgHourly;
        
        // Display results
        document.getElementById('estimated-hours').textContent = totalHours + ' hours';
        document.getElementById('hourly-rate').textContent = '$' + config.hourly.min + ' - $' + config.hourly.max + '/hr';
        document.getElementById('estimated-total').textContent = '$' + minTotal.toLocaleString() + ' - $' + maxTotal.toLocaleString();
        document.getElementById('timeline').textContent = timelineConfig[selectedScope];
        
        results.style.display = 'block';
        results.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    
    function showMaintenancePricing() {
        const config = pricingConfig['maintenance'];
        document.getElementById('estimated-hours').textContent = 'N/A';
        document.getElementById('hourly-rate').textContent = 'Monthly Retainer';
        document.getElementById('estimated-total').textContent = 
            '$' + config.monthly.essential + ' - $' + config.monthly.enterprise + '/month';
        document.getElementById('timeline').textContent = 'Ongoing';
        results.style.display = 'block';
    }
});

