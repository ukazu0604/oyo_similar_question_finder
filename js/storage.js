// js/storage.js

// Generic helper functions
function loadJSON(key, defaultValue = {}) {
    const stored = localStorage.getItem(key);
    return stored ? JSON.parse(stored) : defaultValue;
}

function saveJSON(key, value) {
    localStorage.setItem(key, JSON.stringify(value));
}

function load(key, defaultValue = null) {
    return localStorage.getItem(key) ?? defaultValue;
}

function save(key, value) {
    localStorage.setItem(key, value);
}

function remove(key) {
    localStorage.removeItem(key);
}

// Specific data accessors
export const storage = {
    // Reaction counts
    loadOshiCounts: () => loadJSON('oyo_oshiCounts'),
    saveOshiCounts: (counts) => saveJSON('oyo_oshiCounts', counts),
    loadLikeCounts: () => loadJSON('oyo_likeCounts'),
    saveLikeCounts: (counts) => saveJSON('oyo_likeCounts', counts),
    loadFearCounts: () => loadJSON('oyo_fearCounts'),
    saveFearCounts: (counts) => saveJSON('oyo_fearCounts', counts),

    // Problem check state
    loadChecks: () => loadJSON('oyo_problemChecks'),
    saveChecks: (checks) => saveJSON('oyo_problemChecks', checks),

    // UI state
    loadSortOrder: (defaultValue) => load('oyo_currentSortOrder', defaultValue),
    saveSortOrder: (order) => save('oyo_currentSortOrder', order),
    loadShowUntouchedOnly: () => load('oyo_showUntouchedOnly') === 'true',
    saveShowUntouchedOnly: (value) => save('oyo_showUntouchedOnly', value),

    // Accordion state for major categories
    isMajorCatCollapsed: (largeCat) => load(`oyo_majorCatCollapsed-${largeCat}`) !== 'false',
    setMajorCatCollapsed: (largeCat, isCollapsed) => save(`oyo_majorCatCollapsed-${largeCat}`, isCollapsed),

    // Reset
    resetAll: () => {
        remove('oyo_problemChecks');
        remove('oyo_oshiCounts');
        remove('oyo_likeCounts');
        remove('oyo_fearCounts');
    }
};
