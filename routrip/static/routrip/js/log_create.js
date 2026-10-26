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
  const newCard = document.getElementById('card-list').lastElementChild;     // ← 足す
  initSpotArea(newCard.querySelector('.spot-area')); 
});


// 写真を選んだら、四角の中にプレビューを表示する
document.getElementById('card-list').addEventListener('change', (e) => {
  const input = e.target;
  if (!input.matches('input[type="file"]')) return;

  const card = input.closest('.card-form');
  const box = input.closest('.card-image');
  let img = box.querySelector('.preview');

  if (img) {
    URL.revokeObjectURL(img.src); // 前のプレビュー用の領域を解放する
  }

  const file = input.files[0];
  if (!file) {  // 選択を取り消したとき
    if (img) img.remove();
    renderThumbs();
    applyPhotoLocation(card, null);
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
  applyPhotoLocation(card, file);
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

// 今表示している画面の番号
let currentStep = Number(document.querySelector('.step.is-active').id.replace('step-', ''));

function showStep(n, push = true) {
  steps.forEach((s) => s.classList.toggle('is-active', s.id === `step-${n}`));
  window.scrollTo(0, 0);
  if (push && n !== currentStep) {
    history.pushState({ step: n }, '');      // 履歴に、画面の移動を1つ積む
  }
  currentStep = n;
}

// 画面2で、必須の項目
const REQUIRED = [
  '[name="title"]',
  '[name="trip_start_date"]',
  '[name="trip_end_date"]',
  '[name$="-transport"]',
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
  const incompleteAreas = [...step2.querySelectorAll('.spot-area')]
    .filter((area) => !spotIsComplete(area));

  if (empty.length > 0 || incompleteAreas.length > 0) {
    empty.forEach((el) => el.classList.add('invalid'));
    incompleteAreas.forEach((area) => area.classList.add('invalid'));
    showStep2Error('未入力があります。');
    (empty[0] || incompleteAreas[0]).scrollIntoView({ block: 'center' });
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

const photoInfo = new Map();      // 写真ファイル → {lat, lng, takenAt}
let pickPromise = Promise.resolve();
let pickToken = 0;

// 1枚の写真から、位置情報と撮影日時を読む（読めなくてもエラーにしない）
async function readPhotoInfo(file) {
  let lat = null;
  let lng = null;
  let takenAt = null;

  //位置情報
  try {
    const gps = await exifr.gps(file);  // 位置情報が無いと undefined
    if (gps) {
      lat = gps.latitude;
      lng = gps.longitude;
    }
  } catch (err) {
    console.error('位置情報の読み取りに失敗しました:', file.name, err);
  }
  // 撮影日時
  try{
    const meta = await exifr.parse(file, { pick: ['DateTimeOriginal'] });
    if (meta && meta.DateTimeOriginal) {
      takenAt = meta.DateTimeOriginal;
    }
  } catch (err) {
    console.error('撮影日時の読み取りに失敗しました:', file.name, err);
  }

  return { lat, lng, takenAt };
}

// 撮影日時の順に並べる。日時の無いものは、最後（選んだ順のまま）
function compareByTakenAt(photoA, photoB) {
  const takenAtA = photoInfo.get(photoA).takenAt;   // 撮影日時（無ければ null）
  const takenAtB = photoInfo.get(photoB).takenAt;

  // 両方に撮影日時がある：古いほうを先にする
  if (takenAtA && takenAtB) {
    return takenAtA - takenAtB;
  }
  // 片方にしか無い：撮影日時のあるほうを先にする（無いほうは最後に回す）
  if (takenAtA) return -1;
  if (takenAtB) return 1;
  // 両方とも無い：選んだ順のまま
  return 0;
}

// 選んだ写真のファイル名を、一覧に出す
picker.addEventListener('change', () => {
  const token = ++pickToken;
  const all = [...picker.files];
  const files = all.filter((f) => ALLOWED_IMAGE.test(f.name));
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
  pickPromise = (async () => {
    await Promise.all(files.map(async (f) => {
      photoInfo.set(f, await readPhotoInfo(f));
    }));
    if (token !== pickToken) return;  // 読んでいる間に、選び直されたら、捨てる


    files.sort(compareByTakenAt);
    pickedFiles = files;

    pickedList.innerHTML = '';
    files.forEach((f) => {
      const info = photoInfo.get(f);
      const li = document.createElement('li');
      li.textContent = `${f.name} ${info.lat !== null ? '📍位置情報あり' : '位置情報なし'}`;
      pickedList.append(li);
    });
  })();
});

// カード1枚分の入力を、空に戻す
function resetCard(card) {
  delete card.dataset.lat;
  delete card.dataset.lng;
  delete card.dataset.locSource;
  delete card.dataset.placeName;
  card.querySelector('.spot-candidates').innerHTML = '';
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
document.getElementById('to-step-2').addEventListener('click', async () => {
  await pickPromise;
  const key = fileKey(pickedFiles);
  if (key !== appliedKey) {          // 選び方が変わったときだけ、カードを作り直す
    buildCards(pickedFiles);
    appliedKey = key;
  }
  showStep(2);
});

// 画面2 → 画面1
document.getElementById('back-to-1').addEventListener('click', () => showStep(1));


// ==========================
// 二重投稿の防止
// ==========================
const logForm = document.getElementById('log-form');
const submitButton = logForm.querySelector('.submit-button');
const submitStatus = document.getElementById('submit-status');
let isSubmitting = false;

logForm.addEventListener('submit', (e) => {
  if (isSubmitting) {
    e.preventDefault();               // 2回目以降の送信は、止める
    return;
  }
  isSubmitting = true;
  submitButton.disabled = true;
  submitButton.textContent = '投稿中…';
  submitStatus.hidden = false;
});

// ブラウザの「戻る」で、このページに戻ってきたとき、ボタンを元の状態に戻す
window.addEventListener('pageshow', (e) => {
  if (e.persisted) {
    isSubmitting = false;
    submitButton.disabled = false;
    submitButton.textContent = '投稿する';
    submitStatus.hidden = true;
    skipLeaveWarning = false;
  }
});


// ==========================
// 戻る操作と、入力が消える前の確認
// ==========================
let skipLeaveWarning = false;

// 何か入力されているか
function hasInput() {
  if (pickedFiles.length > 0 || tags.length > 0) return true;
  return [...logForm.querySelectorAll(
    'input[type="text"], input[type="date"], textarea, input[type="file"]'
  )].some((el) => (el.type === 'file' ? el.files.length > 0 : el.value.trim() !== ''));
}

// 履歴の準備：「入口」と「今の画面」の2つを積んでおく
history.replaceState({ guard: true }, '');
history.pushState({ step: currentStep }, '');

window.addEventListener('popstate', (e) => {
  if (e.state && e.state.step) {
    showStep(e.state.step, false);           // 画面を切り替えるだけ
    return;
  }
  // 最初の画面より前に、戻ろうとしたとき
  if (hasInput() && !confirm('入力した内容が消えてしまいます。このページを離れますか？')) {
    history.pushState({ step: currentStep }, '');   // 留まる
    return;
  }
  skipLeaveWarning = true;
  history.back();                                    // ページを離れる
});

// 更新・タブを閉じるときの警告（投稿中は出さない）
window.addEventListener('beforeunload', (e) => {
  if (skipLeaveWarning || isSubmitting || !hasInput()) return;
  e.preventDefault();
  e.returnValue = '';
});

// 画面1の「← 戻る」リンク
document.querySelector('#step-1 a.back-button').addEventListener('click', (e) => {
  if (hasInput() && !confirm('入力した内容が消えてしまいます。ホームに戻りますか？')) {
    e.preventDefault();
    return;
  }
  skipLeaveWarning = true;
});


// ==========================
// スポット（自動で判定／地名で検索）
// ==========================
const resolveUrl = logForm.dataset.resolveUrl;
const nearbyUrl = logForm.dataset.nearbyUrl;
const searchUrl = logForm.dataset.searchUrl;

const NOTE_NO_PHOTO = '写真が無いので、地名で検索してください';
const NOTE_NO_GPS = '写真に位置情報が無いので、地名で検索してください';
const NOTE_CHANGE = '地名で検索して、場所を選んでください';
const NOTE_HINT = '（同じ名前が多いときは、「福岡県 福岡市」のように、県名や市名を足すと絞れます）';

let locationSeq = 0;

// 実行中の処理に番号をつける（あとから来た古い結果を、捨てるため）
function beginTask(area) {
  const seq = ++locationSeq;
  area.dataset.seq = String(seq);
  return seq;
}

function isCurrent(area, seq) {
  return area.isConnected && area.dataset.seq === String(seq);
}

function makeNote(text) {
  const note = document.createElement('p');
  note.className = 'spot-candidates-note';
  note.textContent = text;
  return note;
}

// スポット欄の中の部品を、まとめて取り出す
function spotParts(area) {
  const root = area.closest('.card-form, .start-box');
  return {
    id: root.querySelector('[name$="-spot"]'),
    label: root.querySelector('[name$="-spot_label"]'),
    newName: root.querySelector('[name$="-new_spot_name"]'),
    newLat: root.querySelector('[name$="-new_spot_lat"]'),
    newLng: root.querySelector('[name$="-new_spot_lng"]'),
    status: area.querySelector('.spot-status'),
    resolved: area.querySelector('.spot-resolved'),
    nameLabel: area.querySelector('.spot-name'),
    search: area.querySelector('.place-search'),
    searchNote: area.querySelector('.place-search-note'),
    query: area.querySelector('.place-query'),
    results: area.querySelector('.place-results'),
  };
}

// スポットが決まっているか（「次へ」の確認で使う）
function spotIsComplete(area) {
  const p = spotParts(area);
  if (p.id.value !== '') return true;
  return p.newName.value.trim() !== '' && p.newLat.value !== '' && p.newLng.value !== '';
}

// 「決まった」状態の表示にする（editable: 新しい場所なので、名前を直せる）
function showResolved(area, text, editable) {
  const p = spotParts(area);
  p.status.textContent = '';
  p.search.hidden = true;
  p.resolved.hidden = false;
  p.nameLabel.hidden = editable;
  p.nameLabel.textContent = text;
  p.newName.hidden = !editable;
  area.classList.remove('invalid');
}

// 地名検索の欄を出す
function showSearch(area, note) {
  const p = spotParts(area);
  p.resolved.hidden = true;
  p.status.textContent = '';
  p.search.hidden = false;
  p.searchNote.textContent = note + NOTE_HINT;
}

// 選んだものを、全部消す
function clearSpot(area) {
  const p = spotParts(area);
  p.id.value = '';
  p.label.value = '';
  p.newName.value = '';
  p.newLat.value = '';
  p.newLng.value = '';
  p.resolved.hidden = true;
  p.results.innerHTML = '';
  p.query.value = '';
  p.status.textContent = '';
}

// 登録済みのスポットに決める
function setDbSpot(area, spot) {
  const p = spotParts(area);
  p.id.value = spot.id;
  p.label.value = spot.name;
  p.newName.value = '';
  p.newLat.value = '';
  p.newLng.value = '';
  showResolved(area, spot.name, false);
}

// 新しい場所に決める（名前は、あとから直せる）
function setNewSpot(area, name, lat, lng) {
  const p = spotParts(area);
  p.id.value = '';
  p.label.value = name;
  p.newName.value = name;
  p.newLat.value = lat;
  p.newLng.value = lng;
  showResolved(area, '', true);
}

// 最初の状態にする（サーバーのエラーで戻ってきたときは、入っていた内容を表示する）
function initSpotArea(area) {
  const p = spotParts(area);
  if (p.id.value !== '') {
    showResolved(area, p.label.value || '選択済みのスポット', false);
  } else if (p.newName.value.trim() !== '' && p.newLat.value !== '' && p.newLng.value !== '') {
    showResolved(area, '', true);
  } else {
    showSearch(area, NOTE_NO_PHOTO);
  }
}

// 写真の座標から、場所を自動で決める
async function resolveFromPhoto(area, lat, lng, seq) {
  const p = spotParts(area);
  p.status.textContent = '📍 場所を調べています…';

  let data = null;
  try {
    const res = await fetch(`${resolveUrl}?lat=${lat}&lng=${lng}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    data = await res.json();
  } catch (err) {
    console.error('場所の判定に失敗しました:', err);
  }
  if (!isCurrent(area, seq)) return;

  if (data && data.source === 'db') {
    setDbSpot(area, data.spot);
  } else if (data && data.source === 'reverse') {
    setNewSpot(area, data.name, lat, lng);       // 座標は、写真のものを使う
  } else {
    showSearch(area, '場所の名前を取得できませんでした。地名で検索してください');
  }
}

// カードの写真が変わったときに、そのカードのスポットを、作り直す
async function applyPhotoLocation(card, file) {
  const area = card.querySelector('.spot-area');
  const seq = beginTask(area);
  delete card.dataset.lat;
  delete card.dataset.lng;
  clearSpot(area);

  if (!file) {
    showSearch(area, NOTE_NO_PHOTO);
    return;
  }

  spotParts(area).status.textContent = '📍 写真の位置情報を読んでいます…';
  const info = photoInfo.get(file) || await readPhotoInfo(file);
  if (!isCurrent(area, seq)) return;

  if (info.lat === null) {
    showSearch(area, NOTE_NO_GPS);
    return;
  }
  card.dataset.lat = info.lat;
  card.dataset.lng = info.lng;
  await resolveFromPhoto(area, info.lat, info.lng, seq);
}

// カード1枚の入力を、空に戻す
function resetCard(card) {
  delete card.dataset.lat;
  delete card.dataset.lng;
  const area = card.querySelector('.spot-area');
  beginTask(area);
  clearSpot(area);
  card.querySelectorAll('input[type="file"], textarea, select').forEach((el) => {
    el.value = '';
  });
  const preview = card.querySelector('.preview');
  if (preview) {
    URL.revokeObjectURL(preview.src);
    preview.remove();
  }
  initSpotArea(area);
}

// 地名を検索する
async function searchPlaces(area) {
  const p = spotParts(area);
  const button = area.querySelector('.place-search-button');
  const query = p.query.value.trim();
  if (!query || button.disabled) return;

  // 公開サーバーの利用ルール（1秒に1回まで）のため、押したあと1秒は、押せなくする
  button.disabled = true;
  setTimeout(() => { button.disabled = false; }, 1000);

  const seq = beginTask(area);
  p.results.innerHTML = '';
  p.results.append(makeNote('検索中…'));

  let data = { results: [], error: '検索できませんでした' };
  try {
    const res = await fetch(`${searchUrl}?q=${encodeURIComponent(query)}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    data = await res.json();
  } catch (err) {
    console.error('地名検索に失敗しました:', err);
  }
  if (!isCurrent(area, seq)) return;

  p.results.innerHTML = '';
  if (data.error) {
    p.results.append(makeNote(data.error));
  } else if (data.results.length === 0) {
    p.results.append(makeNote('見つかりませんでした。住所や市区町村名など、別の言葉で検索してみてください'));
  } else {
    p.results.append(makeNote('地点を選んでください'));
  }

  data.results.forEach((place) => {
    const item = document.createElement('button');
    item.type = 'button';
    item.className = 'place-result';
    item.dataset.name = place.name;
    item.dataset.lat = place.lat;
    item.dataset.lng = place.lng;

    const nameLine = document.createElement('span');
    nameLine.className = 'place-result-name';
    nameLine.textContent = `🔎 ${place.name}`;
    item.append(nameLine);

    const detail = shortAddress(place);
    if (detail) {
      const detailLine = document.createElement('span');
      detailLine.className = 'place-result-detail';
      detailLine.textContent = detail;
      item.append(detailLine);
    }
    p.results.append(item);
  });
}

// 住所から、見分けに使う部分だけを取り出す（先頭の名前と、末尾の「日本」は、除く）
function shortAddress(place) {
  const parts = (place.address || '').split(',').map((s) => s.trim()).filter(Boolean);
  if (parts[0] === place.name) parts.shift();
  if (parts[parts.length - 1] === '日本') parts.pop();
  return parts.join('、');
}

// 検索結果を選んだとき：近くに登録済みのスポットがあれば、それを使う。無ければ、新しい場所にする
async function adoptSearchResult(area, place) {
  const p = spotParts(area);
  const seq = beginTask(area);
  p.results.innerHTML = '';
  p.status.textContent = '📍 場所を確認しています…';

  let nearest = null;
  try {
    const res = await fetch(`${nearbyUrl}?lat=${place.lat}&lng=${place.lng}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    nearest = (await res.json()).results[0] || null;
  } catch (err) {
    console.error('近くのスポットの確認に失敗しました:', err);
  }
  if (!isCurrent(area, seq)) return;

  if (nearest) {
    setDbSpot(area, nearest);
  } else {
    setNewSpot(area, place.name, place.lat, place.lng);
  }
}

// ボタンを押したとき
step2.addEventListener('click', (e) => {
  const area = e.target.closest('.spot-area');
  if (!area) return;

  if (e.target.closest('.spot-change')) {          // 変更：地名で検索し直す
    beginTask(area);
    clearSpot(area);
    showSearch(area, NOTE_CHANGE);
    return;
  }
  if (e.target.closest('.place-search-button')) {
    searchPlaces(area);
    return;
  }
  const result = e.target.closest('.place-result');
  if (result) {
    adoptSearchResult(area, {
      name: result.dataset.name,
      lat: result.dataset.lat,
      lng: result.dataset.lng,
    });
  }
});

// 検索欄で Enter を押したときも、検索する（日本語の変換の確定は、除く）
step2.addEventListener('keydown', (e) => {
  if (e.key !== 'Enter' || e.isComposing) return;
  if (!e.target.matches('.place-query')) return;
  e.preventDefault();
  searchPlaces(e.target.closest('.spot-area'));
});

// 新しい場所の名前を直したら、赤枠を消す
step2.addEventListener('input', (e) => {
  if (e.target.matches('[name$="-new_spot_name"]')) {
    e.target.closest('.spot-area').classList.remove('invalid');
  }
});

// 最初から表示されているカードを、準備する
document.querySelectorAll('#card-list .spot-area').forEach(initSpotArea);
