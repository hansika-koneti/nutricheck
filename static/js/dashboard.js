/**
 * NutriCheck – Dashboard Module
 * Handles gauge rendering, nutrient card creation, and visual indicators
 */

const Dashboard = {
    NUTRIENT_CONFIG: {
        calories: { icon: '🔥', unit: 'kcal', daily: 2000, positive: false },
        sugar: { icon: '🍬', unit: 'g', daily: 50, positive: false },
        fat: { icon: '🧈', unit: 'g', daily: 65, positive: false },
        sodium: { icon: '🧂', unit: 'mg', daily: 2300, positive: false },
        protein: { icon: '💪', unit: 'g', daily: 50, positive: true },
        fiber: { icon: '🌾', unit: 'g', daily: 28, positive: true },
    },

    /**
     * Animate the SVG gauge to the target score
     */
    animateGauge(score) {
        const gaugeFill = document.getElementById('gaugeFill');
        const gaugeScore = document.getElementById('gaugeScore');

        // Arc length ≈ π * r = π * 80 ≈ 251.3
        const totalLength = 251.3;
        const offset = totalLength - (score / 100) * totalLength;

        // Reset
        gaugeFill.style.strokeDashoffset = totalLength;
        gaugeScore.textContent = '0';

        // Trigger animation after a short delay
        requestAnimationFrame(() => {
            setTimeout(() => {
                gaugeFill.style.strokeDashoffset = offset;
                this.animateCounter(gaugeScore, 0, score, 1200);
            }, 200);
        });
    },

    /**
     * Animate a number counter from start to end
     */
    animateCounter(element, start, end, duration) {
        const startTime = performance.now();
        const update = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            // Ease out cubic
            const eased = 1 - Math.pow(1 - progress, 3);
            const current = Math.round(start + (end - start) * eased);
            element.textContent = current;
            if (progress < 1) {
                requestAnimationFrame(update);
            }
        };
        requestAnimationFrame(update);
    },

    /**
     * Set verdict badge with appropriate styling
     */
    setVerdict(verdict, explanation) {
        const badge = document.getElementById('verdictBadge');
        const explEl = document.getElementById('verdictExplanation');

        badge.textContent = verdict;
        badge.className = 'verdict-badge';

        if (verdict === 'Healthy Choice') {
            badge.classList.add('healthy');
        } else if (verdict === 'Consume in Moderation') {
            badge.classList.add('moderate');
        } else {
            badge.classList.add('limit');
        }

        explEl.textContent = explanation || '';
    },

    /**
     * Render nutrient cards in the grid
     */
    renderNutrients(nutrients) {
        const grid = document.getElementById('nutrientsGrid');
        grid.innerHTML = '';

        for (const [key, config] of Object.entries(this.NUTRIENT_CONFIG)) {
            const value = nutrients[key];
            if (value === null || value === undefined) continue;

            const pct = Math.min(100, (value / config.daily) * 100);
            const level = pct > 40 ? 'high' : pct > 20 ? 'medium' : 'low';

            const card = document.createElement('div');
            card.className = `nutrient-card ${config.positive ? 'positive' : ''}`;
            card.innerHTML = `
                <div class="nutrient-icon">${config.icon}</div>
                <div class="nutrient-name">${key}</div>
                <div class="nutrient-value">${value}</div>
                <div class="nutrient-unit">${config.unit}</div>
                <div class="nutrient-bar-container">
                    <div class="nutrient-bar ${level}" style="width: 0%"></div>
                </div>
                <div class="nutrient-dv">${Math.round(pct)}% of Daily Value</div>
            `;
            grid.appendChild(card);

            // Animate bar after append
            requestAnimationFrame(() => {
                setTimeout(() => {
                    card.querySelector('.nutrient-bar').style.width = `${Math.min(100, pct)}%`;
                }, 300);
            });
        }
    },

    /**
     * Set recommendation text
     */
    setRecommendation(text) {
        document.getElementById('recommendationText').textContent = text || '';
    },

    /**
     * Render full analysis results
     */
    renderResults(data) {
        this.animateGauge(data.health_score || 0);
        this.setVerdict(data.verdict, data.explanation);
        this.renderNutrients(data);
        this.setRecommendation(data.recommendation);
    },

    /**
     * Get verdict CSS class from string
     */
    getVerdictClass(verdict) {
        if (verdict === 'Healthy Choice') return 'healthy';
        if (verdict === 'Consume in Moderation') return 'moderate';
        return 'limit';
    }
};
