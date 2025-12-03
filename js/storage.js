// js/storage.js
import { saveUserData, loadUserData } from './api.js';

// Generic helper functions
let isSuppressingEvents = false; // Flag to suppress events during bulk operations

function loadJSON(key, defaultValue = {}) {
    const stored = localStorage.getItem(key);
    return stored ? JSON.parse(stored) : defaultValue;
}

// Helper to dispatch storage change event
function dispatchStorageChangeEvent(key) {
    if (!isSuppressingEvents) { // Only dispatch if not suppressing
        const event = new CustomEvent('storageChanged', { detail: { key: key } });
        window.dispatchEvent(event);
    }
}

function saveJSON(key, value) {
    localStorage.setItem(key, JSON.stringify(value));
    dispatchStorageChangeEvent(key); // Dispatch event after saving
}

function load(key, defaultValue = null) {
    return localStorage.getItem(key) ?? defaultValue;
}

function save(key, value) {
    localStorage.setItem(key, value);
    dispatchStorageChangeEvent(key); // Dispatch event after saving
}

// ★追加: イベントを発火させずに保存（UI状態用）
function saveSilent(key, value) {
    localStorage.setItem(key, value);
    // イベントを発火しない
}

function remove(key) {
    localStorage.removeItem(key);
}

// Specific data accessors
export const storage = {
    // Auth
    get accessToken() {
        return load('oyo_accessToken');
    },
    set accessToken(token) {
        if (token) save('oyo_accessToken', token);
        else remove('oyo_accessToken');
    },
    get refreshToken() {
        return load('oyo_refreshToken');
    },
    set refreshToken(token) {
        if (token) save('oyo_refreshToken', token);
        else remove('oyo_refreshToken');
    },

    // Data Version for optimistic locking
    get dataVersion() {
        return parseInt(load('oyo_dataVersion') || '0');
    },
    set dataVersion(version) {
        localStorage.setItem('oyo_dataVersion', version.toString()); // Direct localStorage access to prevent event loop
    },

    // Helper to get current userId
    getCurrentUserId: () => load('oyo_userId', ''), // From saveGasConfig

    // Reaction counts (ユーザーID紐付け)
    loadOshiCounts: () => {
        const userId = storage.getCurrentUserId();
        const key = userId ? `oyo_oshiCounts_${userId}` : 'oyo_oshiCounts_default';
        return loadJSON(key);
    },
    saveOshiCounts: (counts) => {
        const userId = storage.getCurrentUserId();
        const key = userId ? `oyo_oshiCounts_${userId}` : 'oyo_oshiCounts_default';
        saveJSON(key, counts);
    },
    loadLikeCounts: () => {
        const userId = storage.getCurrentUserId();
        const key = userId ? `oyo_likeCounts_${userId}` : 'oyo_likeCounts_default';
        return loadJSON(key);
    },
    saveLikeCounts: (counts) => {
        const userId = storage.getCurrentUserId();
        const key = userId ? `oyo_likeCounts_${userId}` : 'oyo_likeCounts_default';
        saveJSON(key, counts);
    },
    loadFearCounts: () => {
        const userId = storage.getCurrentUserId();
        const key = userId ? `oyo_fearCounts_${userId}` : 'oyo_fearCounts_default';
        return loadJSON(key);
    },
    saveFearCounts: (counts) => {
        const userId = storage.getCurrentUserId();
        const key = userId ? `oyo_fearCounts_${userId}` : 'oyo_fearCounts_default';
        saveJSON(key, counts);
    },

    // Favorites (ユーザーID紐付け)
    loadFavorites: () => {
        const userId = storage.getCurrentUserId();
        const key = userId ? `oyo_favorites_${userId}` : 'oyo_favorites_default';
        return loadJSON(key, []);
    },
    saveFavorites: (favorites) => {
        const userId = storage.getCurrentUserId();
        const key = userId ? `oyo_favorites_${userId}` : 'oyo_favorites_default';
        saveJSON(key, favorites);
    },

    // Problem check state (ユーザーID紐付け)
    loadChecks: () => {
        const userId = storage.getCurrentUserId();
        const key = userId ? `oyo_problemChecks_${userId}` : 'oyo_problemChecks_default';
        return loadJSON(key);
    },
    saveChecks: (checks) => {
        const userId = storage.getCurrentUserId();
        const key = userId ? `oyo_problemChecks_${userId}` : 'oyo_problemChecks_default';
        saveJSON(key, checks);
    },

    // Archived problems (ユーザーID紐付け)
    loadArchivedProblemIds: () => {
        const userId = storage.getCurrentUserId();
        const key = userId ? `oyo_archivedProblemIds_${userId}` : 'oyo_archivedProblemIds_default';
        return loadJSON(key, []);
    },
    saveArchivedProblemIds: (ids) => {
        const userId = storage.getCurrentUserId();
        const key = userId ? `oyo_archivedProblemIds_${userId}` : 'oyo_archivedProblemIds_default';
        saveJSON(key, ids);
    },

    // UI state (ユーザーID紐付け)
    loadSortOrder: (defaultValue) => {
        const userId = storage.getCurrentUserId();
        const key = userId ? `oyo_currentSortOrder_${userId}` : 'oyo_currentSortOrder_default';
        return load(key, defaultValue);
    },
    saveSortOrder: (order) => {
        const userId = storage.getCurrentUserId();
        const key = userId ? `oyo_currentSortOrder_${userId}` : 'oyo_currentSortOrder_default';
        save(key, order);
    },
    loadShowUntouchedOnly: () => load('oyo_showUntouchedOnly') === 'true',
    saveShowUntouchedOnly: (value) => saveSilent('oyo_showUntouchedOnly', value), // UI状態なので同期不要
    loadShowArchivedOnly: () => load('oyo_showArchivedOnly') === 'true',
    saveShowArchivedOnly: (value) => saveSilent('oyo_showArchivedOnly', value), // UI状態なので同期不要
    loadShowFavoritesOnly: () => load('oyo_showFavoritesOnly') === 'true',
    saveShowFavoritesOnly: (value) => saveSilent('oyo_showFavoritesOnly', value), // UI状態なので同期不要

    // Accordion state for major categories
    isMajorCatCollapsed: (largeCat) => load(`oyo_majorCatCollapsed-${largeCat}`) !== 'false',
    setMajorCatCollapsed: (largeCat, isCollapsed) => saveSilent(`oyo_majorCatCollapsed-${largeCat}`, isCollapsed), // UI状態なので同期不要

    // Exam Date (ユーザーID紐付け)
    loadExamDate: () => {
        const userId = storage.getCurrentUserId();
        const key = userId ? `oyo_examDate_${userId}` : 'oyo_examDate_default'; // User-specific key or default
        return load(key);
    },
    saveExamDate: (date) => {
        const userId = storage.getCurrentUserId();
        const key = userId ? `oyo_examDate_${userId}` : 'oyo_examDate_default'; // User-specific key or default
        save(key, date);
    },

    // Last Sync Time
    loadLastSyncTime: () => load('oyo_lastSyncTime'),
    saveLastSyncTime: (timestamp) => localStorage.setItem('oyo_lastSyncTime', timestamp), // Direct save to avoid triggering sync

    // Reset (ユーザーID紐付け)
    resetAll: () => {
        const userId = storage.getCurrentUserId();
        const check_key = userId ? `oyo_problemChecks_${userId}` : 'oyo_problemChecks_default';
        const oshi_key = userId ? `oyo_oshiCounts_${userId}` : 'oyo_oshiCounts_default';
        const like_key = userId ? `oyo_likeCounts_${userId}` : 'oyo_likeCounts_default';
        const fear_key = userId ? `oyo_fearCounts_${userId}` : 'oyo_fearCounts_default';
        const fav_key = userId ? `oyo_favorites_${userId}` : 'oyo_favorites_default';
        const archived_key = userId ? `oyo_archivedProblemIds_${userId}` : 'oyo_archivedProblemIds_default';

        remove(check_key);
        remove(oshi_key);
        remove(like_key);
        remove(fear_key);
        remove(fav_key);
        remove(archived_key);
        remove('oyo_dataVersion'); // Also reset version
        // Keep auth and config
    },

    // Cloud Sync (GAS)
    saveGasConfig: (url, userId) => {
        const oldUserId = load('oyo_userId', ''); // Get current userId before saving new one
        save('oyo_gasUrl', url);
        save('oyo_userId', userId);

        // Migrate sort order from default to user-specific if necessary
        const defaultSortKey = 'oyo_currentSortOrder_default';
        const userSortKey = `oyo_currentSortOrder_${userId}`;
        
        const defaultSortOrder = localStorage.getItem(defaultSortKey);
        const userSortOrder = localStorage.getItem(userSortKey);

        if (defaultSortOrder && !userSortOrder) {
            // If a default sort order exists and no user-specific one, migrate it
            localStorage.setItem(userSortKey, defaultSortOrder);
            localStorage.removeItem(defaultSortKey);
            console.log(`Migrated sort order from default to user ${userId}`);
        }
    },
    loadGasConfig: () => ({
        url: load('oyo_gasUrl', ''),
        userId: load('oyo_userId', '')
    }),

    syncWithCloud: async () => {
        // 1. Load current local data
        const localData = {
            checks: storage.loadChecks(),
            oshi: storage.loadOshiCounts(),
            like: storage.loadLikeCounts(),
            fear: storage.loadFearCounts(),
            favorites: storage.loadFavorites(),
            archived: storage.loadArchivedProblemIds(),
            examDate: storage.loadExamDate()
        };

        // 2. Send to GAS with current data version
        const result = await saveUserData(localData, storage.dataVersion);
        if (result.success && result.version !== undefined) {
            storage.dataVersion = result.version; // Update local version after successful save
            storage.saveLastSyncTime(new Date().toISOString()); // Save sync timestamp
        }
        return result;
    },

    loadFromCloud: async () => {
        isSuppressingEvents = true; // Start suppressing events
        try {
            // 1. Fetch from GAS
            const response = await loadUserData(); // Now returns {data, version}
            const data = response.version !== undefined ? response.data : response; // Handle old and new API response
            const version = response.version || 0;

            // 2. Update local storage
            if (data.checks) storage.saveChecks(data.checks);
            if (data.oshi) storage.saveOshiCounts(data.oshi);
            if (data.like) storage.saveLikeCounts(data.like);
            if (data.fear) storage.saveFearCounts(data.fear);
            if (data.favorites) storage.saveFavorites(data.favorites);
            if (data.archived) storage.saveArchivedProblemIds(data.archived);
            if (data.examDate !== undefined && data.examDate !== null) storage.saveExamDate(data.examDate);

            storage.dataVersion = version; // Update local version after successful load
            storage.saveLastSyncTime(new Date().toISOString()); // Save sync timestamp

            return data;
        } finally {
            isSuppressingEvents = false; // Stop suppressing events
            dispatchStorageChangeEvent('bulk_update'); // Dispatch one event after bulk update
        }
    }
};