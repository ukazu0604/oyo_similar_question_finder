import { state } from './state.js';
import { shouldHighlightProblem } from './utils.js';

// Helper function to determine the tier of a problem
function getProblemTier(problemId, problemChecks, archivedProblemIds) {
    const isArchived = archivedProblemIds.includes(problemId);
    const checks = problemChecks[problemId];
    const checkedCount = checks ? checks.filter(c => c && c.checked).length : 0;

    if (isArchived) {
        return `ARCHIVED_${checkedCount}_CHECKS`;
    } else {
        return `NOT_ARCHIVED_${checkedCount}_CHECKS`;
    }
}

export function renderTotalReactions() {
    const totalOshi = Object.values(state.oshiCounts).reduce((sum, count) => sum + count, 0);
    const totalLike = Object.values(state.likeCounts).reduce((sum, count) => sum + count, 0);
    const totalFear = Object.values(state.fearCounts).reduce((sum, count) => sum + count, 0);

    const totalReactionsEl = document.getElementById('total-reactions');
    if (totalReactionsEl) {
        totalReactionsEl.innerHTML = `
          <span>❤️ ${totalOshi}</span> | <span>👍 ${totalLike}</span> | <span>😱 ${totalFear}</span>
        `;
    }
}

export function renderTotalProgress() {
    if (!state.data.categories) return;

    let totalProblems = 0;
    let totalAchievementPoints = 0; // New variable for achievement points
    const archivedIds = new Set(state.archivedProblemIds);

    // Initialize tier counts
    const tierCounts = {
        NOT_ARCHIVED_0_CHECKS: 0,
        NOT_ARCHIVED_1_CHECK: 0,
        NOT_ARCHIVED_2_CHECKS: 0,
        NOT_ARCHIVED_3_CHECKS: 0,
        NOT_ARCHIVED_4_CHECKS: 0,
        ARCHIVED_0_CHECKS: 0,
        ARCHIVED_1_CHECK: 0,
        ARCHIVED_2_CHECKS: 0,
        ARCHIVED_3_CHECKS: 0,
        ARCHIVED_4_CHECKS: 0,
    };

    // Calculate counts for each tier and achievement points
    for (const middleCat in state.data.categories) {
        const problems = state.data.categories[middleCat];
        totalProblems += problems.length;

        for (const item of problems) {
            const problemId = `${item.main_problem.出典}-${item.main_problem.問題番号}`;
            const isArchived = state.archivedProblemIds.includes(problemId); // Check if problem is archived
            const checks = state.problemChecks[problemId];
            const checkedCount = checks ? checks.filter(c => c && c.checked).length : 0;

            if (isArchived) {
                totalAchievementPoints += 1.0; // Archived problems are 100% achieved
            } else {
                totalAchievementPoints += checkedCount / 4; // Each check contributes 25%
            }

            const tier = getProblemTier(problemId, state.problemChecks, state.archivedProblemIds);
            tierCounts[tier]++;
        }
    }

    // Calculate achievement percentage
    const totalAchievementPercentage = totalProblems > 0 ? (totalAchievementPoints / totalProblems) * 100 : 0;

    // Calculate percentages for each tier (for the stacked bar)
    const tierPercentages = {};
    for (const tier in tierCounts) {
        tierPercentages[tier] = totalProblems > 0 ? (tierCounts[tier] / totalProblems) * 100 : 0;
    }
    
    // stateに計算結果を保存 (テストコードから参照するため - 必要に応じて調整)
    // ここでは新しいティアごとのカウントを保存する
    state.progressTierCounts = tierCounts;
    state.progressTierPercentages = tierPercentages;
    state.totalProblems = totalProblems;

    const container = document.getElementById('total-progress-container');
    if (container) {
        let progressBarHtml = '';
        let legendHtml = '';
        
        const tierOrder = [
            'NOT_ARCHIVED_0_CHECKS', 'NOT_ARCHIVED_1_CHECK', 'NOT_ARCHIVED_2_CHECKS',
            'NOT_ARCHIVED_3_CHECKS', 'NOT_ARCHIVED_4_CHECKS',
            'ARCHIVED_0_CHECKS', 'ARCHIVED_1_CHECK', 'ARCHIVED_2_CHECKS',
            'ARCHIVED_3_CHECKS', 'ARCHIVED_4_CHECKS',
        ];

        const tierLabels = {
            NOT_ARCHIVED_0_CHECKS: '未着手',
            NOT_ARCHIVED_1_CHECK: '1回チェック',
            NOT_ARCHIVED_2_CHECKS: '2回チェック',
            NOT_ARCHIVED_3_CHECKS: '3回チェック',
            NOT_ARCHIVED_4_CHECKS: '4回チェック',
            ARCHIVED_0_CHECKS: 'アーカイブ済(0)',
            ARCHIVED_1_CHECK: 'アーカイブ済(1)',
            ARCHIVED_2_CHECKS: 'アーカイブ済(2)',
            ARCHIVED_3_CHECKS: 'アーカイブ済(3)',
            ARCHIVED_4_CHECKS: 'アーカイブ済(4)',
        };

        tierOrder.forEach(tier => {
            const percentage = tierPercentages[tier].toFixed(2);
            if (percentage > 0) {
                progressBarHtml += `<div class="progress-bar-segment progress-bar-${tier.toLowerCase()}" style="width: ${percentage}%;"></div>`;
                legendHtml += `
                    <span class="legend-item legend-item-${tier.toLowerCase()}">■</span> ${tierLabels[tier]}: ${tierCounts[tier]}問 (${percentage}%) | `;
            }
        });
        // Remove trailing " | " from legend
        legendHtml = legendHtml.replace(/ \| $/, '');


        container.innerHTML = `
        <div class="progress-bar-container stacked">
          <div class="progress-bar">
            ${progressBarHtml}
          </div>
          <div class="progress-text">
             進捗: ${isNaN(totalAchievementPercentage) ? '0.0' : totalAchievementPercentage.toFixed(1)}% (${totalAchievementPoints.toFixed(1)} 問相当 / ${totalProblems} 問中)
          </div>
          <div class="progress-legend">
            ${legendHtml}
          </div>
        </div>
      `;
    }
}

