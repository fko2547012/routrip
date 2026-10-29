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

logForm.addEventListener('input', () => { isChanged = true;});

logForm.addEventListener('change', () => { isChanged = true;});

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

if (input.files.length > 0) { src = URL.createObjectURL(input.files[0]);
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

    const deleteField = cardField(card, 'DELETE');
    const deleted = deleteField
        ? deleteField.value.toLowerCase()
        : '';

    card.hidden = ['on', 'true', '1'].includes(deleted);
    renderPhoto(card);
}

// カードのフォーム番号は変えず、表示順だけを更新
function renumberCards() {
    activeCards().forEach((card, i) => {
        cardField(card, 'ORDER').value = i + 1;
        card.querySelector('.card-number').textContent = `カード ${i + 1}`;
    });
}

// スポットを比較するための値を作る
function editSpotKey(root) {
    const id = root.querySelector('[name$="-spot"]');
    const lat = root.querySelector('[name$="-new_spot_lat"]');
    const lng =root.querySelector('[name$="-new_spot_lng"]');

    if (id.value){
        return `db${id.value}`;
    }
    // 新しいスポットは緯度・経度で区別
    if (lat.value !== '' && lng.value !== '') {
        return `new:${Number(lat.value)},${Number(lng.value)}`;
    }
    return '';
}

// 区間が変わったら、移動手段・時間を未設定にする
function updateRoutes(reset = true) {
    let from = editSpotKey(
        logForm.querySelector('.start-box')
    );
    activeCards().forEach((card) => {
        const to = editSpotKey(card);
        const route = JSON.stringify([from, to]);

        if (
            reset &&
            card.dataset.route !== undefined &&
            card.dataset.route !== route
        ) {
            cardField(card, 'transport').value = '';
            cardField(card, 'duration').value = '';
            const unit = cardField(card, 'duration_unit');
            
            if (unit) {
                unit.value = 'minutes';
            }
        }
        card.dataset.route = route;
        from = to;
    });
}

// 登録済みのカードを準備する
cardList.querySelectorAll(':scope > .card-form')
    .forEach(prepareCard);

