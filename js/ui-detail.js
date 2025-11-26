import { state } from './state.js';
import { storage } from './storage.js';
import { isMobileDevice, shouldHighlightProblem, isProblemUntouched } from './utils.js';
import { renderTotalReactions, renderTotalProgress, renderTotalReviewCount } from './ui-common.js';

export function showDetail(middleCat, isPopState = false) {
    const indexView = document.getElementById('index-view');
    const detailView = document.getElementById('detail-view');

    indexView.style.display = 'none';
    detailView.style.display = 'block';
    document.getElementById('detail-title').textContent = middleCat;

    // ページ上部にスクロール
    if (!isPopState) { // popstateからの呼び出しでない場合のみスクロール
        window.scrollTo(0, 0);
    }
    const container = document.getElementById('detail-container');
    container.innerHTML = '';

    // 表示中の中分類に対応するカウント結果を取得
    // const countsForThisCat = state.referenceCounts[middleCat] || {}; // renderProblemListで取得するのでここでは不要

    // 要件1-2: 復習項目があれば自動で「復習優先」にソート
    const problemsForCheck = state.data.categories[middleCat];
    const hasReviewItems = problemsForCheck.some(item => {
        const problemId = `${item.main_problem.出典}-${item.main_problem.問題番号}`;
        return shouldHighlightProblem(problemId, state.problemChecks);
    });

    if (hasReviewItems) {
        state.currentSortOrder = 'review-first';
        // 要件1-3: デバッグログ出力
        console.log(`[自動並び順変更] カテゴリ「${middleCat}」に復習項目があるため、並び順を「復習優先」に変更しました。`);
    } else {
        // 復習項目がない場合は、storageに保存された（またはデフォルトの）並び順を適用
        state.currentSortOrder = storage.loadSortOrder('default');
        console.log(`[並び順適用] カテゴリ「${middleCat}」に復習項目がないため、保存された設定「${state.currentSortOrder}」を適用します。`);
    }
    // ドロップダウンの表示を現在の並び順に合わせる
    document.getElementById('sort-order').value = state.currentSortOrder;

    // isPopState（リロードやブラウザバック）の場合のみstorageから状態を復元
    // 通常の画面遷移ではリセットする
    if (isPopState) {
        state.showUntouchedOnly = storage.loadShowUntouchedOnly();
        console.log(`[状態復元] リロードのため、「未着手のみ表示」の状態(${state.showUntouchedOnly})をstorageから復元しました。`);
    } else {
        state.showUntouchedOnly = false;
        console.log(`[状態リセット] 画面遷移のため、「未着手のみ表示」の状態をリセットしました。`);
    }

    renderProblemList(middleCat);

    // 「未着手のみ表示」チェックボックスのイベントリスナーを（再）設定
    const untouchedCheckbox = document.getElementById('show-untouched-only');
    // 既存のリスナーを削除して重複を防ぐ
    untouchedCheckbox.replaceWith(untouchedCheckbox.cloneNode(true));
    document.getElementById('show-untouched-only').addEventListener('change', e => {
        state.showUntouchedOnly = e.target.checked;
        storage.saveShowUntouchedOnly(state.showUntouchedOnly); // 状態を保存
        console.log(`[フィルター変更] 未着手のみ表示: ${state.showUntouchedOnly}`);
        renderProblemList(middleCat);
    });
    // 状態を復元
    document.getElementById('show-untouched-only').checked = state.showUntouchedOnly;
}

