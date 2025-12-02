function doGet(e) {
    return ContentService.createTextOutput(JSON.stringify({ status: 'active', message: 'GAS Backend is running' })).setMimeType(ContentService.MimeType.JSON);
}

function doPost(e) {
    const lock = LockService.getScriptLock();
    // Wait for up to 10 seconds for other processes to finish.
    try {
        lock.waitLock(10000);
    } catch (e) {
        return ContentService.createTextOutput(JSON.stringify({ error: 'Server is busy. Please try again.' })).setMimeType(ContentService.MimeType.JSON);
    }

    try {
        const params = JSON.parse(e.postData.contents);
        const action = params.action;

        let result = {};

        switch (action) {
            case 'register':
                result = registerUser(params.userId, params.password);
                break;
            case 'login':
                result = loginUser(params.userId, params.password);
                break;
            case 'validate':
                result = validateToken(params.accessToken);
                break;
            case 'refresh':
                result = refreshTokenFlow(params.refreshToken);
                break;
            case 'save':
                result = saveDataWithAuth(params.accessToken, params.data, params.version);
                break;
            case 'load':
                result = loadDataWithAuth(params.accessToken);
                break;
            case 'clear': // ★追加: clearアクションのハンドラ
                result = clearUserData(params.accessToken);
                break;
            default:
                result = { error: 'Invalid action' };
        }

        return ContentService.createTextOutput(JSON.stringify(result)).setMimeType(ContentService.MimeType.JSON);

    } catch (error) {
        return ContentService.createTextOutput(JSON.stringify({ error: error.toString() })).setMimeType(ContentService.MimeType.JSON);
    } finally {
        lock.releaseLock();
    }
}

// --- Configuration ---
// スプレッドシートIDを自動取得（スクリプトがスプレッドシートにバインドされている場合）
function getSpreadsheetId() {
    // まずスクリプトプロパティから取得を試みる
    const savedId = PropertiesService.getScriptProperties().getProperty('SPREADSHEET_ID');
    if (savedId) {
        return savedId;
    }

    // スクリプトがスプレッドシートにバインドされている場合、自動取得
    try {
        const ss = SpreadsheetApp.getActiveSpreadsheet();
        if (ss) {
            return ss.getId();
        }
    } catch (e) {
        // スタンドアロンスクリプトの場合はエラーになる
    }

    // どちらも取得できない場合はエラー
    throw new Error('Spreadsheet ID not configured. Please set SPREADSHEET_ID in Script Properties or bind this script to a spreadsheet.');
}

function getSpreadsheet() {
    const id = getSpreadsheetId();
    return SpreadsheetApp.openById(id);
}

// --- Auth Functions ---

function registerUser(userId, password) {
    if (!userId || !password) return { error: 'Missing userId or password' };

    const ss = getSpreadsheet();
    let usersSheet = ss.getSheetByName('Users');
    if (!usersSheet) {
        usersSheet = ss.insertSheet('Users');
        // New headers for multi-device support
        usersSheet.appendRow(['UserId', 'PasswordHash', 'AccessToken', 'AccessTokenExpiry', 'RefreshTokens']);
    }

    const data = usersSheet.getDataRange().getValues();
    // Check if user exists
    for (let i = 1; i < data.length; i++) {
        if (data[i][0] === userId) {
            return { error: 'User already exists' };
        }
    }

    const passwordHash = hashPassword(password);
    // RefreshTokens column is initialized with an empty JSON array string
    usersSheet.appendRow([userId, passwordHash, '', '', '[]']);

    return { success: true, message: 'User registered successfully' };
}

function loginUser(userId, password) {
    if (!userId || !password) return { error: 'Missing userId or password' };

    const ss = getSpreadsheet();
    const usersSheet = ss.getSheetByName('Users');
    if (!usersSheet) return { error: 'User sheet not found' };

    const data = usersSheet.getDataRange().getValues();
    const headers = data[0];
    const userIdColIdx = headers.indexOf('UserId');
    const hashColIdx = headers.indexOf('PasswordHash');
    const accessTokenColIdx = headers.indexOf('AccessToken');
    const accessTokenExpiryColIdx = headers.indexOf('AccessTokenExpiry');
    const refreshTokensColIdx = headers.indexOf('RefreshTokens'); // Changed

    if ([userIdColIdx, hashColIdx, accessTokenColIdx, accessTokenExpiryColIdx, refreshTokensColIdx].some(idx => idx === -1)) {
        return { error: 'Users sheet is not initialized correctly for multi-device support.' };
    }

    let userRow = null;
    let rowIndex = -1;

    for (let i = 1; i < data.length; i++) {
        if (data[i][userIdColIdx] === userId) {
            userRow = data[i];
            rowIndex = i;
            break;
        }
    }

    if (!userRow) return { error: 'User not found' };

    const storedHash = userRow[hashColIdx];
    const inputHash = hashPassword(password);

    if (storedHash !== inputHash) {
        return { error: 'Invalid password' };
    }

    // --- New Multi-Device Token Logic ---
    const now = new Date();

    // 1. Generate new tokens
    const newAccessToken = Utilities.getUuid();
    const newAccessTokenExpiry = new Date(now.getTime() + 60 * 60 * 1000); // 1 hour from now

    const newRefreshToken = Utilities.getUuid();
    const newRefreshTokenExpiry = new Date(now.getTime() + 60 * 24 * 60 * 60 * 1000); // 60 days from now

    // 2. Manage refresh tokens array
    let refreshTokens = [];
    try {
        const existingTokens = userRow[refreshTokensColIdx];
        if (existingTokens && typeof existingTokens === 'string' && existingTokens.startsWith('[')) {
            refreshTokens = JSON.parse(existingTokens);
        }
    } catch (e) {
        // Handle case where parsing fails, start fresh
        refreshTokens = [];
    }

    // 3. Filter out expired tokens and add the new one
    const validRefreshTokens = refreshTokens.filter(rt => new Date(rt.expiry) > now);
    validRefreshTokens.push({
        token: newRefreshToken,
        expiry: newRefreshTokenExpiry.toISOString()
    });

    // 4. Update the sheet
    usersSheet.getRange(rowIndex + 1, accessTokenColIdx + 1).setValue(newAccessToken);
    usersSheet.getRange(rowIndex + 1, accessTokenExpiryColIdx + 1).setValue(newAccessTokenExpiry.toISOString());
    usersSheet.getRange(rowIndex + 1, refreshTokensColIdx + 1).setValue(JSON.stringify(validRefreshTokens));

    return {
        success: true,
        accessToken: newAccessToken,
        refreshToken: newRefreshToken,
        userId: userId
    };
}

