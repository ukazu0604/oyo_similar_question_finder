import { initState, state } from './js/state.js';
import { loadData, login, register, validate, refreshAccessToken, clearUserData } from './js/api.js?v=1';
import { initializeRouter } from './js/router.js';
import { renderTotalReactions, renderTotalProgress, renderTotalReviewCount, renderExamCountdown, showNotification } from './js/ui-common.js';
import { renderIndex, showIndex } from './js/ui-index.js';
import { showDetail, renderProblemList } from './js/ui-detail.js';
import { storage } from './js/storage.js';

// Helper function to format sync time
function formatSyncTime(isoString) {
    if (!isoString) return '';
    const date = new Date(isoString);
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    return ` (同期時刻: ${hours}:${minutes})`;
}

window.addEventListener('DOMContentLoaded', async () => {
    const modelInfo = document.getElementById('model-info');
    const modelSelector = document.getElementById('model-selector');
    const currentUserDisplay = document.getElementById('current-user-display');
    const loadingOverlay = document.getElementById('loading-overlay');
    const loadingStatusText = document.getElementById('loading-status-text');

    // --- Step 1: Prepare static UI elements (like model selector) ---
    async function prepareStaticUI() {
        let models = [];
        try {
            const res = await fetch('03_html_output/models.json');
            models = res.ok ? await res.json() : [{ id: 'similar_results.json', name: 'Default (Fallback)' }];
        } catch (e) {
            console.error('Failed to load models.json:', e);
            models = [{ id: 'similar_results.json', name: 'Default (Fallback)' }];
        }

        modelSelector.innerHTML = '';
        models.forEach(model => {
            const option = document.createElement('option');
            option.value = model.id;
            option.textContent = model.name;
            modelSelector.appendChild(option);
        });

        const savedModel = localStorage.getItem('selectedModel');
        if (savedModel && models.some(m => m.id === savedModel)) {
            modelSelector.value = savedModel;
        }
        console.log("Static UI prepared.");
    }

    // --- Step 2a: Load core application data (the model itself) ---
    async function loadCoreData() {
        loadingStatusText.textContent = '問題データを読み込み中...';
        try {
            const selectedModelId = modelSelector.value;
            await loadData(selectedModelId);
        } catch (e) {
            modelInfo.textContent = 'データ読み込みエラー';
            console.error(e);
            throw new Error('Failed to load core data.');
        }
    }

    // --- Step 2b: Initialize user session and load user-specific data ---
    async function initializeUserSession() {
        let isAuthenticated = false;

        const accessToken = storage.accessToken;

        if (accessToken) {
            try {
                const res = await validate(accessToken);
                if (res.valid) {
                    isAuthenticated = true;
                    console.log("Access token is valid.");
                }
            } catch (e) {
                console.warn("Validation with access token failed, will try to refresh:", e.message);
            }
        }

        if (!isAuthenticated && storage.refreshToken) {
            console.log("Trying to refresh token...");
            try {
                const refreshResult = await refreshAccessToken();
                isAuthenticated = !!refreshResult;
            } catch (e) {
                console.error("Refreshing token failed:", e.message);
                isAuthenticated = false;
            }
        }

        if (isAuthenticated) {
            console.log("Session authenticated.");
            try {
                await storage.loadFromCloud();
                // Re-initialize state with cloud data
                initState();
                // Re-render UI to reflect cloud data
                const currentHash = location.hash.substring(1);
                if (currentHash) {
                    renderProblemList(decodeURIComponent(currentHash));
                } else {
                    renderIndex(state.data.categories);
                }
                renderTotalReactions();
                renderTotalReviewCount();
                renderTotalProgress();
            } catch (e) {
                console.error('Cloud data loading failed:', e.message);
            }
        } else {
            console.log("Session not authenticated.");
        }

        console.log("User session initialization finished.");

        return { isAuthenticated };
    }

    // --- Step 3: Render the final UI after all data is loaded ---
    function renderFinalUI() {
        loadingStatusText.textContent = 'UIを更新中...';
        modelInfo.textContent = `使用モデル: ${state.data.model || 'N/A'}`;

        renderTotalReactions();
        renderTotalReviewCount();
        renderTotalProgress();
        renderExamCountdown();

        initializeRouter();
        const initialHash = location.hash.substring(1);
        if (initialHash) {
            showDetail(decodeURIComponent(initialHash), true);
        } else {
            renderIndex(state.data.categories);
        }
        console.log("Final UI rendered.");
    }

    // --- Helper: Enable editing features after login ---
    function enableEditingFeatures() {
        // Remove read-only class from all interactive elements
        document.querySelectorAll('.check-box, .reaction-button, .archive-button, .star-icon').forEach(el => {
            el.classList.remove('read-only');
        });
        console.log("Editing features enabled.");
    }

    // --- Helper: Update user display ---
    function updateUserDisplay() {
        const config = storage.loadGasConfig();
        if (storage.accessToken && config.userId) {
            const lastSync = storage.loadLastSyncTime();
            const syncTimeText = lastSync ? formatSyncTime(lastSync) : '';
            currentUserDisplay.textContent = `User: ${config.userId}${syncTimeText}`;
        } else {
            currentUserDisplay.textContent = '';
        }
    }

    // --- Main Execution ---
    async function main() {
        await prepareStaticUI();

        const gasConfig = storage.loadGasConfig();
        if (!gasConfig || !gasConfig.url) {
            loadingOverlay.classList.remove('visible'); // loadingOverlayを非表示に
            syncModal.style.display = 'block'; // syncModalを表示
            gasUrlInput.value = ''; // gasUrlInputを空に
            syncStatus.textContent = 'GAS URLが設定されていません。同期設定を行ってください。'; // 警告メッセージ
            syncStatus.style.color = 'red';
            showNotification('GAS URLが設定されていません。', 5000, 'error');
            return; // main()関数の残りの処理をスキップ
        }

        loadingOverlay.classList.add('visible');

        try {
            // 1. Load core data first
            await loadCoreData();

            // 2. Initialize state with local data
            initState();

            // 3. Render UI immediately in read-only mode
            window.isReadOnlyMode = true;
            renderFinalUI();
            loadingOverlay.classList.remove('visible');

            // Add read-only class to all interactive elements
            document.querySelectorAll('.check-box, .reaction-button, .archive-button, .star-icon').forEach(el => {
                el.classList.add('read-only');
            });

            // Show notification that user can browse
            showNotification('問題を閲覧できます。ログイン処理中...', 3000, 'info');

            // 4. Authenticate in background
            const sessionResult = await initializeUserSession();

            // 5. Enable editing after authentication
            window.isReadOnlyMode = false;
            enableEditingFeatures();

            if (sessionResult.isAuthenticated) {
                updateUserDisplay();
                showNotification('ログイン完了！編集可能になりました。', 2000, 'success');
            } else {
                document.getElementById('login-modal').style.display = 'block';
                if (storage.refreshToken) {
                    showNotification('セッションが切れました。ログインすると編集できます。', 5000, 'warning');
                } else {
                    showNotification('ログインすると編集できます。', 3000, 'info');
                }
            }

            console.log("Initialization complete.");

        } catch (error) {
            console.error("Initialization failed:", error);
            alert('アプリケーションの初期化に失敗しました。ページをリロードしてください。');
        } finally {
            window.state = state;
            window.storage = storage;
            window.clearUserData = clearUserData;
            window.appInitialized = true;
        }
    }

    main();

    // --- Event Listeners ---
    const loginModal = document.getElementById('login-modal');
    const authStatus = document.getElementById('auth-status');

    document.getElementById('auth-button').addEventListener('click', () => {
        if (storage.accessToken) {
            if (confirm('ログアウトしますか？')) {
                storage.accessToken = null;
                storage.refreshToken = null;
                currentUserDisplay.textContent = '';
                showNotification('ログアウトしました。ページをリロードします。', 2000, 'info');
                setTimeout(() => location.reload(), 1000);
            }
        } else {
            loginModal.style.display = 'block';
            authStatus.textContent = '';
        }
    });

    document.getElementById('close-login-modal').addEventListener('click', () => {
        loginModal.style.display = 'none';
    });

    window.addEventListener('click', (e) => {
        if (e.target === loginModal) {
            loginModal.style.display = 'none';
        }
    });

    document.getElementById('login-button').addEventListener('click', async () => {
        const userId = document.getElementById('login-user-id').value;
        const password = document.getElementById('login-password').value;
        authStatus.textContent = 'ログイン中...';
        authStatus.style.color = 'blue';

        try {
            const res = await login(userId, password);
            if (res.success) {
                storage.accessToken = res.accessToken;
                storage.refreshToken = res.refreshToken;
                storage.saveGasConfig(storage.loadGasConfig().url, res.userId); // Use userId from response
                authStatus.textContent = 'ログイン成功！';
                authStatus.style.color = 'green';
                currentUserDisplay.textContent = `User: ${res.userId}`; // Use userId from response
                setTimeout(() => {
                    loginModal.style.display = 'none';
                    showNotification('ログインしました。データを再読み込みします。', 2000, 'success');
                    location.reload();
                }, 1000);
            } else {
                authStatus.textContent = 'エラー: ' + (res.error || 'ログイン失敗');
                authStatus.style.color = 'red';
            }
        } catch (e) {
            authStatus.textContent = '通信エラー: ' + e.message;
            authStatus.style.color = 'red';
        }
    });

    document.getElementById('register-button').addEventListener('click', async () => {
        const userId = document.getElementById('login-user-id').value;
        const password = document.getElementById('login-password').value;
        authStatus.textContent = '登録中...';
        authStatus.style.color = 'blue';

        try {
            const res = await register(userId, password);
            if (res.success) {
                authStatus.textContent = '登録成功！ログインしてください。';
                authStatus.style.color = 'green';
            } else {
                authStatus.textContent = 'エラー: ' + (res.error || '登録失敗');
                authStatus.style.color = 'red';
            }
        } catch (e) {
            authStatus.textContent = '通信エラー: ' + e.message;
            authStatus.style.color = 'red';
        }
    });

    modelSelector.addEventListener('change', async (e) => {
        localStorage.setItem('selectedModel', e.target.value);
        location.reload();
    });

    document.getElementById('back-button').addEventListener('click', e => {
        e.preventDefault();
        history.pushState(null, null, ' '); // Clear hash
        showIndex();
    });

    document.getElementById('reset-storage-button').addEventListener('click', () => {
        if (confirm('本当にすべてのチェック状態とリアクションをリセットしますか？クラウドデータは削除されません。')) {
            storage.resetAll();
            alert('リセットしました。ページをリロードします。');
            location.reload();
        }
    });

    // --- Sync UI Logic ---
    const syncModal = document.getElementById('sync-modal');
    const gasUrlInput = document.getElementById('gas-url');
    const examDateInput = document.getElementById('exam-date');
    const syncStatus = document.getElementById('sync-status');

    document.getElementById('sync-settings-button').addEventListener('click', () => {
        const config = storage.loadGasConfig();
        gasUrlInput.value = config.url;
        examDateInput.value = storage.loadExamDate() || '';
        syncStatus.textContent = '';
        syncModal.style.display = 'block';
    });

    document.getElementById('close-sync-modal').addEventListener('click', () => {
        syncModal.style.display = 'none';
    });

    window.addEventListener('click', (e) => {
        if (e.target === syncModal) {
            syncModal.style.display = 'none';
        }
    });

    document.getElementById('save-sync-settings').addEventListener('click', async () => {
        const url = gasUrlInput.value.trim();
        const examDate = examDateInput.value;
        const currentConfig = storage.loadGasConfig();

        storage.saveGasConfig(url, currentConfig.userId);
        storage.saveExamDate(examDate);
        state.examDate = examDate;
        renderExamCountdown();

        syncStatus.textContent = '設定を保存しました。';
        syncStatus.style.color = 'green';

        // ★試験日変更後、すぐにクラウドに同期する
        if (storage.accessToken) { // ログインしている場合のみ同期
            syncStatus.textContent = '設定を保存しました。クラウドに同期中...';
            try {
                await storage.syncWithCloud();
                syncStatus.textContent = '設定を保存し、クラウドに同期しました！リロードします...';
                syncStatus.style.color = 'green';
            } catch (e) {
                syncStatus.textContent = '設定は保存しましたが、クラウド同期に失敗しました: ' + e.message;
                syncStatus.style.color = 'red';
            }
        }

        location.reload(); // 設定保存後にアプリケーションを再読み込み
    });

    document.getElementById('manual-sync-upload').addEventListener('click', async () => {
        if (!storage.accessToken) { // Check accessToken
            showNotification('ログインが必要です。', 3000, 'warning');
            return;
        }
        syncStatus.textContent = 'アップロード中...';
        syncStatus.style.color = 'blue';
        try {
            await storage.syncWithCloud();
            syncStatus.textContent = 'アップロード完了！';
            syncStatus.style.color = 'green';
        } catch (e) {
            syncStatus.textContent = 'エラー: ' + e.message;
            syncStatus.style.color = 'red';
        }
    });

    document.getElementById('manual-sync-download').addEventListener('click', async () => {
        if (!storage.accessToken) { // Check accessToken
            showNotification('ログインが必要です。', 3000, 'warning');
            return;
        }
        syncStatus.textContent = 'ダウンロード中...';
        syncStatus.style.color = 'blue';
        try {
            await storage.loadFromCloud();
            syncStatus.textContent = 'ダウンロード完了！リロードします...';
            syncStatus.style.color = 'green';
            setTimeout(() => location.reload(), 1000);
        } catch (e) {
            syncStatus.textContent = 'エラー: ' + e.message;
            syncStatus.style.color = 'red';
        }
    });

    // --- Auto Sync Logic (Debounced) ---

    function debounce(func, delay) {

        let timeout;

        return function (...args) {

            const context = this;

            clearTimeout(timeout);

            timeout = setTimeout(() => func.apply(context, args), delay);

        };

    }



    const debouncedSync = debounce(async () => {







        if (!storage.accessToken) {







            console.warn('Auto sync skipped: User not logged in.');







            return;







        }







        console.log('Auto syncing data to cloud...');







        try {







            await storage.syncWithCloud();







            showNotification('自動保存しました！', 1500, 'success');







        } catch (e) {







            if (e.message.includes('ConflictError')) {







                // Optimistic lock conflict detected







                console.warn('Optimistic lock conflict detected:', e.message);







                const confirmReload = confirm(







                    '他の端末でデータが更新されました。最新の状態を読み込みますか？\n' +







                    '（「キャンセル」した場合、この端末での変更は破棄されます）'







                );







                if (confirmReload) {







                    // ページ全体を再読み込みして最新の状態を反映



                    location.reload();







                } else {







                    showNotification('自動保存をキャンセルしました。', 2000, 'info');







                }







            } else {



                console.error('Auto sync failed:', e.message);



                if (e.message.includes('Session expired') || e.message.includes('Unauthorized')) {



                    showNotification('セッションエラー。リロードします。', 3000, 'error');



                    setTimeout(() => location.reload(), 2000);



                } else {



                    showNotification('自動保存に失敗しました: ' + e.message, 5000, 'error');



                }



            }







        }







    }, 3000); // 3 seconds debounce delay







    window.addEventListener('storageChanged', (e) => {
        if (e.detail && e.detail.key === 'bulk_update') {
            console.log('Skipping auto-sync for bulk update');
            return;
        }
        debouncedSync();
    });



    window.addEventListener('archiveUpdated', () => {

        const indexView = document.getElementById('index-view');

        if (indexView.style.display !== 'none') {

            renderIndex(state.data.categories);

            renderTotalProgress();

        }

    });

});

