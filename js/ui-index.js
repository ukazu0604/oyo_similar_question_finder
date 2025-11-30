import { state } from './state.js';
import { storage } from './storage.js';
import { shouldHighlightProblem } from './utils.js';
import { navigateToDetail } from './router.js';
import { renderTotalReviewCount, renderTotalProgress } from './ui-common.js';

export function showIndex(isPopState = false) {
    const indexView = document.getElementById('index-view');
    const detailView = document.getElementById('detail-view');

    detailView.style.display = 'none';
    indexView.style.display = 'block';

    renderIndex(state.data.categories);
    renderTotalReviewCount();
    renderTotalProgress();
    window.scrollTo(0, 0);

    // トップページに復習項目がある場合、最初の復習項目までスクロールする
    // 描画が完了するのを待つために少し遅延させる
    setTimeout(() => {
        const firstReviewCategory = document.querySelector('.middle-category-link.has-review-items');
        if (firstReviewCategory) {
            // isPopStateがtrue（ブラウザバックなど）の場合はスクロール位置が復元されるため、
            // ユーザーの明示的な操作がない場合のみスクロールする
            if (!isPopState) firstReviewCategory.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }, 100);
}

export function renderIndex(categories) {
    const categoryList = document.getElementById('category-list');

    // 大項目でグループ化
    const groupedByLargeCategory = {};
    for (const [middleCat, problems] of Object.entries(categories)) {
        if (problems.length > 0) {
            const largeCat = problems[0].main_problem.大項目;
            if (!groupedByLargeCategory[largeCat]) {
                groupedByLargeCategory[largeCat] = [];
            }
            groupedByLargeCategory[largeCat].push({ middleCat, problems });
        }
    }

    categoryList.innerHTML = '';
    // 大項目のキーでソートして表示
    Object.keys(groupedByLargeCategory).sort((a, b) => {
        // "1.基礎理論"のような文字列から先頭の数字を抜き出して比較する
        const numA = parseInt(a.split('.')[0], 10);
        const numB = parseInt(b.split('.')[0], 10);
        return numA - numB;
    }).forEach(largeCat => {
        // --- START: New logic for large category summary ---
        let largeCatTotalProblems = 0; // Total problems in this large category (archived + non-archived)
        let largeCatNonArchivedCheckedCount = 0;
        let largeCatArchivedCheckedCount = 0;
        let largeCatArchivedProblemCount = 0; // Number of archived problems in this large category
        let largeCatTotalReviewItems = 0;

        groupedByLargeCategory[largeCat].forEach(({ problems }) => {
            largeCatTotalProblems += problems.length; // Sum all problems for denominator

            problems.forEach(item => {
                const problemId = `${item.main_problem.出典}-${item.main_problem.問題番号}`;
                const isArchived = state.archivedProblemIds.includes(problemId);
                const checks = state.problemChecks[problemId];
                const checkedCount = checks ? checks.filter(c => c && c.checked).length : 0;

                if (isArchived) {
                    largeCatArchivedProblemCount++;
                    largeCatArchivedCheckedCount += checkedCount;
                } else {
                    largeCatNonArchivedCheckedCount += checkedCount;
                }

                // Calculate review items (this logic remains the same)
                if (shouldHighlightProblem(problemId, state.problemChecks)) {
                    largeCatTotalReviewItems++;
                }
            });
        });

        const largeCatNonArchivedEquivalent = largeCatNonArchivedCheckedCount / 4;
        const largeCatArchivedEquivalent = largeCatArchivedCheckedCount / 4;

        const largeCatCompletedPercentage = largeCatTotalProblems > 0 ? (largeCatNonArchivedEquivalent / largeCatTotalProblems) * 100 : 0;
        const largeCatArchivedPercentage = largeCatTotalProblems > 0 ? (largeCatArchivedProblemCount / largeCatTotalProblems) * 100 : 0;

        const largeCatTotalProgressPercentage = largeCatCompletedPercentage + largeCatArchivedPercentage;
        // --- END: New logic ---

        const largeCategorySection = document.createElement('div');
        largeCategorySection.className = 'major-category';

        // -- Reworked majorTitle --
        const majorTitle = document.createElement('div');
        majorTitle.className = 'major-title';
        majorTitle.dataset.largeCat = largeCat;
        majorTitle.style.display = 'flex';
        majorTitle.style.justifyContent = 'space-between';
        majorTitle.style.alignItems = 'center';

        const titleTextEl = document.createElement('span');
        titleTextEl.className = 'large-category-title-text';
        // title innerHTML will be set by expand/collapse logic later

        const summaryEl = document.createElement('div');
        summaryEl.className = 'large-category-summary';
        summaryEl.innerHTML = `
        <span class="progress-percentage">${largeCatTotalProgressPercentage.toFixed(0)}%</span>
        ${largeCatTotalReviewItems > 0 ? `<span class="review-count">🔥 ${largeCatTotalReviewItems}</span>` : ''}
        <span class="problem-count">${largeCatTotalProblems}問</span>
      `;

        majorTitle.appendChild(titleTextEl);
        majorTitle.appendChild(summaryEl);
        largeCategorySection.appendChild(majorTitle);
        // -- End rework --

        const middleCategoryList = document.createElement('div');
        middleCategoryList.className = 'middle-category-list'; // クラスを追加
        groupedByLargeCategory[largeCat].forEach(({ middleCat, problems }) => {
            // カテゴリごとのリアクション合計を計算
            let totalOshi = 0;
            let totalLike = 0;
            let totalFear = 0;
            problems.forEach(item => {
                const problemId = `${item.main_problem.出典}-${item.main_problem.問題番号}`;
                totalOshi += state.oshiCounts[problemId] || 0;
                totalLike += state.likeCounts[problemId] || 0;
                totalFear += state.fearCounts[problemId] || 0;
            });

            // このカテゴリの進捗を計算
            let problemsInThisCategory = problems.length; // フィルター前のこのカテゴリの問題総数

            let nonArchivedCheckedCount = 0;
            let archivedCheckedCount = 0;
            let archivedProblemCount = 0; // このカテゴリ内のアーカイブ済み問題数

            problems.forEach(item => { // このproblems配列はアーカイブ済みも含む
                const problemId = `${item.main_problem.出典}-${item.main_problem.問題番号}`;
                const isArchived = state.archivedProblemIds.includes(problemId);
                const checks = state.problemChecks[problemId];
                const checkedCount = checks ? checks.filter(c => c && c.checked).length : 0;

                if (isArchived) {
                    archivedProblemCount++;
                    archivedCheckedCount += checkedCount;
                } else {
                    nonArchivedCheckedCount += checkedCount;
                }
            });

            const nonArchivedEquivalent = nonArchivedCheckedCount / 4;
            const archivedEquivalent = archivedCheckedCount / 4;

            const completedPercentage = problemsInThisCategory > 0 ? (nonArchivedEquivalent / problemsInThisCategory) * 100 : 0;
            const archivedPercentage = problemsInThisCategory > 0 ? (archivedProblemCount / problemsInThisCategory) * 100 : 0;

            const totalCategoryProgressPercentage = completedPercentage + archivedPercentage;

            const progressHtml = `<span class="progress-percentage">${totalCategoryProgressPercentage.toFixed(0)}%</span>`;


            // このカテゴリにハイライトすべき問題があるかチェック
            let reviewItemCount = 0;
            for (const item of problems) {
                const problemId = `${item.main_problem.出典}-${item.main_problem.問題番号}`;
                if (shouldHighlightProblem(problemId, state.problemChecks)) {
                    reviewItemCount++;
                }
            }
            const hasReviewItems = reviewItemCount > 0;

            // 復習カウントのHTMLを生成
            let reviewCountHtml = ''; // デフォルトは空文字列
            if (hasReviewItems) {
                reviewCountHtml = `<span class="review-count">🔥 ${reviewItemCount}</span>`;
            }

            // 表示用のHTMLを生成
            const reactionSummaryHtml = `
            <div class="reaction-summary">
              <span>❤️ ${totalOshi}</span>
              <span>👍 ${totalLike}</span>
              <span>😱 ${totalFear}</span>
            </div>`;

            const item = document.createElement('div');
            item.className = 'middle-category-item';
            item.innerHTML = `
            <a href="#" class="middle-category-link ${hasReviewItems ? 'has-review-items' : ''}" data-cat="${middleCat}">
              <span class="category-name">${middleCat}</span>
              <div class="category-meta">
                ${progressHtml}
                ${reviewCountHtml}
                ${reactionSummaryHtml}
                <span class="problem-count">${problems.length}問</span>
                <span class="arrow">›</span>
              </div>
            </a>`;
            middleCategoryList.appendChild(item);
        });
        largeCategorySection.appendChild(middleCategoryList);
        categoryList.appendChild(largeCategorySection);
    });

    // --- Reworked event listeners ---
    // 大項目の開閉機能を追加
    document.querySelectorAll('.major-title').forEach(titleEl => {
        const largeCat = titleEl.dataset.largeCat;
        const titleTextEl = titleEl.querySelector('.large-category-title-text');
        const listEl = titleEl.nextElementSibling; // middle-category-listを指す
        // storageから開閉状態を復元。指定がなければ閉じた状態がデフォルト
        let isCollapsed = storage.isMajorCatCollapsed(largeCat);
        if (isCollapsed) {
            listEl.style.display = 'none';
            titleTextEl.innerHTML = `▶ ${largeCat}`; // 閉じた状態の矢印
        } else {
            listEl.style.display = ''; // デフォルト表示
            titleTextEl.innerHTML = `▼ ${largeCat}`; // 開いた状態の矢印
        }

        titleEl.addEventListener('click', () => {
            const currentlyCollapsed = listEl.style.display === 'none';
            if (currentlyCollapsed) {
                listEl.style.display = ''; // 表示
                titleTextEl.innerHTML = `▼ ${largeCat}`;
                storage.setMajorCatCollapsed(largeCat, false);
            } else {
                listEl.style.display = 'none'; // 非表示
                titleTextEl.innerHTML = `▶ ${largeCat}`;
                storage.setMajorCatCollapsed(largeCat, true);
            }
        });
    });

    // イベント設定
    document.querySelectorAll('.middle-category-link').forEach(link => {
        link.addEventListener('click', e => {
            e.preventDefault();
            const cat = e.currentTarget.dataset.cat;
            console.log(`[カテゴリクリック] カテゴリ「${cat}」がクリックされました。`);

            console.log(`[画面遷移] navigateToDetail('${cat}') を呼び出します。`);
            navigateToDetail(cat);
        });
    });
    console.log("renderIndex completed"); // Debug log
}