function validateToken(accessToken) {
    if (!accessToken) return { valid: false };

    const user = getUserByAccessToken(accessToken);
    if (user) {
        return { valid: true, userId: user.userId };
    }
    return { valid: false };
}

function refreshTokenFlow(providedRefreshToken) {
    if (!providedRefreshToken) return { error: 'No refresh token provided.' };

    const ss = getSpreadsheet();
    const usersSheet = ss.getSheetByName('Users');
    if (!usersSheet) return { error: 'User sheet not found.' };

    const data = usersSheet.getDataRange().getValues();
    const headers = data[0];
    const refreshTokensColIdx = headers.indexOf('RefreshTokens');
    const accessTokenColIdx = headers.indexOf('AccessToken');
    const accessTokenExpiryColIdx = headers.indexOf('AccessTokenExpiry');
    const userIdColIdx = headers.indexOf('UserId');

    if ([refreshTokensColIdx, accessTokenColIdx, accessTokenExpiryColIdx, userIdColIdx].some(idx => idx === -1)) {
        return { error: 'Users sheet is not initialized correctly for multi-device support.' };
    }

    const now = new Date();
    let targetUserRowIndex = -1;
    let userId = '';

    // Find the user and the valid refresh token
    for (let i = 1; i < data.length; i++) {
        const userRow = data[i];
        let refreshTokens = [];
        try {
            const existingTokens = userRow[refreshTokensColIdx];
            if (existingTokens && typeof existingTokens === 'string' && existingTokens.startsWith('[')) {
                refreshTokens = JSON.parse(existingTokens);
            }
        } catch (e) {
            continue; // Skip row if JSON is invalid
        }

        const foundToken = refreshTokens.find(rt => rt.token === providedRefreshToken && new Date(rt.expiry) > now);

        if (foundToken) {
            targetUserRowIndex = i;
            userId = userRow[userIdColIdx];
            break; // Found the user, exit loop
        }
    }

    if (targetUserRowIndex === -1) {
        return { error: 'Invalid or expired refresh token.' };
    }

    // Generate and save a new access token
    const newAccessToken = Utilities.getUuid();
    const newAccessTokenExpiry = new Date(now.getTime() + 60 * 60 * 1000); // 1 hour from now

    usersSheet.getRange(targetUserRowIndex + 1, accessTokenColIdx + 1).setValue(newAccessToken);
    usersSheet.getRange(targetUserRowIndex + 1, accessTokenExpiryColIdx + 1).setValue(newAccessTokenExpiry.toISOString());

    return { success: true, accessToken: newAccessToken, userId: userId };
}

// --- Data Functions ---

