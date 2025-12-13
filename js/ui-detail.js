import { state } from './state.js';
import { storage } from './storage.js';
import { isMobileDevice, shouldHighlightProblem, isProblemUntouched } from './utils.js';
import { renderTotalReactions, renderTotalProgress, renderTotalReviewCount, showNotification } from './ui-common.js';

export function showDetail(middleCat, isPopState = false, scrollToProblemId = null) {
    const indexView = document.getElementById('index-view');
    const detailView = document.getElementById('detail-view');

    indexView.style.display = 'none';
    detailView.style.display = 'block';
    document.getElementById('detail-title').textContent = middleCat;

    const container = document.getElementById('detail-container');
    container.innerHTML = '';

    // 要件1-2: 復習項目があれば自動で「復習優先」にソート
    const problemsForCheck = state.data.categories[middleCat];
    const hasReviewItems = problemsForCheck.some(item => {
        const problemId = `${item.main_problem.出典}-${item.main_problem.問題番号}`;
        return shouldHighlightProblem(problemId, state.problemChecks);
    });

    const storedSortOrder = storage.loadSortOrder();

    if (storedSortOrder) {
        // 保存されたソート順があればそれを優先
        state.currentSortOrder = storedSortOrder;
        console.log(`[並び順適用] 保存された設定「${state.currentSortOrder}」を適用します。`);
    } else if (hasReviewItems) {
        // 保存された設定がなく、復習項目があれば「復習優先」を提案
        state.currentSortOrder = 'review-first';
        console.log(`[自動並び順変更] カテゴリ「${middleCat}」に復習項目があるため、並び順を「復習優先」に変更しました。`);
    } else {
        // 保存された設定も復習項目もなければデフォルト
        state.currentSortOrder = 'default';
        console.log(`[並び順適用] デフォルトの並び順を適用します。`);
    }


    // isPopState（リロードやブラウザバック）の場合のみstorageから状態を復元
    if (isPopState) {
        state.showUntouchedOnly = storage.loadShowUntouchedOnly();
        state.showArchivedOnly = storage.loadShowArchivedOnly();
        state.showFavoritesOnly = storage.loadShowFavoritesOnly();
        console.log(`[状態復元] フィルター状態を復元しました。`);
    } else {
        state.showUntouchedOnly = false;
        state.showArchivedOnly = false;
        state.showFavoritesOnly = false;
        console.log(`[状態リセット] フィルター状態をリセットしました。`);
    }

    renderProblemList(middleCat); // Call renderProblemList first

    // New logic: Scroll to specific problem if scrollToProblemId is provided
    if (scrollToProblemId) {
        // Delay scroll to ensure elements are rendered
        setTimeout(() => {
            const problemCardElement = document.querySelector(`.problem-panel[data-problem-id="${scrollToProblemId}"]`);
            if (problemCardElement) {
                problemCardElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
                // Optional: add temporary highlight
                problemCardElement.classList.add('highlight-problem');
                setTimeout(() => {
                    problemCardElement.classList.remove('highlight-problem');
                }, 2000);
            }
        }, 100);
    }

    // 「未着手のみ表示」チェックボックス
    const untouchedCheckbox = document.getElementById('show-untouched-only');
    untouchedCheckbox.replaceWith(untouchedCheckbox.cloneNode(true));
    document.getElementById('show-untouched-only').addEventListener('change', e => {
        state.showUntouchedOnly = e.target.checked;
        storage.saveShowUntouchedOnly(state.showUntouchedOnly);
        renderProblemList(middleCat);
    });
    document.getElementById('show-untouched-only').checked = state.showUntouchedOnly;

    // 「アーカイブ済みを表示」チェックボックス
    const archivedCheckbox = document.getElementById('show-archived-only');
    archivedCheckbox.replaceWith(archivedCheckbox.cloneNode(true));
    document.getElementById('show-archived-only').addEventListener('change', e => {
        state.showArchivedOnly = e.target.checked;
        storage.saveShowArchivedOnly(state.showArchivedOnly);
        renderProblemList(middleCat);
    });
    document.getElementById('show-archived-only').checked = state.showArchivedOnly;

    // 「お気に入りのみ表示」チェックボックス
    const favoritesCheckbox = document.getElementById('show-favorites-only');
    favoritesCheckbox.replaceWith(favoritesCheckbox.cloneNode(true));
    document.getElementById('show-favorites-only').addEventListener('change', e => {
        state.showFavoritesOnly = e.target.checked;
        storage.saveShowFavoritesOnly(state.showFavoritesOnly);
        renderProblemList(middleCat);
    });
    document.getElementById('show-favorites-only').checked = state.showFavoritesOnly;

    // ソート順変更
    const sortOrderSelect = document.getElementById('sort-order');
    sortOrderSelect.replaceWith(sortOrderSelect.cloneNode(true));
    document.getElementById('sort-order').addEventListener('change', e => {
        state.currentSortOrder = e.target.value;
        storage.saveSortOrder(state.currentSortOrder);

        const currentCat = document.getElementById('detail-title').textContent;
        if (currentCat) {
            renderProblemList(currentCat);
        }
    });
    document.getElementById('sort-order').value = state.currentSortOrder;
}

