import { state } from './state.js';
import { shouldHighlightProblem } from './utils.js';

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
    let partialCompletedCount = 0; // 0.25刻みの進捗を保持する新しい変数
    const archivedIds = new Set(state.archivedProblemIds); // 高速なルックアップのためSetを使用
    const archivedCount = archivedIds.size;

    for (const middleCat in state.data.categories) {
        const problems = state.data.categories[middleCat];
        totalProblems += problems.length;

        for (const item of problems) {
            const problemId = `${item.main_problem.出典}-${item.main_problem.問題番号}`;

            // アーカイブ済みの問題は進捗に含めないが、アーカイブバーの計算には使う
            if (archivedIds.has(problemId)) {
                continue;
            }

            const checks = state.problemChecks[problemId];
            if (checks) {
                const checkedCount = checks.filter(c => c && c.checked).length;
                partialCompletedCount += checkedCount / 4; // 0.25刻みで加算
            }
        }
    }

    // 進捗バーの計算は partialCompletedCount を使用
    const completedPercentage = totalProblems > 0 ? (partialCompletedCount / totalProblems) * 100 : 0;
    const archivedPercentage = totalProblems > 0 ? (archivedCount / totalProblems) * 100 : 0;
    const totalProgressPercentage = completedPercentage + archivedPercentage;

    // stateに計算結果を保存 (テストコードから参照するため)
    state.calculatedCompletedCount = partialCompletedCount;
    state.calculatedArchivedCount = archivedCount;

    const container = document.getElementById('total-progress-container');
    if (container) {
        container.innerHTML = `
        <div class="progress-bar-container stacked">
          <div class="progress-bar">
            <div class="progress-bar-completed" style="width: ${completedPercentage.toFixed(2)}%;"></div>
            <div class="progress-bar-archived" style="width: ${archivedPercentage.toFixed(2)}%;"></div>
          </div>
          <div class="progress-text">
             進捗: ${totalProgressPercentage.toFixed(1)}% (${(partialCompletedCount + archivedCount).toFixed(1)} / ${totalProblems} 問)
          </div>
          <div class="progress-legend">
            <span class="legend-item completed">■</span>完了: ${partialCompletedCount.toFixed(1)}問 (${completedPercentage.toFixed(1)}%) | 
            <span class="legend-item archived">■</span>アーカイブ: ${archivedCount}問 (${archivedPercentage.toFixed(1)}%)
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
