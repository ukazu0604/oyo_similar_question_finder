import { showDetail } from './ui-detail.js';
import { showIndex } from './ui-index.js';

export function initializeRouter() {
    window.addEventListener('popstate', e => {
        const hash = location.hash.substring(1);
        if (hash) {
            showDetail(decodeURIComponent(hash), true); // popstateからの呼び出しなのでtrue
        } else {
            showIndex(true);
        }
    });
}

export function navigateToDetail(cat, problemId = null) {
    console.log(`[履歴操作] history.pushStateを実行します。ハッシュ: #${encodeURIComponent(cat)}`);
    history.pushState({ category: cat, problemId: problemId }, `詳細: ${cat}`, `#${encodeURIComponent(cat)}`);
    showDetail(cat, false, problemId);
}

export function navigateToIndex() {
    // showIndex(false); // Usually called by back button which is handled by popstate or explicit click
    // If explicit click (like a "Home" button if we had one, or the back link which acts as history.back usually)
    // The original app had a back button that called showIndex().
    showIndex(false);
}
