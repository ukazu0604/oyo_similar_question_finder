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

    let totalProblems = 0; // 総問題数
    let totalCheckedCount = 0; // チェックされた総数

    for (const middleCat in state.data.categories) {
        const problems = state.data.categories[middleCat];
        totalProblems += problems.length;
        for (const item of problems) {
            const problemId = `${item.main_problem.出典}-${item.main_problem.問題番号}`;
            const checks = state.problemChecks[problemId];
            if (checks) {
                checks.forEach(c => {
                    if (c && c.checked) {
                        totalCheckedCount++;
                    }
                });
            }
        }
    }
    const completedProblemsEquivalent = totalCheckedCount / 4; // 4チェックで1問完了と換算
    const progressPercentage = totalProblems > 0 ? (completedProblemsEquivalent / totalProblems) * 100 : 0;

    const container = document.getElementById('total-progress-container');
    if (container) {
        container.innerHTML = `
        <div class="progress-bar-container">
          <div class="progress-bar">
            <div class="progress-bar-inner" style="width: ${progressPercentage.toFixed(2)}%;"></div>
          </div>
          <div class="progress-text">${completedProblemsEquivalent.toFixed(2)} / ${totalProblems} 問</div>
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
