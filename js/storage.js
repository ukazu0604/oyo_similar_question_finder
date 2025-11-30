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

    // Reaction counts
    loadOshiCounts: () => loadJSON('oyo_oshiCounts'),
    saveOshiCounts: (counts) => saveJSON('oyo_oshiCounts', counts),
    loadLikeCounts: () => loadJSON('oyo_likeCounts'),
    saveLikeCounts: (counts) => saveJSON('oyo_likeCounts', counts),
    loadFearCounts: () => loadJSON('oyo_fearCounts'),
    saveFearCounts: (counts) => saveJSON('oyo_fearCounts', counts),

    // Favorites (New)
    loadFavorites: () => loadJSON('oyo_favorites', []),
    saveFavorites: (favorites) => saveJSON('oyo_favorites', favorites),

    // Problem check state
    loadChecks: () => loadJSON('oyo_problemChecks'),
    saveChecks: (checks) => saveJSON('oyo_problemChecks', checks),

    // Archived problems
    loadArchivedProblemIds: () => loadJSON('oyo_archivedProblemIds', []),
    saveArchivedProblemIds: (ids) => saveJSON('oyo_archivedProblemIds', ids),

    // UI state
    loadSortOrder: (defaultValue) => load('oyo_currentSortOrder', defaultValue),
    saveSortOrder: (order) => save('oyo_currentSortOrder', order),
    loadShowUntouchedOnly: () => load('oyo_showUntouchedOnly') === 'true',
    saveShowUntouchedOnly: (value) => save('oyo_showUntouchedOnly', value),
    loadShowArchivedOnly: () => load('oyo_showArchivedOnly') === 'true',
    saveShowArchivedOnly: (value) => save('oyo_showArchivedOnly', value),
    loadShowFavoritesOnly: () => load('oyo_showFavoritesOnly') === 'true',
    saveShowFavoritesOnly: (value) => save('oyo_showFavoritesOnly', value),

    // Accordion state for major categories
    isMajorCatCollapsed: (largeCat) => load(`oyo_majorCatCollapsed-${largeCat}`) !== 'false',
    setMajorCatCollapsed: (largeCat, isCollapsed) => save(`oyo_majorCatCollapsed-${largeCat}`, isCollapsed),

    // Exam Date (New)
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

    // Helper to get current userId
    getCurrentUserId: () => load('oyo_userId', ''), // From saveGasConfig

    // Last Sync Time
    loadLastSyncTime: () => load('oyo_lastSyncTime'),
    saveLastSyncTime: (timestamp) => localStorage.setItem('oyo_lastSyncTime', timestamp), // Direct save to avoid triggering sync

    // Reset
    resetAll: () => {
        remove('oyo_problemChecks');
        remove('oyo_oshiCounts');
        remove('oyo_likeCounts');
        remove('oyo_fearCounts');
        remove('oyo_favorites');
        remove('oyo_archivedProblemIds');
        remove('oyo_dataVersion'); // Also reset version
        // Keep auth and config
    },

    // Cloud Sync (GAS)
    saveGasConfig: (url, userId) => {
        save('oyo_gasUrl', url);
        save('oyo_userId', userId);
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
            const data = response.data || {};
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

            return data; // Return only data part for backward compatibility with existing callers
        } finally {
            isSuppressingEvents = false; // Stop suppressing events
            dispatchStorageChangeEvent('bulk_update'); // Dispatch one event after bulk update
        }
    }
};