// 入力エラー時も変更後の順番を復元する
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
    
    const html = document.getElementById('card-template').innerHTML .replaceAll('__prefix__', index);
    cardList.insertAdjacentHTML('beforeend', html);
    totalInput.value = index + 1;
    prepareCard(cardList.lastElementChild);

    showSavedSpot(
        cardList.lastElementChild.querySelector('.spot-area')
    );
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

    if (button.classList.contains('remove-card')) { const deleteField = cardField(card, 'DELETE');
        
        if (deleteField) {
            deleteField.value = 'on';
            card.hidden = true;
        } else {
            card.remove();
        }

    } else {
        const cards = activeCards();
        const index = cards.indexOf(card);
        
        if (button.classList.contains('move-up') && index > 0) { cardList.insertBefore(card, cards[index - 1]);
        } else if (
            button.classList.contains('move-down') &&
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
document.getElementById('id_start-spot')
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
    
    if (names.some((name) => [...name].length > 30)) { tagError.textContent = 'タグは30文字以内にしてください';
        return false;
    }
    if (names.some((name) => !tags.includes(name))) { isChanged = true;
    }

tags = [...new Set([...tags, ...names])];
tagInput.value = '';

renderTags();
return true;
}

// Enterでタグ追加
tagInput.addEventListener('keydown', (e) => { if (e.key !== 'Enter' || e.isComposing) return;
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
    radio.addEventListener('change', () => { thumbCard = card;
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
    step2.querySelectorAll('.invalid').forEach((elment) => {elment.classList.remove('invalid');});
    
    if (!activeCards().length) {showStep2Error('カードを1枚以上追加してください');
        return;
    }

  // 削除対象のカードは、未入力チェックから除く
    const required = [...step2.querySelectorAll(
        '[name="title"], [name="trip_start_date"], ' +
        '[name="trip_end_date"]'
    ),
    ...activeCards().flatMap((card) => [
        cardField(card, 'transport'),
        cardField(card, 'comment'),
    ]),
];

    const empty = required.filter((elment) => !elment.value.trim());
    const spotArea=[
        step2.querySelector('.start-box .spot-area'),
        ...activeCards().map((card)=> card.querySelector('.spot-area')),
    ];
    const incompleteSpots=spotArea.filter(
        (area)=>!editSpotIsComplete(area)
    ); 
    empty.forEach((element)=>{
        element.classList.add('invalid');
    });
    incompleteSpots.forEach((area)=>{
        area.classList.add('invalid');
    });
    if (empty.length || incompleteSpots.length) {
        showStep2Error('未入力があります。');
        (empty[0] || incompleteSpots[0]).scrollIntoView({ block: 'center' });
        return;
    }
    const start = step2.querySelector('[name="trip_start_date"]');
    const end = step2.querySelector('[name="trip_end_date"]');
    if (end.value < start.value) {end.classList.add('invalid');
        showStep2Error('終了日は開始日以降にしてください');
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
logForm.addEventListener('keydown', (e) => { if (e.isComposing) return;
    if (e.key === 'Enter' && e.target.tagName === 'INPUT') { e.preventDefault();
    }
});


// ==========================
// 二重更新の防止
// ==========================
const submitButton = logForm.querySelector('.submit-button');

logForm.addEventListener('submit', (e) => { if (isSubmitting) {
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
window.addEventListener('pageshow', (e) => { if (e.persisted) {
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
window.addEventListener('beforeunload', (e) => { if (skipLeaveWarning || isSubmitting || !isChanged) return;
    e.preventDefault();
    e.returnValue = '';
});

// 編集画面の「← 戻る」リンク
document.querySelector('#edit-step-2 a.back-button')
.addEventListener('click', (e) => {
    if ( isChanged && !confirm('変更した内容が保存されません。詳細画面に戻りますか？')) {
        e.preventDefault();
        return;
    }

    skipLeaveWarning = true;
});

// 保存済みの出発地・スポット名を表示する
function showSavedSpot(area) {
    const root = area.closest('.card-form, .start-box');

    const label = root.querySelector('[name$="-spot_label"]');
    const newName = root.querySelector('[name$="-new_spot_name"]');

    const resolved = area.querySelector('.spot-resolved');
    const nameLabel = area.querySelector('.spot-name');
    const search = area.querySelector('.place-search');

    const savedName = label ? label.value.trim() : '';
    const newSpotName = newName ? newName.value.trim() : '';

    if (newSpotName) {
        resolved.hidden = false;
        search.hidden = true;
        nameLabel.hidden = true;
        newName.hidden = false;
    } else if (savedName) {
        nameLabel.textContent = savedName;
        nameLabel.hidden = false;
        resolved.hidden = false;
        search.hidden = true;

        if (newName) {newName.hidden = true;}
    } else {
        resolved.hidden = true;
        search.hidden = false;
    }
}

// 初めて画面を開いたときにも適用する
logForm.querySelectorAll('.spot-area').forEach(showSavedSpot);


// ==========================
// スポットの変更・検索・選択
// ==========================
const editSearchUrl = logForm.dataset.searchUrl;
const editNearbyUrl = logForm.dataset.nearbyUrl;

let editSpotTask = 0;
let nextSearchTime = 0;

// スポット欄の入力要素を取得する
function editSpotParts(area) {
    const root = area.closest('.card-form, .start-box');
    return {
        id: root.querySelector('[name$="-spot"]'),
        label: root.querySelector('[name$="-spot_label"]'),
        newName: root.querySelector('[name$="-new_spot_name"]'),
        lat: root.querySelector('[name$="-new_spot_lat"]'),
        lng: root.querySelector('[name$="-new_spot_lng"]'),
        status: area.querySelector('.spot-status'),
        resolved: area.querySelector('.spot-resolved'),
        nameLabel: area.querySelector('.spot-name'),
        search: area.querySelector('.place-search'),
        note: area.querySelector('.place-search-note'),
        query: area.querySelector('.place-query'),
        results: area.querySelector('.place-results'),
    };
}

// 古い検索結果を反映しないための番号
function beginEditSpotTask(area) {
    const task = ++editSpotTask;
    area.dataset.editTask = String(task);
    return task;
}

function isCurrentEditSpotTask(area, task) {
    return (
        area.isConnected &&
        !area.closest('.card-form')?.hidden &&
        area.dataset.editTask === String(task)
    );
}

// スポットが確定しているか
function editSpotIsComplete(area) {
    const p = editSpotParts(area);
    return Boolean(
        p.id.value || (
            p.newName.value.trim() &&
            p.lat.value !== '' &&
            p.lng.value !== ''
        )
    );
}

// メッセージを安全に表示する
function editSpotMessage(container, text) {
    const message = document.createElement('p');
    message.className = 'spot-candidates-note';
    message.textContent = text;
    container.replaceChildren(message);
}

// 検索APIからJSONを取得する
async function getEditSpotJson(baseUrl, parameters) {
    const url = new URL(baseUrl, window.location.href);
    
    Object.entries(parameters).forEach(([name, value]) => {url.searchParams.set(name, value);});

    const response = await fetch(url, { headers: { Accept: 'application/json' },});
    
    if (response.redirected) { throw new Error('ログイン状態を確認してください。');}
    let data;
    try {
        data = await response.json();
    } catch {
        throw new Error('検索結果を取得できませんでした。');
    }
    if (!response.ok || data.error) {throw new Error(
            data.error || '検索に失敗しました。'
        );
    }
    return data;
}

// 「変更」で検索欄を表示する
function openEditSpotSearch(area) {
    beginEditSpotTask(area);

    const p = editSpotParts(area);
    const previousName = p.newName.value || p.label.value;
    
    p.id.value = '';
    p.label.value = '';
    p.newName.value = '';
    p.lat.value = '';
    p.lng.value = '';
    p.resolved.hidden = true;
    p.search.hidden = false;
    p.status.textContent = '';
    p.results.replaceChildren();
    p.note.textContent = '地名で検索して、場所を選んでください。';
    p.query.value = previousName;
    p.query.focus();
    updateRoutes();
    isChanged = true;
}

// 地名を検索する
async function searchEditPlaces(area) {
    const p = editSpotParts(area);
    const query = p.query.value.trim();

    if (!query) { editSpotMessage(p.results, '地名を入力してください。');
        return;
    }

    if (Date.now() < nextSearchTime) {
        editSpotMessage( p.results, '少し待ってから検索してください。');
        return;
    }

    nextSearchTime = Date.now() + 1000;
    const task = beginEditSpotTask(area);
    editSpotMessage(p.results, '検索中…');
    
    try {
        const data = await getEditSpotJson(editSearchUrl, { q: query,});
        if (!isCurrentEditSpotTask(area, task)) return;
        
        const places = data.results || [];
        if (!places.length) { editSpotMessage( p.results, '見つかりませんでした。市区町村名などを加えて検索してください。');
            return;
        }

        editSpotMessage(p.results, '場所を選んでください。');
        places.forEach((place) => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'place-result';
            const name = document.createElement('span');
            name.className = 'place-result-name';
            name.textContent = place.name;
            button.append(name);

            if (place.address) {
                const address = document.createElement('span');
                address.className = 'place-result-detail';
                address.textContent = place.address;
                button.append(address);
            }
            button.addEventListener('click', () => {
                selectEditPlace(area, place);
            });
            p.results.append(button);
        });
    } catch (error) {if (!isCurrentEditSpotTask(area, task)) return;
        editSpotMessage(p.results, error.message);
    }
}

// 検索結果を選択する
async function selectEditPlace(area, place) {
    const p = editSpotParts(area);
    const task = beginEditSpotTask(area);
    
    p.status.textContent = '近くの登録済みスポットを確認しています…';
    try {
        const data = await getEditSpotJson(editNearbyUrl, {
            lat: place.lat,
            lng: place.lng,
        });
        if (!isCurrentEditSpotTask(area, task)) return;
        const existingSpot = (data.results || [])[0];
        if (existingSpot) {
        // 近くに登録済みスポットがある場合
            p.id.value = existingSpot.id;
            p.label.value = existingSpot.name;
            p.newName.value = '';
            p.lat.value = '';
            p.lng.value = '';
            p.nameLabel.textContent = existingSpot.name;
            p.nameLabel.hidden = false;
            p.newName.hidden = true;
        } else {
            // 新しいスポットとして保存する場合
            p.id.value = '';
            p.label.value = place.name;
            p.newName.value = place.name;
            p.lat.value = place.lat;
            p.lng.value = place.lng;
            p.nameLabel.hidden = true;
            p.newName.hidden = false;
        }

        p.status.textContent = '';
        p.results.replaceChildren();
        p.search.hidden = true;
        p.resolved.hidden = false;

        area.classList.remove('invalid');

        updateRoutes();
        isChanged = true;
    } catch (error) {
        if (!isCurrentEditSpotTask(area, task)) return;
        p.status.textContent = error.message;
    }
}

// 出発地・既存カード・追加カードのボタンに対応する
logForm.addEventListener('click', (event) => {
    const area = event.target.closest('.spot-area');
    if (!area) return;
    if (event.target.closest('.spot-change')) {
        event.preventDefault();
        openEditSpotSearch(area);
    } else if (event.target.closest('.place-search-button')) {
        event.preventDefault();
        searchEditPlaces(area);
    }
});

// 検索欄のEnterでも検索する
logForm.addEventListener('keydown', (event) => {
    if (
        event.key !== 'Enter' ||
        event.isComposing ||
        !event.target.matches('.place-query')
    ) {
        return;
    }
    event.preventDefault();
    searchEditPlaces(event.target.closest('.spot-area'));
});