export function renderProblemList(middleCat) {
    let problems = [...state.data.categories[middleCat]];
    const countsForThisCat = state.referenceCounts[middleCat] || {};

    // アーカイブフィルター
    if (state.showArchivedOnly) {
        problems = problems.filter(item => {
            const problemId = `${item.main_problem.出典}-${item.main_problem.問題番号}`;
            return state.archivedProblemIds.includes(problemId);
        });
    } else {
        problems = problems.filter(item => {
            const problemId = `${item.main_problem.出典}-${item.main_problem.問題番号}`;
            return !state.archivedProblemIds.includes(problemId);
        });
    }

    // 未着手フィルター
    if (state.showUntouchedOnly) {
        problems = problems.filter(item => isProblemUntouched(item, state.problemChecks));
    }

    // お気に入りフィルター
    if (state.showFavoritesOnly) {
        problems = problems.filter(item => {
            const problemId = `${item.main_problem.出典}-${item.main_problem.問題番号}`;
            return state.favorites.includes(problemId);
        });
    }

    // ソート
    if (state.currentSortOrder === 'review-first') {
        problems.sort((a, b) => {
            const aId = `${a.main_problem.出典}-${a.main_problem.問題番号}`;
            const bId = `${b.main_problem.出典}-${b.main_problem.問題番号}`;
            const aNeedsReview = shouldHighlightProblem(aId, state.problemChecks);
            const bNeedsReview = shouldHighlightProblem(bId, state.problemChecks);

            if (aNeedsReview !== bNeedsReview) {
                return bNeedsReview - aNeedsReview;
            }
            return a.main_problem.問題番号 - b.main_problem.問題番号;
        });
    } else if (state.currentSortOrder === 'ref-desc') {
        problems.sort((a, b) => {
            const countA = countsForThisCat[a.main_problem.問題番号] || 0;
            const countB = countsForThisCat[b.main_problem.問題番号] || 0;
            return countB - countA;
        });
    } else if (state.currentSortOrder === 'oshi-desc') {
        problems.sort((a, b) => {
            const countA = state.oshiCounts[`${a.main_problem.出典}-${a.main_problem.問題番号}`] || 0;
            const countB = state.oshiCounts[`${b.main_problem.出典}-${b.main_problem.問題番号}`] || 0;
            return countB - countA;
        });
    } else if (state.currentSortOrder === 'like-desc') {
        problems.sort((a, b) => {
            const countA = state.likeCounts[`${a.main_problem.出典}-${a.main_problem.問題番号}`] || 0;
            const countB = state.likeCounts[`${b.main_problem.出典}-${b.main_problem.問題番号}`] || 0;
            return countB - countA;
        });
    } else if (state.currentSortOrder === 'fear-desc') {
        problems.sort((a, b) => {
            const countA = state.fearCounts[`${a.main_problem.出典}-${a.main_problem.問題番号}`] || 0;
            const countB = state.fearCounts[`${b.main_problem.出典}-${b.main_problem.問題番号}`] || 0;
            return countB - countA;
        });
    } else {
        problems.sort((a, b) => {
            return a.main_problem.問題番号 - b.main_problem.問題番号;
        });
    }

    const container = document.getElementById('detail-container');
    container.innerHTML = '';
    problems.forEach(item => {
        const main = item.main_problem;
        let mainProblemLink = main.リンク;
        if (isMobileDevice()) {
            mainProblemLink = mainProblemLink.replace('https://www.ap-siken.com/', 'https://www.ap-siken.com/s/');
        }

        const card = document.createElement('div');
        const mainProblemUniqueId = `${main.出典}-${main.問題番号}`;
        const needsReview = shouldHighlightProblem(mainProblemUniqueId, state.problemChecks);

        // Checks
        let checksHtml = '<div class="check-container">';
        for (let i = 0; i < 4; i++) {
            const checkData = state.problemChecks[mainProblemUniqueId]?.[i];
            const isChecked = checkData && checkData.checked;
            checksHtml += `<div class="check-box ${isChecked ? 'checked c' + i : ''}" data-problem-id="${mainProblemUniqueId}" data-check-index="${i}"></div>`;
        }
        checksHtml += '</div>';

        // Reactions
        const mainOshiCount = state.oshiCounts[mainProblemUniqueId] || 0;
        const mainLikeCount = state.likeCounts[mainProblemUniqueId] || 0;
        const mainFearCount = state.fearCounts[mainProblemUniqueId] || 0;
        const reactionHtml = `
          <div class="reaction-container">
            <button class="reaction-button" data-problem-id="${mainProblemUniqueId}" data-reaction-type="oshi">❤️</button>
            <span class="reaction-count">${mainOshiCount}</span>
            <button class="reaction-button" data-problem-id="${mainProblemUniqueId}" data-reaction-type="like">👍</button>
            <span class="reaction-count">${mainLikeCount}</span>
            <button class="reaction-button" data-problem-id="${mainProblemUniqueId}" data-reaction-type="fear">😱</button>
            <span class="reaction-count">${mainFearCount}</span>
          </div>`;

        // Archive
        const isArchived = state.archivedProblemIds.includes(mainProblemUniqueId);
        const archiveHtml = `
          <div class="archive-container">
            <button class="archive-button" data-problem-id="${mainProblemUniqueId}">
              ${isArchived ? '↩️ 元に戻す' : '📥 アーカイブ'}
            </button>
          </div>
        `;

        // Star (Favorite)
        const isFavorite = state.favorites.includes(mainProblemUniqueId);
        const starHtml = `<span class="star-icon ${isFavorite ? 'active' : ''}" data-problem-id="${mainProblemUniqueId}">★</span>`;

        card.className = `problem-card ${needsReview ? 'needs-review' : ''}`;
        let html = `
          <a href="${mainProblemLink}" target="_blank" class="problem-panel main-problem" data-problem-id="${mainProblemUniqueId}">
            <div class="problem-number">${starHtml} 問題: ${main.問題番号}</div>
            <div class="problem-title">${main.問題名}</div>
            <div class="problem-source">出典: ${main.出典} ${reactionHtml}</div>
            ${checksHtml}
            ${archiveHtml}
          </a>
        `;

        // Similar Problems
        const filteredSimilars = item.similar_problems
            ? item.similar_problems
                .sort((a, b) => b.similarity - a.similarity)
                .filter((sim, index) => index < 5 || sim.similarity >= 0.9)
            : [];

        if (filteredSimilars.length > 0) {
            const similarCount = filteredSimilars.length;
            const totalSimilarity = filteredSimilars.reduce((sum, sim) => sum + sim.similarity, 0);
            const averageSimilarity = (totalSimilarity / similarCount) * 100;

            html += `
            <div class="similar-section">
              <div class="similar-toggle">
                <span class="similar-title">📊 類似問題 (${similarCount}件)</span>
                <span class="average-similarity">平均: ${averageSimilarity.toFixed(1)}%</span>
                <span class="toggle-arrow">▼</span>
              </div>
              <div class="similar-content" style="display: none;">
          `;
            filteredSimilars.forEach(sim => {
                const s = sim.data;
                let similarProblemLink = s.リンク;
                if (isMobileDevice()) {
                    similarProblemLink = similarProblemLink.replace('https://www.ap-siken.com/', 'https://www.ap-siken.com/s/');
                }

                const simProblemUniqueId = `${s.出典}-${s.問題番号}`;
                let simChecksHtml = '<div class="check-container">';
                for (let i = 0; i < 4; i++) {
                    const isChecked = state.problemChecks[simProblemUniqueId]?.[i]?.checked;
                    simChecksHtml += `<div class="check-box ${isChecked ? 'checked c' + i : ''}" data-problem-id="${simProblemUniqueId}" data-check-index="${i}"></div>`;
                }
                simChecksHtml += '</div>';

                const simOshiCount = state.oshiCounts[simProblemUniqueId] || 0;
                const simLikeCount = state.likeCounts[simProblemUniqueId] || 0;
                const simFearCount = state.fearCounts[simProblemUniqueId] || 0;
                const simReactionHtml = `
              <div class="reaction-container">
                <button class="reaction-button" data-problem-id="${simProblemUniqueId}" data-reaction-type="oshi">❤️</button>
                <span class="reaction-count">${simOshiCount}</span>
                <button class="reaction-button" data-problem-id="${simProblemUniqueId}" data-reaction-type="like">👍</button>
                <span class="reaction-count">${simLikeCount}</span>
                <button class="reaction-button" data-problem-id="${simProblemUniqueId}" data-reaction-type="fear">😱</button>
                <span class="reaction-count">${simFearCount}</span>
              </div>`;

                const isSimFavorite = state.favorites.includes(simProblemUniqueId);
                const simStarHtml = `<span class="star-icon ${isSimFavorite ? 'active' : ''}" data-problem-id="${simProblemUniqueId}">★</span>`;

                html += `
              <a href="${similarProblemLink}" target="_blank" class="problem-panel similar-item">
                <span class="similarity-badge">${(sim.similarity * 100).toFixed(1)}%</span>
                <div class="problem-number">${simStarHtml} 問題: ${s.問題番号}</div>
                <div class="problem-title">${s.問題名}</div>
                <div class="problem-source">出典: ${s.出典} ${simReactionHtml}</div>
                <div class="problem-meta">被参照: ${countsForThisCat[s.問題番号] || 0}回</div>
                ${simChecksHtml}
              </a>
            `;
            });
            html += `
              </div>
            </div>
          `;
        }
        card.innerHTML = html;
        container.appendChild(card);
    });

    // Event Listeners
    document.querySelectorAll('.similar-toggle').forEach(toggle => {
        toggle.addEventListener('click', () => {
            const content = toggle.nextElementSibling;
            const arrow = toggle.querySelector('.toggle-arrow');
            if (content.style.display === 'none' || content.style.display === '') {
                content.style.display = 'block';
                arrow.textContent = '▲';
            } else {
                content.style.display = 'none';
                arrow.textContent = '▼';
            }
        });
    });

    document.querySelectorAll('.check-box').forEach(box => {
        box.addEventListener('click', e => {
            e.preventDefault();
            e.stopPropagation();

            // Check if in read-only mode
            if (window.isReadOnlyMode) {
                showNotification('ログイン処理中です。しばらくお待ちください。', 2000, 'warning');
                return;
            }

            const problemId = e.target.dataset.problemId;
            const checkIndex = parseInt(e.target.dataset.checkIndex, 10);

            if (!state.problemChecks[problemId]) {
                state.problemChecks[problemId] = Array(4).fill(null).map(() => ({ checked: false, timestamp: null }));
            }

            const currentCheck = state.problemChecks[problemId][checkIndex];
            const newCheckedState = !currentCheck.checked;
            const newTimestamp = newCheckedState ? Date.now() : null;

            state.problemChecks[problemId][checkIndex] = {
                checked: newCheckedState,
                timestamp: newTimestamp
            };
            storage.saveChecks(state.problemChecks);

            document.querySelectorAll(`.check-box[data-problem-id="${problemId}"][data-check-index="${checkIndex}"]`).forEach(boxToUpdate => {
                if (newCheckedState) {
                    boxToUpdate.classList.add('checked', 'c' + checkIndex);
                } else {
                    boxToUpdate.classList.remove('checked', 'c' + checkIndex);
                }
            });

            const needsReview = shouldHighlightProblem(problemId, state.problemChecks);
            document.querySelectorAll(`.problem-card`).forEach(card => {
                const panel = card.querySelector(`.problem-panel[data-problem-id="${problemId}"]`);
                if (!panel) return;
                card.classList.toggle('needs-review', needsReview);
            });

            renderTotalReviewCount();
            renderTotalProgress();
        });
    });

    document.querySelectorAll('.reaction-button').forEach(button => {
        button.addEventListener('click', e => {
            e.preventDefault();
            e.stopPropagation();

            // Check if in read-only mode
            if (window.isReadOnlyMode) {
                showNotification('ログイン処理中です。しばらくお待ちください。', 2000, 'warning');
                return;
            }

            const problemId = e.target.dataset.problemId;
            const reactionType = e.target.dataset.reactionType;

            if (reactionType === 'oshi') {
                state.oshiCounts[problemId] = (state.oshiCounts[problemId] || 0) + 1;
                storage.saveOshiCounts(state.oshiCounts);
            } else if (reactionType === 'like') {
                state.likeCounts[problemId] = (state.likeCounts[problemId] || 0) + 1;
                storage.saveLikeCounts(state.likeCounts);
            } else if (reactionType === 'fear') {
                state.fearCounts[problemId] = (state.fearCounts[problemId] || 0) + 1;
                storage.saveFearCounts(state.fearCounts);
            }

            document.querySelectorAll(`.reaction-button[data-problem-id="${problemId}"][data-reaction-type="${reactionType}"]`).forEach(btnToUpdate => {
                const countElement = btnToUpdate.nextElementSibling;
                if (countElement && countElement.classList.contains('reaction-count')) {
                    countElement.textContent = (reactionType === 'oshi' ? state.oshiCounts[problemId] : reactionType === 'like' ? state.likeCounts[problemId] : state.fearCounts[problemId]);
                }
            });


            renderTotalReactions();
        });
    });

    document.querySelectorAll('.archive-button').forEach(button => {
        button.addEventListener('click', e => {
            e.preventDefault();
            e.stopPropagation();

            // Check if in read-only mode
            if (window.isReadOnlyMode) {
                showNotification('ログイン処理中です。しばらくお待ちください。', 2000, 'warning');
                return;
            }

            const problemId = e.target.dataset.problemId;
            const index = state.archivedProblemIds.indexOf(problemId);

            if (index > -1) {
                state.archivedProblemIds.splice(index, 1);
                showNotification("問題を復元しました");
            } else {
                state.archivedProblemIds.push(problemId);
                showNotification("問題をアーカイブしました");
            }

            storage.saveArchivedProblemIds(state.archivedProblemIds);
            window.dispatchEvent(new CustomEvent('archiveUpdated'));

            renderTotalProgress();
            renderProblemList(document.getElementById('detail-title').textContent);
        });
    });

    // Star Icon Click Listener
    document.querySelectorAll('.star-icon').forEach(star => {
        star.addEventListener('click', e => {
            e.preventDefault();
            e.stopPropagation();

            // Check if in read-only mode
            if (window.isReadOnlyMode) {
                showNotification('ログイン処理中です。しばらくお待ちください。', 2000, 'warning');
                return;
            }

            const problemId = e.target.dataset.problemId;
            const index = state.favorites.indexOf(problemId);

            if (index > -1) {
                state.favorites.splice(index, 1);
                e.target.classList.remove('active');
                showNotification("お気に入りから削除しました");
            } else {
                state.favorites.push(problemId);
                e.target.classList.add('active');
                showNotification("お気に入りに追加しました");
            }

            storage.saveFavorites(state.favorites);

            // Update all star icons for this problem
            document.querySelectorAll(`.star-icon[data-problem-id="${problemId}"]`).forEach(s => {
                if (state.favorites.includes(problemId)) {
                    s.classList.add('active');
                } else {
                    s.classList.remove('active');
                }
            });

            // If showing favorites only, re-render might be needed to remove un-favorited item
            if (state.showFavoritesOnly) {
                renderProblemList(document.getElementById('detail-title').textContent);
            }
        });
    });
}
