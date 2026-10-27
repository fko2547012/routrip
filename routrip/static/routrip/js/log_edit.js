// ==========================
// 編集画面の初期設定
// ==========================
const logForm = document.getElementById('log-edit-form');
const cardList = document.getElementById('card-list');

// Pythonから渡された、登録済みの写真とサムネイル
const savedImages = JSON.parse(
    document.getElementById('card-images').textContent
);
const selectedThumbnail = JSON.parse(
    document.getElementById('selected-thumbnail').textContent
);

// 入力内容が変更されたか
let isChanged = false;
let isSubmitting = false;
let skipLeaveWarning = false;

logForm.addEventListener('input', () => {
    isChanged = true;
});

logForm.addEventListener('change', () => {
    isChanged = true;
});

// カード内の入力欄を取得
function cardField(card, name) {
    return card.querySelector(`[name$="-${name}"]`);
}

// 削除されていないカードを取得
function activeCards() {
    return [...cardList.querySelectorAll(':scope > .card-form')]
    .filter((card) => {
        const value = cardField(card, 'DELETE').value.toLowerCase();
        return !['on', 'true', '1'].includes(value);
    });
}


// ==========================
// カードの追加・削除・写真プレビュー
// ==========================

// 保存済みの写真、または選び直した写真を表示
function renderPhoto(card) {
    const input = cardField(card, 'image_path');
    const box = card.querySelector('.card-image');
    const clear = card.querySelector(
    'input[type="checkbox"][name$="-image_path-clear"]'
);
let img = box.querySelector('.preview');
if (card.dataset.previewUrl) {
    URL.revokeObjectURL(card.dataset.previewUrl);
    delete card.dataset.previewUrl;
}

let src = savedImages[card.dataset.prefix] || '';

if (clear && clear.checked) {src = '';}

if (input.files.length > 0) {
    src = URL.createObjectURL(input.files[0]);
    card.dataset.previewUrl = src;
}

if (!src) {if (img) img.remove();
    return;
}

if (!img) {
    img = document.createElement('img');
    img.className = 'preview';
    img.alt = 'カードの写真';
    box.prepend(img);
}

img.src = src;
}

// カードの初期設定
function prepareCard(card) {
    card.dataset.prefix = cardField(card, 'ORDER').name
    .replace(/-ORDER$/, '');
    const deleted = cardField(card, 'DELETE').value.toLowerCase();
    card.hidden = ['on', 'true', '1'].includes(deleted);

  // 並び替えボタンを追加
    const controls = document.createElement('div');
    
    [['up', '↑ 上へ'],['down', '↓ 下へ'],].forEach(([action, text]) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.dataset.action = action;
        button.textContent = text;
        controls.append(button);
    });
    card.querySelector('.card-box').append(controls);
    renderPhoto(card);
}

// カードのフォーム番号は変えず、表示順だけを更新
function renumberCards() {
    activeCards().forEach((card, i) => {
        cardField(card, 'ORDER').value = i + 1;
        card.querySelector('.card-title').textContent = `カード ${i + 1}`;
    });
}

// 区間が変わったら、移動手段・時間を未設定にする
function updateRoutes(reset = true) {
    let from = document.getElementById('id_start_spot').value;
    activeCards().forEach((card) => {
    const to = cardField(card, 'spot').value;
    const route = JSON.stringify([from, to]);

    if (reset && card.dataset.route !== undefined && card.dataset.route !== route) {
        cardField(card, 'transport').value = '';
        cardField(card, 'duration').value = '';
    }
    card.dataset.route = route;
    from = to;
});
}

// 登録済みのカードを準備
cardList.querySelectorAll(':scope > .card-form')
.forEach(prepareCard);

// 入力エラーで戻った場合も、変更後の順番を復元
activeCards()
.sort((a, b) => {
    return Number(cardField(a, 'ORDER').value)
    - Number(cardField(b, 'ORDER').value);
})
.forEach((card) => cardList.append(card));
renumberCards();
updateRoutes(false);

// 「カードを追加」ボタン
document.getElementById('add-card').addEventListener('click', () => {
    const totalInput = document.getElementById('id_cards-TOTAL_FORMS');
    const index = Number(totalInput.value);
    const html = document.getElementById('card-template').innerHTML
    .replaceAll('__prefix__', index);
    
    cardList.insertAdjacentHTML('beforeend', html);
    totalInput.value = index + 1;
    
    prepareCard(cardList.lastElementChild);
    renumberCards();
    updateRoutes();
    renderThumbs();
    
    isChanged = true;
});

