// Front end: talks to the Flask REST API with fetch().

const API = "/api";
const $ = (id) => document.getElementById(id);

// ---------- helpers ----------
async function request(url, options = {}) {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Something went wrong");
  return data;
}

function today() {
  return new Date().toISOString().slice(0, 10); // YYYY-MM-DD
}

// Build table cells with textContent (not innerHTML) so user notes can't inject HTML.
function cell(text, className) {
  const td = document.createElement("td");
  td.textContent = text;
  if (className) td.className = className;
  return td;
}

// ---------- load data ----------
async function loadCategories() {
  const categories = await request(`${API}/categories`);
  for (const c of categories) {
    $("category").add(new Option(c, c));
    $("filter-category").add(new Option(c, c));
  }
}

async function loadSummary() {
  const s = await request(`${API}/summary?month=${$("month").value}`);
  $("total").textContent = s.total.toFixed(2);
  const list = $("by-category");
  list.innerHTML = "";
  for (const [category, total] of Object.entries(s.by_category)) {
    const li = document.createElement("li");
    li.textContent = `${category}: ₹${total.toFixed(2)}`;
    list.appendChild(li);
  }
}

async function loadExpenses() {
  const params = new URLSearchParams({ month: $("month").value });
  if ($("filter-category").value) params.set("category", $("filter-category").value);
  const expenses = await request(`${API}/expenses?${params}`);

  const tbody = $("expense-list");
  tbody.innerHTML = "";
  for (const e of expenses) {
    const tr = document.createElement("tr");
    tr.append(cell(e.date), cell(e.category), cell(e.note), cell(`₹${e.amount.toFixed(2)}`, "num"));

    const actions = document.createElement("td");
    const edit = document.createElement("button");
    edit.textContent = "Edit";
    edit.className = "link";
    edit.onclick = () => startEdit(e);
    const del = document.createElement("button");
    del.textContent = "Delete";
    del.className = "link danger";
    del.onclick = () => deleteExpense(e.id);
    actions.append(edit, del);
    tr.appendChild(actions);

    tbody.appendChild(tr);
  }
  $("empty").classList.toggle("hidden", expenses.length > 0);
}

function refresh() {
  return Promise.all([loadSummary(), loadExpenses()]);
}

// ---------- add / edit / delete ----------
function resetForm() {
  $("expense-form").reset();
  $("expense-id").value = "";
  $("date").value = today();
  $("form-title").textContent = "Add expense";
  $("submit-btn").textContent = "Add";
  $("cancel-btn").classList.add("hidden");
  $("error").textContent = "";
}

function startEdit(e) {
  $("expense-id").value = e.id;
  $("amount").value = e.amount;
  $("category").value = e.category;
  $("date").value = e.date;
  $("note").value = e.note;
  $("form-title").textContent = "Edit expense";
  $("submit-btn").textContent = "Save";
  $("cancel-btn").classList.remove("hidden");
  $("amount").focus();
}

async function deleteExpense(id) {
  if (!confirm("Delete this expense?")) return;
  await request(`${API}/expenses/${id}`, { method: "DELETE" });
  refresh();
}

$("expense-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const id = $("expense-id").value;
  const body = JSON.stringify({
    amount: $("amount").value,
    category: $("category").value,
    date: $("date").value,
    note: $("note").value,
  });
  try {
    if (id) {
      await request(`${API}/expenses/${id}`, { method: "PUT", body });
    } else {
      await request(`${API}/expenses`, { method: "POST", body });
    }
    resetForm();
    refresh();
  } catch (err) {
    $("error").textContent = err.message;
  }
});

$("cancel-btn").addEventListener("click", resetForm);
$("month").addEventListener("change", refresh);
$("filter-category").addEventListener("change", loadExpenses);

// ---------- start ----------
$("month").value = today().slice(0, 7); // current month, YYYY-MM
resetForm();
loadCategories().then(refresh);
