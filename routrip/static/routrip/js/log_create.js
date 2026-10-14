// ==========================
// カードの追加・削除・写真プレビュー
// ==========================
// 「カードを追加」ボタンを押したら、フォームのセットを追加する
document.getElementById('add-card').addEventListener('click', () => {
  const totalInput = document.querySelector('[name$="-TOTAL_FORMS"]');
  const index = Number(totalInput.value);

  const html = document.getElementById('card-template').innerHTML
    .replaceAll('__prefix__', index);
  document.getElementById('card-list').insertAdjacentHTML('beforeend', html);

  totalInput.value = index + 1;
});


// 写真を選んだら、四角の中にプレビューを表示する
document.getElementById('card-list').addEventListener('change', (e) => {
  const input = e.target;
  if (!input.matches('input[type="file"]')) return;

  const box = input.closest('.card-image');
  let img = box.querySelector('.preview');

  if (img) {
    URL.revokeObjectURL(img.src); // 前のプレビュー用の領域を解放する
  }

  const file = input.files[0];
  if (!file) {  // 選択を取り消したとき
    if (img) img.remove();
    renderThumbs();
    return;
  }

  if (!img) {
    img = document.createElement('img');
    img.className = 'preview';
    img.alt = '';
    box.prepend(img); // 画像を、四角の一番上に入れる
  }
  img.src = URL.createObjectURL(file);
  renderThumbs();
});


// カードの番号を 0, 1, 2... と詰め直す
function renumberCards() {
  const cards = document.querySelectorAll('#card-list > .card-form');
  cards.forEach((card, i) => {
    card.querySelectorAll('[name], [id], [for]').forEach((el) => {
      ['name', 'id', 'for'].forEach((attr) => {
        const value = el.getAttribute(attr);
        if (value) {
          el.setAttribute(attr, value.replace(/-\d+-/, `-${i}-`));
        }
      });
    });
  });
  document.querySelector('[name$="-TOTAL_FORMS"]').value = cards.length;
}

// 「×」を押したカードを消す
document.getElementById('card-list').addEventListener('click', (e) => {
  const button = e.target.closest('.remove-card');
  if (!button) return;

  const card = button.closest('.card-form');
  const preview = card.querySelector('.preview');
  if (preview) URL.revokeObjectURL(preview.src);   // プレビュー用の領域を解放

  card.remove();
  renumberCards();
  renderThumbs();
});


// ==========================
// タグ（チップ）
// ==========================
const tagInput = document.getElementById('tag-input');
const tagHidden = document.getElementById('id_tag_text');
const tagChips = document.getElementById('tag-chips');
const tagError = document.getElementById('tag-error');

// 保存エラーで戻ってきたときのために、隠し入力欄の値から、タグを復元する
let tags = tagHidden.value.split(/\s+/).filter(Boolean);

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
    label.textContent = '#' + name;       // textContent なので、入力した文字が HTML として動くことはない

    chip.append(remove, label);
    tagChips.append(chip);
  });
  tagHidden.value = tags.join(' ');       // サーバーに送る値を更新
}