// 写真・スポットが変更されたとき
cardList.addEventListener('change', (e) => {
    const card = e.target.closest('.card-form');
    if (!card) return;
    
    if (
        e.target.matches('input[type="file"]') ||
        e.target.name.endsWith('-image_path-clear')
    ) {
        renderPhoto(card);
    renderThumbs()
}

if (e.target.name.endsWith('-spot')) {
    updateRoutes();
}
});

// カード削除・並び替え
cardList.addEventListener('click', (e) => {
    const button = e.target.closest('button');
    if (!button) return;
    const card = button.closest('.card-form');
    if (!card) return;
    
    if (button.classList.contains('remove-card')) {
    // カードを消さず、削除フラグを付けて送信する
    cardField(card, 'DELETE').value = 'on';
    card.hidden = true;
} else {
    const cards = activeCards();
    const index = cards.indexOf(card);
    
    if (button.dataset.action === 'up' && index > 0) {
        cardList.insertBefore(card, cards[index - 1]);
    } else if (
        button.dataset.action === 'down' &&
        index < cards.length - 1
    ) {
        cards[index + 1].after(card);
    } else {
        return;
    }
}
renumberCards();
updateRoutes();
renderThumbs();

isChanged = true;
});

// 出発地が変更されたとき
document.getElementById('id_start_spot')
.addEventListener('change', () => updateRoutes());


// ==========================
// タグ（チップ）
// ==========================
const tagInput = document.getElementById('tag-input');
const tagHidden = document.getElementById('id_tag_text');
const tagChips = document.getElementById('tag-chips');
const tagError = document.getElementById('tag-error');
let tags = [...new Set(tagHidden.value.split(/[,\s、，]+/).filter(Boolean)
)];

function renderTags() {
    tagChips.innerHTML = '';
    tags.forEach((name, i) => {
        const chip = document.createElement('span');
        chip.className = 'chip';
        
        const remove = document.createElement('button');
        remove.type = 'button';
        remove.className = 'chip-remove';
        remove.textContent = '×';
        remove.dataset.index = i;

        const label = document.createElement('span');
        label.textContent = '#' + name;
        chip.append(remove, label);
        tagChips.append(chip);
    });
    tagHidden.value = tags.join(' ');
}

