import { useEffect, useState } from "react";
import { api } from "../api";
import { ErrorBox, Section } from "../components/ui";
import { CATEGORY_LABEL } from "../format";
import type { Entity } from "../types";

const split = (s: string) => s.split(",").map((x) => x.trim()).filter(Boolean);

export default function EntitiesPage() {
  const [items, setItems] = useState<Entity[]>([]);
  const [form, setForm] = useState({ name: "", category: "government", handles: "", domains: "", keywords: "" });
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("");

  const load = () => api.entities().then(setItems).catch((e) => setError(e.message));
  useEffect(() => {
    load();
  }, []);

  async function add(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await api.createEntity({
        name: form.name,
        category: form.category,
        handles: split(form.handles),
        domains: split(form.domains),
        keywords: split(form.keywords),
      });
      setForm({ ...form, name: "", handles: "", domains: "", keywords: "" });
      load();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  const shown = items.filter((i) => !filter || i.name.toLowerCase().includes(filter.toLowerCase()));
  return (
    <div className="space-y-6">
      <Section title="Tambah entitas">
        <form onSubmit={add} className="card grid gap-3 md:grid-cols-2">
          {error && <div className="md:col-span-2"><ErrorBox error={error} /></div>}
          <input className="input" placeholder="Nama organisasi" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <select className="input" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
            {Object.entries(CATEGORY_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
          <input className="input" placeholder="Handle (pisah koma), mis. kemkomdigi, bssn_ri" value={form.handles} onChange={(e) => setForm({ ...form, handles: e.target.value })} />
          <input className="input" placeholder="Domain resmi (pisah koma), mis. komdigi.go.id" value={form.domains} onChange={(e) => setForm({ ...form, domains: e.target.value })} />
          <input className="input md:col-span-2" placeholder="Kata kunci spesifik (pisah koma)" value={form.keywords} onChange={(e) => setForm({ ...form, keywords: e.target.value })} />
          <div><button className="btn-primary">Simpan</button></div>
        </form>
      </Section>
      <Section title={`Daftar entitas (${items.length})`} action={<input className="input max-w-xs" placeholder="Cari…" value={filter} onChange={(e) => setFilter(e.target.value)} />}>
        <div className="card overflow-x-auto p-0">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs text-slate-500">
              <tr><th className="p-2">Nama</th><th>Kategori</th><th>Handle</th><th>Domain</th><th>Kata kunci</th><th /></tr>
            </thead>
            <tbody>
              {shown.map((e) => (
                <tr key={e.id} className="border-t border-slate-100 align-top">
                  <td className="p-2 font-medium">{e.name}</td>
                  <td>{CATEGORY_LABEL[e.category] ?? e.category}</td>
                  <td className="text-xs">{e.handles.join(", ")}</td>
                  <td className="text-xs">{e.domains.join(", ")}</td>
                  <td className="text-xs">{e.keywords.join(", ")}</td>
                  <td className="p-2">
                    <button className="text-xs text-red-600 hover:underline" onClick={() => confirm(`Hapus ${e.name}?`) && api.deleteEntity(e.id).then(load)}>
                      Hapus
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>
    </div>
  );
}