export function renderTotalReviewCount() {
    if (!state.data.categories) return;

    let totalReviewCount = 0;
    for (const middleCat in state.data.categories) {
        for (const item of state.data.categories[middleCat]) {
            const problemId = `${item.main_problem.出典}-${item.main_problem.問題番号}`;
            if (shouldHighlightProblem(problemId, state.problemChecks)) {
                totalReviewCount++;
            }
        }
    }

    const totalReviewEl = document.getElementById('total-review-summary');
    if (totalReviewEl) {
        if (totalReviewCount > 0) {
            totalReviewEl.innerHTML = `<span class="review-count">🔥 ${totalReviewCount}</span>`;
        } else {
            totalReviewEl.innerHTML = `<span class="review-count" style="background: none; color: inherit;">😊</span>`;
        }
    }
}

export function renderExamCountdown() {
    const examDateStr = state.examDate;
    const el = document.getElementById('exam-countdown');
    if (!el) return;

    if (!examDateStr) {
        el.textContent = '';
        el.style.display = 'none';
        return;
    }

    const examDate = new Date(examDateStr);
    const today = new Date();
    // Reset time part for accurate day calculation
    today.setHours(0, 0, 0, 0);
    examDate.setHours(0, 0, 0, 0);

    const diffTime = examDate - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    el.style.display = 'inline-block';
    if (diffDays > 0) {
        el.textContent = `試験まであと ${diffDays} 日`;
    } else if (diffDays === 0) {
        el.textContent = `試験当日です！`;
    } else {
        el.textContent = `試験から ${Math.abs(diffDays)} 日経過`;
    }
}

let notificationTimeout;

/**
 * Show a notification toast with different types and durations
 * @param {string} message - The message to display
 * @param {number} duration - Duration in milliseconds (0 = manual close only)
 * @param {string} type - Notification type: 'success', 'info', 'warning', 'error'
 */
export function showNotification(message, duration = 2000, type = 'info') {
    const container = document.getElementById('notification-container');
    if (!container) return;

    // Clear any existing timeout
    if (notificationTimeout) {
        clearTimeout(notificationTimeout);
        notificationTimeout = null;
    }

    // Remove all type classes
    container.classList.remove('success', 'info', 'warning', 'error', 'visible');

    // Set the message and type
    const showCloseButton = duration === 0 || duration > 5000;

    if (showCloseButton) {
        container.innerHTML = `
            <span class="notification-message">${message}</span>
            <button class="notification-close" aria-label="Close notification">×</button>
        `;

        // Add click handler for close button
        const closeBtn = container.querySelector('.notification-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                container.classList.remove('visible');
                if (notificationTimeout) {
                    clearTimeout(notificationTimeout);
                    notificationTimeout = null;
                }
            });
        }
    } else {
        container.innerHTML = `<span class="notification-message">${message}</span>`;
    }

    // Add type class and show
    container.classList.add(type, 'visible');

    // Auto-hide after duration (if duration > 0)
    if (duration > 0) {
        notificationTimeout = setTimeout(() => {
            container.classList.remove('visible');
            notificationTimeout = null;
        }, duration);
    }
}
