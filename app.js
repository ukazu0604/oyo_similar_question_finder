import { initState, state } from './js/state.js';
import { loadData } from './js/api.js';
import { initializeRouter } from './js/router.js';
import { renderTotalReactions, renderTotalProgress, renderTotalReviewCount } from './js/ui-common.js';
import { renderIndex, showIndex } from './js/ui-index.js';
import { showDetail, renderProblemList } from './js/ui-detail.js';
import { storage } from './js/storage.js';

(async () => {
    const modelInfo = document.getElementById('model-info');

    async function initializePage() {
        try {
            initState(); // Load state from storage
            await loadData(); // Load data from JSON

            modelInfo.textContent = `使用モデル: ${state.data.model || 'N/A'}`;

            renderTotalReactions();
            renderTotalReviewCount();
            renderTotalProgress();

            initializeRouter();

            // 初期読み込み時にハッシュがあれば詳細ページを表示
            const initialHash = location.hash.substring(1);
            if (initialHash) {
                renderTotalProgress(); // 詳細ページ直アクセスでもプログレスバーは表示
                showDetail(decodeURIComponent(initialHash), true); // リロード時はスクロール位置を復元するため isPopState=true
            } else {
                // 初期表示がトップページの場合
                renderIndex(state.data.categories);

                // 復習項目までスクロール
                setTimeout(() => {
                    const firstReviewCategory = document.querySelector('.middle-category-link.has-review-items');
                    if (firstReviewCategory) {
                        firstReviewCategory.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                }, 100);
            }

        } catch (e) {
            modelInfo.textContent = 'データ読み込みエラー';
            console.error(e);
        }
    }

    // Global event listeners
    document.getElementById('back-button').addEventListener('click', e => {
        e.preventDefault();
        history.pushState(null, null, ' '); // Clear hash
        showIndex();
    });

    document.getElementById('reset-storage-button').addEventListener('click', () => {
        if (confirm('本当にすべてのチェック状態とリアクションをリセットしますか？')) {
            storage.resetAll();
            alert('リセットしました。ページをリロードします。');
            location.reload();
        }
    });

    document.getElementById('sort-order').addEventListener('change', e => {
        state.currentSortOrder = e.target.value;
        storage.saveSortOrder(state.currentSortOrder);

        const currentCat = document.getElementById('detail-title').textContent;
        if (currentCat) {
            renderProblemList(currentCat);
        }
    });

    initializePage();
})();