export function renderProblemList(middleCat) {
    let problems = [...state.data.categories[middleCat]]; // ソートやフィルタリングのためにコピーを作成
    const countsForThisCat = state.referenceCounts[middleCat] || {};

    // 「未着手のみ表示」フィルターを適用
    if (state.showUntouchedOnly) {
        problems = problems.filter(item => isProblemUntouched(item, state.problemChecks));
    }
    // 選択された並び順に応じてソート
    if (state.currentSortOrder === 'review-first') {
        problems.sort((a, b) => {
            const aId = `${a.main_problem.出典}-${a.main_problem.問題番号}`;
            const bId = `${b.main_problem.出典}-${b.main_problem.問題番号}`;
            const aNeedsReview = shouldHighlightProblem(aId, state.problemChecks);
            const bNeedsReview = shouldHighlightProblem(bId, state.problemChecks);

            if (aNeedsReview !== bNeedsReview) {
                return bNeedsReview - aNeedsReview; // true (1) が先に来るように降順ソート
            }
            return a.main_problem.問題番号 - b.main_problem.問題番号; // 復習ステータスが同じ場合は問題番号順
        });
    } else if (state.currentSortOrder === 'ref-desc') {
        problems.sort((a, b) => {
            const countA = countsForThisCat[a.main_problem.問題番号] || 0;
            const countB = countsForThisCat[b.main_problem.問題番号] || 0;
            return countB - countA; // 降順
        });
    } else if (state.currentSortOrder === 'oshi-desc') {
        problems.sort((a, b) => {
            const countA = state.oshiCounts[`${a.main_problem.出典}-${a.main_problem.問題番号}`] || 0;
            const countB = state.oshiCounts[`${b.main_problem.出典}-${b.main_problem.問題番号}`] || 0;
            return countB - countA; // 降順
        });
    } else if (state.currentSortOrder === 'like-desc') {
        problems.sort((a, b) => {
            const countA = state.likeCounts[`${a.main_problem.出典}-${a.main_problem.問題番号}`] || 0;
            const countB = state.likeCounts[`${b.main_problem.出典}-${b.main_problem.問題番号}`] || 0;
            return countB - countA; // 降順
        });
    } else if (state.currentSortOrder === 'fear-desc') {
        problems.sort((a, b) => {
            const countA = state.fearCounts[`${a.main_problem.出典}-${a.main_problem.問題番号}`] || 0;
            const countB = state.fearCounts[`${b.main_problem.出典}-${b.main_problem.問題番号}`] || 0;
            return countB - countA; // 降順
        });
    } else { // default
        problems.sort((a, b) => {
            // 問題番号が数値なので、数値として比較する
            return a.main_problem.問題番号 - b.main_problem.問題番号; // 昇順
        });
    }

    const container = document.getElementById('detail-container');
    container.innerHTML = '';
    problems.forEach(item => {
        const main = item.main_problem;
        let mainProblemLink = main.リンク;
        if (isMobileDevice()) {
            // スマートフォン版のURLに変換
            mainProblemLink = mainProblemLink.replace('https://www.ap-siken.com/', 'https://www.ap-siken.com/s/');
        }

        const card = document.createElement('div');

        const mainProblemUniqueId = `${main.出典}-${main.問題番号}`;

        // ハイライト判定
        const needsReview = shouldHighlightProblem(mainProblemUniqueId, state.problemChecks);

        // チェックボックスのHTMLを生成
        let checksHtml = '<div class="check-container">';
        for (let i = 0; i < 4; i++) {
            const checkData = state.problemChecks[mainProblemUniqueId]?.[i];
            const isChecked = checkData && checkData.checked;
            checksHtml += `<div class="check-box ${isChecked ? 'checked c' + i : ''}" data-problem-id="${mainProblemUniqueId}" data-check-index="${i}"></div>`;
        }
        checksHtml += '</div>';

        // リアクションボタンのHTMLを生成
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

        card.className = `problem-card ${needsReview ? 'needs-review' : ''}`;
        let html = `
          <a href="${mainProblemLink}" target="_blank" class="problem-panel main-problem">
            <div class="problem-number">問題: ${main.問題番号}</div>
            <div class="problem-title">${main.問題名}</div>
            <div class="problem-source">出典: ${main.出典} ${reactionHtml}</div>
            ${checksHtml}
          </a>
        `;
        // 類似度が50%以上のものだけをフィルタリング
        const filteredSimilars = item.similar_problems
            ? item.similar_problems.filter(sim => sim.similarity >= 0.5)
            : [];

        if (filteredSimilars.length > 0) {
            const similarCount = filteredSimilars.length;
            // 平均類似度を計算
            const totalSimilarity = filteredSimilars.reduce((sum, sim) => sum + sim.similarity, 0);
            const averageSimilarity = (totalSimilarity / similarCount) * 100;

            html += `
            <div class="similar-section">
              <div class="similar-toggle">
                <span class="similar-title">📊 類似問題 (${similarCount > 5 ? '上位5' : similarCount}件)</span>
                <span class="average-similarity">平均: ${averageSimilarity.toFixed(1)}%</span>
                <span class="toggle-arrow">▼</span> <!-- 矢印を右端に -->
              </div>
              <div class="similar-content" style="display: none;">
          `;
            filteredSimilars.slice(0, 5).forEach(sim => {
                const s = sim.data;
                let similarProblemLink = s.リンク;
                if (isMobileDevice()) {
                    // スマートフォン版のURLに変換
                    similarProblemLink = similarProblemLink.replace('https://www.ap-siken.com/', 'https://www.ap-siken.com/s/');
                }

                // 類似問題用のチェックボックスHTMLを生成
                const simProblemUniqueId = `${s.出典}-${s.問題番号}`;
                let simChecksHtml = '<div class="check-container">';
                for (let i = 0; i < 4; i++) {
                    const isChecked = state.problemChecks[simProblemUniqueId]?.[i]?.checked;
                    simChecksHtml += `<div class="check-box ${isChecked ? 'checked c' + i : ''}" data-problem-id="${simProblemUniqueId}" data-check-index="${i}"></div>`;
                }
                simChecksHtml += '</div>';

                // 類似問題用のリアクションボタンHTMLを生成
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

                html += `
              <a href="${similarProblemLink}" target="_blank" class="problem-panel similar-item">
                <span class="similarity-badge">${(sim.similarity * 100).toFixed(1)}%</span>
                <div class="problem-number">問題: ${s.問題番号}</div>
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

    // 新しく生成したアコーディオン要素にイベントリスナーを設定
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

    // 新しく生成したチェックボックスにイベントリスナーを設定
    document.querySelectorAll('.check-box').forEach(box => {
        box.addEventListener('click', e => {
            e.preventDefault(); // aタグのリンク遷移を防止
            e.stopPropagation(); // 親要素へのイベント伝播を停止

            const problemId = e.target.dataset.problemId;
            const checkIndex = parseInt(e.target.dataset.checkIndex, 10);

            // チェック状態の初期化
            if (!state.problemChecks[problemId]) {
                state.problemChecks[problemId] = Array(4).fill(null).map(() => ({ checked: false, timestamp: null }));
            }

            // 状態をトグル
            const currentCheck = state.problemChecks[problemId][checkIndex];
            const newCheckedState = !currentCheck.checked;

            const newTimestamp = newCheckedState ? Date.now() : null;
            if (newTimestamp) {
                console.log(`[Check ON] Problem: ${problemId}, Index: ${checkIndex}, Timestamp: ${new Date(newTimestamp).toLocaleString()}`);
            }

            state.problemChecks[problemId][checkIndex] = {
                checked: newCheckedState,
                timestamp: newTimestamp
            };
            storage.saveChecks(state.problemChecks); // 変更を保存

            // 画面に表示されている同じ問題IDとインデックスを持つすべてのチェックボックスの表示を更新
            document.querySelectorAll(`.check-box[data-problem-id="${problemId}"][data-check-index="${checkIndex}"]`).forEach(boxToUpdate => {
                if (newCheckedState) {
                    boxToUpdate.classList.add('checked', 'c' + checkIndex);
                } else {
                    boxToUpdate.classList.remove('checked', 'c' + checkIndex);
                }
            });

            // ハイライト状態もリアルタイムで更新
            const needsReview = shouldHighlightProblem(problemId, state.problemChecks);
            document.querySelectorAll(`.problem-card`).forEach(card => {
                const panel = card.querySelector(`.problem-panel[data-problem-id="${problemId}"]`);
                if (!panel) return; // 関係ないカードはスキップ
                card.classList.toggle('needs-review', needsReview);
            });

            // 全体の復習数のみ更新（トップページに戻った時にカテゴリ一覧は再描画される）
            renderTotalReviewCount();
            renderTotalProgress();
            // 「未着手のみ表示」がONの場合、リストを再描画して着手済みの項目を消す
            // if (showUntouchedOnly) renderProblemList(document.getElementById('detail-title').textContent);
        });
    });

    // 新しく生成したリアクションボタンにイベントリスナーを設定
    document.querySelectorAll('.reaction-button').forEach(button => {
        button.addEventListener('click', e => {
            e.preventDefault(); // aタグのリンク遷移を防止
            e.stopPropagation(); // 親要素へのイベント伝播を停止

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

            // 画面に表示されている同じ問題IDを持つすべてのカウント表示を更新
            document.querySelectorAll(`.reaction-button[data-problem-id="${problemId}"][data-reaction-type="${reactionType}"]`).forEach(btnToUpdate => {
                const countElement = btnToUpdate.nextElementSibling;
                if (countElement && countElement.classList.contains('reaction-count')) {
                    countElement.textContent = (reactionType === 'oshi' ? state.oshiCounts[problemId] : reactionType === 'like' ? state.likeCounts[problemId] : state.fearCounts[problemId]);
                }
            });

            // 全体の合計数も更新
            renderTotalReactions();
        });
    });
}