// 入力欄の文字をタグとして追加
function addTagsFromInput() {
    tagError.textContent = '';
    const names = tagInput.value
    .split(/[,\s、，]+/)
    .map((name) => name.replace(/^[#＃]+/, ''))
    .filter(Boolean);
    
    if (names.some((name) => [...name].length > 30)) {
        tagError.textContent = 'タグは30文字以内にしてください';
        return false;
    }
    if (names.some((name) => !tags.includes(name))) {
    isChanged = true;
}

tags = [...new Set([...tags, ...names])];
tagInput.value = '';

renderTags();
return true;
}

// Enterでタグ追加
tagInput.addEventListener('keydown', (e) => {
    if (e.key !== 'Enter' || e.isComposing) return;
    e.preventDefault();
    addTagsFromInput();
});

// 追加ボタン
document.getElementById('add-tag')
.addEventListener('click', addTagsFromInput);

// タグ削除
tagChips.addEventListener('click', (e) => {const button = e.target.closest('.chip-remove');
    if (!button) return;
    tags.splice(Number(button.dataset.index), 1);
    renderTags();
    isChanged = true;
});

renderTags();


// ==========================
// サムネイル選択
// ==========================
const thumbList = document.getElementById('thumb-list');
let thumbCard = activeCards().find((card) => card.dataset.prefix === selectedThumbnail) || null;

function renderThumbs() {
    thumbList.innerHTML = '';
    const cards = activeCards().filter(
        (card) => card.querySelector('.preview')
    );

  // 選択していたカードが削除されたら、最初の写真にする
if (!cards.includes(thumbCard)) {thumbCard = cards[0] || null;}
cards.forEach((card) => {
    const preview = card.querySelector('.preview');
    const label = document.createElement('label');
    label.className = 'thumb';
    const radio = document.createElement('input');
    radio.type = 'radio';
    radio.name = 'thumbnail';

    // 編集用Pythonと同じキーを送る
    radio.value = card.dataset.prefix;
    radio.checked = card === thumbCard;
    radio.addEventListener('change', () => {
        thumbCard = card;
        isChanged = true;
    });
    const img = document.createElement('img');
    img.src = preview.src;
    img.alt = 'サムネイル候補';
    
    const check = document.createElement('span');
    check.className = 'thumb-check';
    check.textContent = '✓';
    label.append(radio, img, check);
    thumbList.append(label);
});
}

renderThumbs();


// ==========================
// 画面の切り替え
// ==========================
const step2 = document.getElementById('edit-step-2');
const step3 = document.getElementById('edit-step-3');
const step2Error = document.getElementById('edit-error');

function showStep(n) {
    step2.classList.toggle('is-active', n === 2);
    step3.classList.toggle('is-active', n === 3);
    step2.hidden = n !== 2;
    step3.hidden = n !== 3;
    window.scrollTo(0, 0);
}

function showStep2Error(message) {
    step2Error.textContent = message;
    step2Error.hidden = false;
}

// 画面2 → 画面3
document.getElementById('to-step-3').addEventListener('click', () => {
    step2.querySelectorAll('.invalid').forEach((el) => {el.classList.remove('invalid');});
    
    if (activeCards().length === 0) {
        showStep2Error('カードを1枚以上追加してください');
        return;
    }

  // 削除対象のカードは、未入力チェックから除く
    const required = [...step2.querySelectorAll(
        '[name="title"], [name="trip_start_date"], ' +
        '[name="trip_end_date"], [name="start_spot"]'
    ),
    ...activeCards().flatMap((card) => [
        cardField(card, 'transport'),
        cardField(card, 'spot'),
        cardField(card, 'comment'),
    ]),
];

    const empty = required.filter((el) => el.value.trim() === '');
    if (empty.length > 0) {empty.forEach((el) => el.classList.add('invalid'));
        showStep2Error('未入力があります。');
        empty[0].scrollIntoView({ block: 'center' });
        return;
    }
    const start = step2.querySelector('[name="trip_start_date"]');
    const end = step2.querySelector('[name="trip_end_date"]');
    if (end.value < start.value) {end.classList.add('invalid');
        showStep2Error('終了日は開始日以降にしてください');
        end.scrollIntoView({ block: 'center' });
        return;
    }
    step2Error.hidden = true;
    renderThumbs();
    showStep(3);
});

// 開始日より前の終了日は選択できないようにする
const startDate = step2.querySelector('[name="trip_start_date"]');
const endDate = step2.querySelector('[name="trip_end_date"]');

startDate.addEventListener('change', () => {endDate.min = startDate.value;});
endDate.min = startDate.value;

// 入力し直したら赤枠を消す
step2.addEventListener('input', (e) => {e.target.classList.remove('invalid');});

step2.addEventListener('change', (e) => {e.target.classList.remove('invalid');});

// 画面3 → 画面2
document.getElementById('back-to-step-2')
.addEventListener('click', () => showStep(2));

// Enterで誤って更新しないようにする
logForm.addEventListener('keydown', (e) => {
    if (e.isComposing) return;
    if (e.key === 'Enter' && e.target.tagName === 'INPUT') {
        e.preventDefault();
    }
});


// ==========================
// 二重更新の防止
// ==========================
const submitButton = logForm.querySelector('.submit-button');

logForm.addEventListener('submit', (e) => {
    if (isSubmitting) {
        e.preventDefault();
        return;
    }

  // 入力途中のタグを確定する
    if (!addTagsFromInput()) {
        e.preventDefault();
        showStep(3);
        return;
    }

    renumberCards();
    isSubmitting = true;
    submitButton.disabled = true;
    submitButton.textContent = '更新中…';
});

// ブラウザの「戻る」で復元されたとき
window.addEventListener('pageshow', (e) => {
    if (e.persisted) {
        isSubmitting = false;
        skipLeaveWarning = false;
        submitButton.disabled = false;
        submitButton.textContent = '更新する';
    }
});


// ==========================
// 入力が消える前の確認
// ==========================

// 更新・タブを閉じる・ブラウザで戻るとき
window.addEventListener('beforeunload', (e) => {
    if (skipLeaveWarning || isSubmitting || !isChanged) return;
    e.preventDefault();
    e.returnValue = '';
});

// 編集画面の「← 戻る」リンク
document.querySelector('#edit-step-2 a.back-button')
.addEventListener('click', (e) => {
    if (
        isChanged &&
        !confirm('変更した内容が保存されません。詳細画面に戻りますか？')
    ) {
        e.preventDefault();
        return;
    }

    skipLeaveWarning = true;
});