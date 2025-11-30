import { storage } from './storage.js';

export const state = {
    data: {},
    referenceCounts: {},
    oshiCounts: {},
    likeCounts: {},
    fearCounts: {},
    problemChecks: {},
    archivedProblemIds: [], // アーカイブされた問題IDのリスト
    favorites: [], // お気に入り（スター）の問題IDリスト
    currentSortOrder: 'default',
    showUntouchedOnly: false,
    showArchivedOnly: false, // アーカイブ済み問題の表示フラグ
    showFavoritesOnly: false, // お気に入り問題の表示フラグ
    examDate: null // 試験日
};

export function initState() {
    state.currentSortOrder = storage.loadSortOrder('default');
    state.oshiCounts = storage.loadOshiCounts();
    state.likeCounts = storage.loadLikeCounts();
    state.fearCounts = storage.loadFearCounts();
    state.archivedProblemIds = storage.loadArchivedProblemIds();
    state.favorites = storage.loadFavorites();
    state.examDate = storage.loadExamDate();

    const loadedChecks = storage.loadChecks();
    const { migratedChecks, needsSave } = migrateChecks(loadedChecks);
    state.problemChecks = migratedChecks;
    if (needsSave) {
        storage.saveChecks(state.problemChecks); // 移行が発生した場合のみ保存
    }
}

// 古いデータ構造（ブール値の配列）からの移行処理
function migrateChecks(checks) {
    let needsSave = false;
    for (const problemId in checks) {
        if (Array.isArray(checks[problemId]) && typeof checks[problemId][0] === 'boolean') {
            needsSave = true;
            checks[problemId] = checks[problemId].map(isChecked => ({
                checked: isChecked,
                timestamp: isChecked ? Date.now() : null // 古いデータはとりあえず今の時刻で
            }));
        }
    }
    return { migratedChecks: checks, needsSave };
}
