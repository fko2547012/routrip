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
    return;
  }

  if (!img) {
    img = document.createElement('img');
    img.className = 'preview';
    img.alt = '';
    box.prepend(img); // 画像を、四角の一番上に入れる
  }
  img.src = URL.createObjectURL(file);
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