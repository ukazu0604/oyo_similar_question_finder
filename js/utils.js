export function isMobileDevice() {
    return /Mobi|Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

export function shouldHighlightProblem(problemId, problemChecks) {
    const checks = problemChecks[problemId];
    if (!checks) return false;

    const now = Date.now();
    const reviewIntervals = [
        1 * 60 * 60 * 1000,   // 1時間
        1 * 24 * 60 * 60 * 1000,  // 1日
        6 * 24 * 60 * 60 * 1000,  // 6日
        Infinity // 4つ目はハイライトしない
    ];

    // 最後のチェックがどの段階かを見つける
    let lastCheckedIndex = -1;
    for (let i = checks.length - 1; i >= 0; i--) {
        if (checks[i] && checks[i].checked) {
            lastCheckedIndex = i;
            break;
        }
    }

    // どのチェックもされていない場合はハイライトしない
    if (lastCheckedIndex === -1) {
        return false;
    }

    // 最後のチェックのタイムスタンプと経過時間を取得
    const lastCheck = checks[lastCheckedIndex];
    const elapsedTime = now - lastCheck.timestamp;
    const requiredInterval = reviewIntervals[lastCheckedIndex];
    const shouldHighlight = elapsedTime > requiredInterval;

    // デバッグ用に時刻情報をコンソールに出力
    if (lastCheck.timestamp) { // タイムスタンプがある場合のみログ出力
        // console.log(`[Highlight Check] Problem: ${problemId}`, { ... });
        // Keeping it clean for now, can add back if needed or use a debug flag
    }

    // 経過時間が指定の間隔を超えていればハイライト対象
    return shouldHighlight;
}

export function isProblemUntouched(item, problemChecks) {
    const problemId = `${item.main_problem.出典}-${item.main_problem.問題番号}`;
    const checks = problemChecks[problemId];

    // チェック情報が存在しない場合は未着手
    if (!checks) return true;

    // checks配列のいずれかのcheckedプロパティがtrueであれば着手済み
    const isTouched = checks.some(c => c && c.checked);

    // isTouchedがtrueなら着手済みなので、その逆（false）を返す
    return !isTouched;
}