function saveDataWithAuth(accessToken, jsonData, clientVersion) {
    const user = getUserByAccessToken(accessToken);
    if (!user) return { error: 'Unauthorized or Access Token Expired' };

    const ss = getSpreadsheet();
    let dataSheet = ss.getSheetByName('Data');
    if (!dataSheet) {
        dataSheet = ss.insertSheet('Data');
        // Add Version header
        dataSheet.appendRow(['UserId', 'JSON_Data', 'LastUpdated', 'Version']);
    }

    const data = dataSheet.getDataRange().getValues();
    const headers = data[0];
    const userIdColIdx = headers.indexOf('UserId');
    const jsonDataColIdx = headers.indexOf('JSON_Data');
    const lastUpdatedColIdx = headers.indexOf('LastUpdated');
    const versionColIdx = headers.indexOf('Version');

    if ([userIdColIdx, jsonDataColIdx, lastUpdatedColIdx, versionColIdx].some(idx => idx === -1)) {
        return { error: 'Data sheet is not initialized correctly. Missing required headers for optimistic locking.' };
    }

    let found = false;
    let currentRowIndex = -1;
    let storedVersion = 0;

    for (let i = 1; i < data.length; i++) {
        if (data[i][userIdColIdx] === user.userId) {
            currentRowIndex = i;
            storedVersion = parseInt(data[i][versionColIdx] || 0); // Parse existing version, default to 0
            found = true;
            break;
        }
    }

    // Check for optimistic lock conflict
    if (found && clientVersion !== undefined && clientVersion !== storedVersion) {
        return { error: 'ConflictError', currentVersion: storedVersion };
    }

    const newVersion = storedVersion + 1;
    const now = new Date().toISOString();

    if (found) {
        // Update existing
        dataSheet.getRange(currentRowIndex + 1, jsonDataColIdx + 1).setValue(JSON.stringify(jsonData));
        dataSheet.getRange(currentRowIndex + 1, lastUpdatedColIdx + 1).setValue(now);
        dataSheet.getRange(currentRowIndex + 1, versionColIdx + 1).setValue(newVersion);
    } else {
        // Append new row
        dataSheet.appendRow([user.userId, JSON.stringify(jsonData), now, newVersion]);
    }

    return { success: true, version: newVersion };
}

function loadDataWithAuth(accessToken) {
    const user = getUserByAccessToken(accessToken);
    if (!user) return { error: 'Unauthorized or Access Token Expired' };

    const ss = getSpreadsheet();
    const dataSheet = ss.getSheetByName('Data');
    if (!dataSheet) return { data: {}, version: 0 }; // Return empty data and version 0 if no sheet

    const data = dataSheet.getDataRange().getValues();
    const headers = data[0];
    const userIdColIdx = headers.indexOf('UserId');
    const jsonDataColIdx = headers.indexOf('JSON_Data');
    const versionColIdx = headers.indexOf('Version');

    if ([userIdColIdx, jsonDataColIdx, versionColIdx].some(idx => idx === -1)) {
        // Fallback for old sheet structure, or error out
        return { error: 'Data sheet is not initialized correctly. Missing required headers for optimistic locking.' };
    }

    for (let i = 1; i < data.length; i++) {
        if (data[i][userIdColIdx] === user.userId) {
            const storedVersion = parseInt(data[i][versionColIdx] || 0);
            return { data: JSON.parse(data[i][jsonDataColIdx]), version: storedVersion };
        }
    }
    return { data: {}, version: 0 }; // Return empty data and version 0 if no data found for user
}

// ★追加: ユーザーデータをクリアする関数
function clearUserData(accessToken) {
    const user = getUserByAccessToken(accessToken);
    if (!user) return { error: 'Unauthorized or Access Token Expired' };

    const ss = getSpreadsheet();
    const dataSheet = ss.getSheetByName('Data');
    if (!dataSheet) return { success: true, message: 'Data sheet not found, no data to clear.' };

    const data = dataSheet.getDataRange().getValues();
    const headers = data[0];
    const userIdColIdx = headers.indexOf('UserId');

    if (userIdColIdx === -1) {
        return { error: 'Data sheet is not initialized correctly. Missing UserId header.' };
    }

    let rowsToDelete = [];
    for (let i = 1; i < data.length; i++) {
        if (data[i][userIdColIdx] === user.userId) {
            rowsToDelete.push(i + 1); // 行番号は1から始まるため +1
        }
    }

    // 後ろから削除することで行番号のずれを防ぐ
    for (let i = rowsToDelete.length - 1; i >= 0; i--) {
        dataSheet.deleteRow(rowsToDelete[i]);
    }

    return { success: true, message: `Data for user ${user.userId} cleared.` };
}

// --- Helpers ---

function getUserByAccessToken(token) {
    const ss = getSpreadsheet();
    const usersSheet = ss.getSheetByName('Users');
    if (!usersSheet) return null;

    const data = usersSheet.getDataRange().getValues();
    const headers = data[0];
    const accessTokenColIdx = headers.indexOf('AccessToken');
    const accessTokenExpiryColIdx = headers.indexOf('AccessTokenExpiry');
    const userIdColIdx = headers.indexOf('UserId');

    if (accessTokenColIdx === -1 || accessTokenExpiryColIdx === -1 || userIdColIdx === -1) {
        return null; // Sheet not initialized correctly
    }

    for (let i = 1; i < data.length; i++) {
        const storedToken = data[i][accessTokenColIdx];
        const expiryStr = data[i][accessTokenExpiryColIdx];

        if (storedToken === token) {
            const expiry = new Date(expiryStr);
            if (expiry > new Date()) {
                return { userId: data[i][userIdColIdx] };
            }
        }
    }
    return null;
}

function hashPassword(password) {
    const rawHash = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, password);
    let txtHash = '';
    for (let i = 0; i < rawHash.length; i++) {
        let hashVal = rawHash[i];
        if (hashVal < 0) {
            hashVal += 256;
        }
        if (hashVal.toString(16).length == 1) {
            txtHash += '0';
        }
        txtHash += hashVal.toString(16);
    }
    return txtHash;
}
