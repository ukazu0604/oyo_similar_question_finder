import { state } from './state.js';
import { storage } from './storage.js';

// GAS Web App URL
function getGasUrl() {
    const config = storage.loadGasConfig();
    return config.url;
}

async function postToGas(action, payload = {}, authRequired = false, isRetry = false) {
    const url = getGasUrl();
    if (!url) {
        throw new Error('GAS URL is not configured.');
    }

    const buildBody = () => {
        const body = {
            action: action,
            ...payload
        };
        if (authRequired) {
            const token = storage.accessToken;
            if (!token) {
                throw new Error('Authentication required, but access token is missing.');
            }
            body.accessToken = token;
        }
        return body;
    };

    const makeRequest = async () => {
        const body = buildBody();
        try {
            const response = await fetch(url, {
                method: 'POST',
                mode: 'cors',
                headers: {
                    'Content-Type': 'text/plain;charset=utf-8',
                },
                body: JSON.stringify(body)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();

            if (result.error) {
                throw new Error(result.error);
            }
            return result;
        } catch (error) {
            throw error;
        }
    };

    try {
        return await makeRequest();
    } catch (error) {
        const isAuthError = authRequired && (
            error.message.includes('Unauthorized') || 
            error.message.includes('Expired') || 
            error.message.includes('missing')
        );
        
        if (isAuthError && !isRetry) {
            try {
                const refreshResult = await refreshAccessToken();
                if (refreshResult) {
                    return await postToGas(action, payload, authRequired, true);
                } else {
                    throw new Error('Session expired. Please log in again.');
                }
            } catch (refreshError) {
                throw refreshError;
            }
        }
        
        throw error;
    }
}

export async function register(userId, password) {
    return await postToGas('register', { userId, password });
}

export async function login(userId, password) {
    // The responsibility of saving tokens is now in the caller (app.js)
    return await postToGas('login', { userId, password });
}

export async function refreshAccessToken() {
    const refreshToken = storage.refreshToken;
    if (!refreshToken) {
        throw new Error('No refresh token available.');
    }

    try {
        const result = await postToGas('refresh', { refreshToken });
        if (result.success && result.accessToken) {
            storage.accessToken = result.accessToken;
            if (result.userId) {
                storage.saveGasConfig(getGasUrl(), result.userId);
            }
            return result;
        } else {
            throw new Error(result.error || 'Refresh flow did not return a new access token.');
        }
    } catch (e) {
        // Don't log this to console, it might be expected if refresh token is expired.
        // console.error('[REFRESH] Failed to refresh access token:', e.message, e);
        storage.accessToken = null;
        storage.refreshToken = null;
        return null; 
    }
}

export async function validate(accessToken) {
    return await postToGas('validate', { accessToken });
}

export async function saveUserData(data, version) {
    return await postToGas('save', { data, version }, true);
}

export async function loadUserData() {
    return await postToGas('load', {}, true);
}

export async function clearUserData() {
    return await postToGas('clear', {}, true);
}

export async function loadData(modelId = 'similar_results.json') {
    try {
        const res = await fetch(`03_html_output/${modelId}`);
        state.data = await res.json();

        // **類似問題を同じ中分類のものだけにフィルタリングする**
        for (const middleCat in state.data.categories) {
            state.data.categories[middleCat].forEach(item => {
                item.similar_problems = item.similar_problems.filter(sim => {
                    return sim.data.中分類 === item.main_problem.中分類;
                });
            });
        }

        calculateReferenceCounts(state.data.categories);

        return state.data;
    } catch (e) {
        console.error('データ読み込みエラー', e);
        throw e;
    }
}

function calculateReferenceCounts(categories) {
    state.referenceCounts = {}; // カウント結果を格納するオブジェクトを初期化

    // 中分類ごとにループ
    for (const middleCat in categories) {
        const problemsInCat = categories[middleCat];
        const countsInCat = {}; // この中分類内でのカウント用

        // この中分類内の各問題が持つ「類似問題リスト」をチェック
        problemsInCat.forEach(item => {
            item.similar_problems.forEach(sim => {
                // 類似度が80%以上のものだけをカウント対象にする
                if (sim.similarity >= 0.8) {
                    const problemId = sim.data.問題番号;
                    countsInCat[problemId] = (countsInCat[problemId] || 0) + 1;
                }
            });
        });

        // この中分類のカウント結果を保存
        state.referenceCounts[middleCat] = countsInCat;
    }
}