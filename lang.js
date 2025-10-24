Skip to content
Navigation Menu
Ibrohim0200
Astech

Type / to search
Code
Issues
Pull requests
Actions
Projects
Wiki
Security
1
Insights
Settings
Files
Go to file
t
image
locales
index.html
lang.js
Astech
/lang.js
Ibrohim0200
Ibrohim0200
Update lang.js
0beaacb
 · 
19 hours ago

Code

Blame
79 lines (62 loc) · 2.54 KB
function getLangFromUrl() {
  const params = new URLSearchParams(window.location.search);
  return params.get("lang") || localStorage.getItem("lang") || "uz";
}

async function loadLanguage(lang) {
  try {
    const response = await fetch(`locales/${lang}.json`);
    if (!response.ok) throw new Error("Language file not found");
    const data = await response.json();
    applyTranslations(data);
    localStorage.setItem("lang", lang);
  } catch (err) {
    console.error("❌ Tilni yuklashda xatolik:", err);
  }
}

function applyTranslations(texts) {
  document.querySelector("nav a.active").textContent = texts.navbar.autopark;

  document.querySelectorAll(".car-card").forEach(card => {
    const priceElement = card.querySelector(".price");
    if (priceElement) {
      // 1️⃣ data-price dan sonni olamiz
      const priceValue = priceElement.getAttribute("data-price");
      if (priceValue) {
        // 2️⃣ Raqamni 3 lik formatda yozamiz (masalan: 1 200 000)
        const formatted = Number(priceValue).toLocaleString('uz-UZ');

        // 3️⃣ Eski matnning oxiridagi so‘zlarni (so'm/kun) olib tashlab, yangi suffix qo‘shamiz
        priceElement.innerText = `${formatted} ${texts.cars.price_suffix}`;
      } else {
        // Agar data-price bo‘lmasa, eski matndan foydalanamiz
        const parts = priceElement.innerText.split(' ');
        parts.pop(); // oxirgi elementni (so'm/kun) olib tashlaydi
        const numberPart = parts.join(' ');
        priceElement.innerText = `${numberPart} ${texts.cars.price_suffix}`;
      }
    }

    const btn = card.querySelector(".btn");
    if (btn) btn.innerText = texts.cars.order_button;
  });

  // Modal tarjimalari
  const labels = document.querySelectorAll(".form-group label");
  if (labels.length >= 4) {
    labels[0].innerText = texts.modal.name_label;
    labels[1].innerText = texts.modal.phone_label;
    labels[2].innerText = texts.modal.start_date_label;
    labels[3].innerText = texts.modal.end_date_label;
  }

  document.querySelector("#orderModal h2").innerText = texts.modal.title;
  document.querySelector("#orderModal button").innerText = texts.modal.confirm_button;

  window.ALERTS = texts.alerts;
  console.log(texts.console.ready);
}

function showAlert(type) {
  if (window.ALERTS && window.ALERTS[type]) {
    alert(window.ALERTS[type]);
  } else {
    alert("⚠️ Xatolik yuz berdi!");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const lang = getLangFromUrl();
  loadLanguage(lang);
});