// 入力欄の文字を、タグとして追加する
function addTagsFromInput() {
  tagError.textContent = '';
  const names = tagInput.value.split(/[,\s、，]+/);
  names.forEach((raw) => {
    const name = raw.replace(/^[#＃]+/, '');   // 先頭の # は取り除く
    if (!name || tags.includes(name)) return;
    if (name.length > 30) {
      tagError.textContent = 'タグは30文字以内にしてください';
      return;
    }
    tags.push(name);
  });
  tagInput.value = '';
  renderTags();
}

// Enter でタグを追加する（フォームの送信はさせない）
tagInput.addEventListener('keydown', (e) => {
  if (e.key !== 'Enter') return;
  if (e.isComposing) return;              // 日本語の変換を確定するEnterは、無視する
  e.preventDefault();
  addTagsFromInput();
});

// チップの「×」で、そのタグを消す
tagChips.addEventListener('click', (e) => {
  const button = e.target.closest('.chip-remove');
  if (!button) return;
  tags.splice(Number(button.dataset.index), 1);
  renderTags();
});

// 入力欄に、Enterを押していない文字が残っていたら、保存の直前に、タグとして追加する
tagInput.closest('form').addEventListener('submit', addTagsFromInput);

renderTags();


// ==========================
// サムネイル選択
// ==========================
const thumbList = document.getElementById('thumb-list');
let thumbCard = null;   // 選ばれているカード（画面上の要素）

function renderThumbs() {
  const cards = [...document.querySelectorAll('#card-list > .card-form')];
  thumbList.innerHTML = '';
  let firstRadio = null;
  let firstCard = null;
  let hasSelected = false;

  cards.forEach((card, i) => {
    const preview = card.querySelector('.preview');
    if (!preview) return;                       // 写真の無いカードは、並べない

    const label = document.createElement('label');
    label.className = 'thumb';

    const radio = document.createElement('input');
    radio.type = 'radio';
    radio.name = 'thumbnail';
    radio.value = i;                            // 何枚目のカードか
    if (card === thumbCard) {
      radio.checked = true;
      hasSelected = true;
    }
    radio.addEventListener('change', () => { thumbCard = card; });

    const img = document.createElement('img');
    img.src = preview.src;
    img.alt = '';

    const check = document.createElement('span');
    check.className = 'thumb-check';
    check.textContent = '✓';

    label.append(radio, img, check);
    thumbList.append(label);

    if (!firstRadio) {
      firstRadio = radio;
      firstCard = card;
    }
  });

  // 何も選ばれていなければ、最初の写真を選んだ状態にする
  if (!hasSelected && firstRadio) {
    firstRadio.checked = true;
    thumbCard = firstCard;
  } else if (!hasSelected) {
    thumbCard = null;
  }
}

renderThumbs();


// ==========================
// 画面の切り替え
// ==========================
const steps = document.querySelectorAll('.step');
const step2 = document.getElementById('step-2');
const step2Error = document.getElementById('step2-error');

function showStep(n) {
  steps.forEach((s) => s.classList.toggle('is-active', s.id === `step-${n}`));
  window.scrollTo(0, 0);
}

// 画面2で、必須の項目
const REQUIRED = [
  '[name="title"]',
  '[name="trip_start_date"]',
  '[name="trip_end_date"]',
  '[name="start_spot"]',
  '[name$="-transport"]',
  '[name$="-spot"]',
  '[name$="-comment"]',
].join(',');

function showStep2Error(message) {
  /*
  画面2のエラーメッセージを表示
  */
  step2Error.textContent = message;
  step2Error.hidden = false;
}

// 画面2 → 画面3
document.getElementById('to-step-3').addEventListener('click', () => {
  step2.querySelectorAll('.invalid').forEach((el) => el.classList.remove('invalid'));

  // 未入力の確認
  const empty = [...step2.querySelectorAll(REQUIRED)]
    .filter((el) => el.value.trim() === '');
  if (empty.length > 0) {
    empty.forEach((el) => el.classList.add('invalid'));
    showStep2Error('未入力があります。');
    empty[0].scrollIntoView({ block: 'center' });
    return;
  }

  // 終了日が、開始日より前でないかの確認
  const start = step2.querySelector('[name="trip_start_date"]');
  const end = step2.querySelector('[name="trip_end_date"]');
  if (end.value < start.value) {            // 「2026-09-20」の形は、文字のまま比べられる
    end.classList.add('invalid');
    showStep2Error('終了日は開始日以降にしてください');
    end.scrollIntoView({ block: 'center' });
    return;
  }

  step2Error.hidden = true;
  showStep(3);
});

// 開始日を決めたら、終了日のカレンダーで、それより前を選べなくする
const startDate = step2.querySelector('[name="trip_start_date"]');
const endDate = step2.querySelector('[name="trip_end_date"]');
startDate.addEventListener('change', () => { endDate.min = startDate.value; });
endDate.min = startDate.value;

// 入力し直したら、赤枠を消す
step2.addEventListener('input', (e) => e.target.classList.remove('invalid'));
step2.addEventListener('change', (e) => e.target.classList.remove('invalid'));

// 画面3 → 画面2
document.getElementById('back-to-2').addEventListener('click', () => showStep(2));

// 入力欄でEnterを押しても、フォームを送信させない
document.getElementById('log-form').addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && e.target.tagName === 'INPUT') {
    e.preventDefault();
  }
});


