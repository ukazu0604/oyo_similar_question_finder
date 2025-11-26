import { state } from './state.js';

export async function loadData() {
    try {
        const res = await fetch('03_html_output/similar_results.json');
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
                // 類似度が50%以上のものだけをカウント対象にする
                if (sim.similarity >= 0.5) {
                    const problemId = sim.data.問題番号;
                    countsInCat[problemId] = (countsInCat[problemId] || 0) + 1;
                }
            });
        });

        // この中分類のカウント結果を保存
        state.referenceCounts[middleCat] = countsInCat;
    }
}