// ==========================
// 画面1：画像選択
// ==========================
const picker = document.getElementById('image-picker');
const pickedList = document.getElementById('picked-list');
let pickedFiles = [];
// 画面2から始まったとき（エラーで戻ってきたとき）は、カードを作り直さない
let appliedKey = step2.classList.contains('is-active') ? '' : null;

// 選ばれた写真が、前と同じかを見分けるための文字列
function fileKey(files) {
  return files.map((f) => `${f.name}:${f.size}:${f.lastModified}`).join('|');
}

const ALLOWED_IMAGE = /\.(jpe?g|png|gif|webp)$/i;
const pickerError = document.getElementById('picker-error');

// 選んだ写真のファイル名を、一覧に出す
picker.addEventListener('change', () => {
  const all = [...picker.files];
  pickedFiles = all.filter((f) => ALLOWED_IMAGE.test(f.name));
  const rejected = all.filter((f) => !ALLOWED_IMAGE.test(f.name));

  if (rejected.length > 0) {
    pickerError.textContent =
      `対応していない形式のファイルを除きました（${rejected.map((f) => f.name).join('、')}）。` +
      'JPEG・PNG・GIF・WebPが使えます。';
    pickerError.hidden = false;
  } else {
    pickerError.hidden = true;
  }

  pickedList.innerHTML = '';
  pickedFiles.forEach((f) => {
    const li = document.createElement('li');
    li.textContent = f.name;
    pickedList.append(li);
  });
});

// カード1枚分の入力を、空に戻す
function resetCard(card) {
  card.querySelectorAll('input[type="file"], textarea, select').forEach((el) => {
    el.value = '';
  });
  const preview = card.querySelector('.preview');
  if (preview) {
    URL.revokeObjectURL(preview.src);
    preview.remove();
  }
}

// カードの写真の欄に、1枚の写真を入れる
function setFile(card, file) {
  const input = card.querySelector('input[type="file"]');
  const dt = new DataTransfer();
  dt.items.add(file);
  input.files = dt.files;
  input.dispatchEvent(new Event('change', { bubbles: true }));   // プレビューを出す
}

// 写真の数だけカードを作って、写真を入れる
function buildCards(files) {
  const cardList = document.getElementById('card-list');

  // 1枚目を残して、あとのカードは消す
  [...cardList.querySelectorAll(':scope > .card-form')].slice(1).forEach((card) => {
    const preview = card.querySelector('.preview');
    if (preview) URL.revokeObjectURL(preview.src);
    card.remove();
  });
  renumberCards();
  resetCard(cardList.querySelector(':scope > .card-form'));

  // 足りない分は、「カードを追加」ボタンを押したことにして、増やす
  const need = Math.max(files.length, 1);
  for (let i = 1; i < need; i++) {
    document.getElementById('add-card').click();
  }

  const cards = cardList.querySelectorAll(':scope > .card-form');
  files.forEach((file, i) => setFile(cards[i], file));
  renderThumbs();
}

// 画面1 → 画面2
document.getElementById('to-step-2').addEventListener('click', () => {
  const key = fileKey(pickedFiles);
  if (key !== appliedKey) {          // 選び方が変わったときだけ、カードを作り直す
    buildCards(pickedFiles);
    appliedKey = key;
  }
  showStep(2);
});

// 画面2 → 画面1
document.getElementById('back-to-1').addEventListener('click', () => showStep(1));